import tempfile
from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import Arch, LinuxDistribution
from pyinfra.operations import files, server, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

# https://github.com/k3s-io/k3s/releases
k3s_version = 'v1.23.3+k3s1'

# https://github.com/GoogleContainerTools/skaffold/releases
skaffold_version = 'v1.37.0'

master_ip = "10.5.0.1"
server_node = 'bang'
nodes = ['slash', 'dash', 'frontbed', 'garage']
admin_from = ['bang', 'slash', 'dash']

if host.name in [nodes + [server_node]]:
    server.sysctl(key='net.ipv4.ip_forward', value="1", persist=True)
    server.sysctl(key='net.ipv6.conf.all.forwarding', value="1", persist=True)

    tail = 'k3s' if host.get_fact(Arch) == 'x86_64' else 'k3s-armhf'
    files.download(
        src=f'https://github.com/rancher/k3s/releases/download/{k3s_version}/{tail}',
        dest='/usr/local/bin/k3s',
        user='root',
        group='root',
        mode='755',
        cache_time=43000,
        # force=True,  # to get a new version
    )

    if is_pi:
        old_cmdline = host.get_fact(FindInFile, path='/boot/cmdline.txt', pattern=r'.*')[0]
        print(repr(old_cmdline))
        if 'cgroup' not in old_cmdline:
            cmdline = old_cmdline + ' cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory'
            files.line(path='/boot/cmdline.txt', line='.*', replace=cmdline)
            # pi needs reboot now

        server.shell(commands=[
            'update-alternatives --set iptables /usr/sbin/iptables-nft',
            'update-alternatives --set ip6tables /usr/sbin/ip6tables-nft',
        ])
        # needs reboot if this changed

    # See https://github.com/rancher/k3s/issues/1802 and https://rancher.com/docs/k3s/latest/en/installation/private-registry/
    files.directory(path='/etc/rancher/k3s')
    files.template(src='templates/kube/registries.yaml.j2', dest='/etc/rancher/k3s/registries.yaml')

    service_name = 'k3s.service' if host.name == 'bang' else 'k3s-node.service'
    which_conf = 'config.yaml.j2' if host.name == 'bang' else 'node-config.yaml.j2'

    # /var/lib/rancher/k3s/server/node-token is the source of the string in secrets/k3s_token
    token = open('secrets/k3s_token', 'rt').read().strip()
    files.template(
        src=f'templates/kube/{which_conf}',
        dest='/etc/k3s_config.yaml',
        master_ip=master_ip,
        token=token,
        wg_ip=host.host_data['wireguard_address'],
    )

    files.template(
        src='templates/kube/k3s.service.j2',
        dest=f'/etc/systemd/system/{service_name}',
        role='server' if host.name == 'bang' else 'agent',
    )
    systemd.service(service=service_name, daemon_reload=True, enabled=True, restarted=True)

if host.name == 'bang':
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

    files.chown(target='/etc/rancher/k3s/k3s.yaml', user='root', group='drewp')
    files.chmod(target='/etc/rancher/k3s/k3s.yaml', mode='640')

    # see https://github.com/GoogleContainerTools/skaffold/releases
    files.download(src=f'https://storage.googleapis.com/skaffold/releases/{skaffold_version}/skaffold-linux-amd64',
                   dest='/usr/local/bin/skaffold',
                   user='root',
                   group='root',
                   mode='755',
                   cache_time=1000)
