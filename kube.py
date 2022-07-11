import os
import tempfile
from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import Arch, LinuxDistribution
from pyinfra.operations import files, server, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']
raise NotImplementedError("update templates from current config files")
# https://github.com/k3s-io/k3s/releases
# 1.23.6 per https://github.com/cilium/cilium/issues/20331
k3s_version = 'v1.23.6+k3s1'

# https://github.com/GoogleContainerTools/skaffold/releases
skaffold_version = 'v1.39.1'

master_ip = "10.5.0.1"
server_node = 'bang'
nodes = ['slash', 'dash']  #, 'dash', 'frontbed', 'garage']
admin_from = ['bang', 'slash', 'dash']
def host_prep():
    server.sysctl(key='net.ipv4.ip_forward', value="1", persist=True)
    server.sysctl(key='net.ipv6.conf.all.forwarding', value="1", persist=True)
    server.sysctl(key='fs.inotify.max_user_instances', value='8192', persist=True)
    server.sysctl(key='fs.inotify.max_user_watches', value='524288', persist=True)

    tail = 'k3s' if host.get_fact(Arch) == 'x86_64' else 'k3s-armhf'
    files.download(
        src=f'https://github.com/rancher/k3s/releases/download/{k3s_version}/{tail}',
        dest='/usr/local/bin/k3s',
        user='root',
        group='root',
        mode='755',
        cache_time=43000,
        #force=True,  # to get a new version
    )

    if is_pi:
        old_cmdline = host.get_fact(FindInFile, path='/boot/cmdline.txt', pattern=r'.*')[0]
        if 'cgroup' not in old_cmdline:
            cmdline = old_cmdline + ' cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory'
            files.line(path='/boot/cmdline.txt', line='.*', replace=cmdline)
            # pi needs reboot now

    # https://github.com/k3s-io/k3s/issues/1812 unclear
    server.shell(commands=[
        'update-alternatives --set iptables /usr/sbin/iptables-legacy',
        'update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy',
    ])
    # needs reboot if this changed

    # See https://github.com/rancher/k3s/issues/1802 and https://rancher.com/docs/k3s/latest/en/installation/private-registry/
    files.directory(path='/etc/rancher/k3s')

def config_and_run_service():
    service_name = 'k3s.service' if host.name == server_node else 'k3s-node.service'
    which_conf = 'config.yaml.j2' if host.name == server_node else 'node-config.yaml.j2'
    role = 'server' if host.name == server_node else 'agent'

    # /var/lib/rancher/k3s/server/node-token is the source of the string in secrets/k3s_token,
    # so this presumes a previous run
    if host.name == server_node:
        token="ununsed"
    else:
        if not os.path.exists('/var/lib/rancher/k3s/server/node-token'):
            print("first pass is for server only- skipping other nodes")
            return
        token = open('/var/lib/rancher/k3s/server/node-token', 'rt').read().strip()
    files.template(
        src=f'templates/kube/{which_conf}',
        dest='/etc/k3s_config.yaml',
        master_ip=master_ip,
        token=token,
        wg_ip=host.host_data['wireguard_address'],
    )
    # files.put(
    #     src='templates/kube/flannel.link',  #
    #     dest='/etc/systemd/network/10-flannel.link')  # then reboot
    files.template(
        src='templates/kube/k3s.service.j2',
        dest=f'/etc/systemd/system/{service_name}',
        role=role,
    )
    systemd.service(service=service_name, daemon_reload=True, enabled=True, restarted=True)


if host.name in nodes + [server_node]:
    host_prep()

    # not until registry is up, right?
    files.template(src='templates/kube/registries.yaml.j2', dest='/etc/rancher/k3s/registries.yaml')
    config_and_run_service()

if host.name == server_node:
    files.put(
        src="templates/kube/coredns.yaml",
        dest="/var/lib/rancher/k3s/server/manifests/coredns.yaml",
        mode="600",
    )
    # files.put(
    #     src="templates/kube/coredns-map.yaml",
    #     dest="/var/lib/rancher/k3s/server/manifests/coredns-map.yaml",
    #     mode="600",
    # )
    # tmp = tempfile.NamedTemporaryFile(suffix='.yaml')
    # files.template(
    #     src='templates/kube/Corefile.yaml.j2',
    #     dest=tmp.name,
    # )
    # server.shell(commands=[
    #     'kubectl replace configmap '
    #     # '-n kube-system '
    #     # 'coredns '
    #     f'--filename={tmp.name} '
    #     '-o yaml '
    #     # '--dry-run=client | kubectl apply -',
    # ])
# one-time thing at cluster create time? not sure
# - name: Replace https://localhost:6443 by https://master-ip:6443
#   command: >-
#     k3s kubectl config set-cluster default
#       --server=https://{{ master_ip }}:6443
#       --kubeconfig ~{{ ansible_user }}/.kube/config

if host.name in admin_from:
    files.link(path='/usr/local/bin/kubectl', target='/usr/local/bin/k3s')
    files.directory(path='/home/drewp/.kube', user='drewp', group='drewp')
    files.line(path="/home/drewp/.zshrc", line="KUBECONFIG", replace='export KUBECONFIG=/etc/rancher/k3s/k3s.yaml')

    # assumes pyinfra is running on server_node
    files.put(src='/etc/rancher/k3s/k3s.yaml', dest='/etc/rancher/k3s/k3s.yaml', user='root', group='drewp', mode='640')

    # see https://github.com/GoogleContainerTools/skaffold/releases
    files.download(src=f'https://storage.googleapis.com/skaffold/releases/{skaffold_version}/skaffold-linux-amd64',
                   dest='/usr/local/bin/skaffold',
                   user='root',
                   group='root',
                   mode='755',
                   cache_time=1000)
    # one time; writes to $HOME
    #skaffold config set --global insecure-registries bang5:5000