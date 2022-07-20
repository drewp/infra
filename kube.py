import os

from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import Arch, LinuxDistribution
from pyinfra.operations import files, server, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

master_ip = "10.5.0.1"
server_node = 'bang'
nodes = ['slash', 'dash']  #, 'dash', 'frontbed', 'garage']
admin_from = ['bang', 'slash', 'dash']
# https://github.com/k3s-io/k3s/releases
# 1.23.6 per https://github.com/cilium/cilium/issues/20331
k3s_version = 'v1.23.6+k3s1'

# https://github.com/GoogleContainerTools/skaffold/releases
skaffold_version = 'v1.39.1'


def download_k3s():
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


def install_skaffold():
    files.download(src=f'https://storage.googleapis.com/skaffold/releases/{skaffold_version}/skaffold-linux-amd64',
                   dest='/usr/local/bin/skaffold',
                   user='root',
                   group='root',
                   mode='755',
                   cache_time=1000)
    # one time; writes to $HOME
    #skaffold config set --global insecure-registries bang5:5000


def pi_cgroup_setup():
    old_cmdline = host.get_fact(FindInFile, path='/boot/cmdline.txt', pattern=r'.*')[0]
    if 'cgroup' not in old_cmdline:
        cmdline = old_cmdline + ' cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory'
        files.line(path='/boot/cmdline.txt', line='.*', replace=cmdline)
        # pi needs reboot now


def host_prep():
    server.sysctl(key='net.ipv4.ip_forward', value="1", persist=True)
    server.sysctl(key='net.ipv6.conf.all.forwarding', value="1", persist=True)
    server.sysctl(key='fs.inotify.max_user_instances', value='8192', persist=True)
    server.sysctl(key='fs.inotify.max_user_watches', value='524288', persist=True)

    # https://sysctl-explorer.net/net/ipv4/rp_filter/
    none, strict, loose = 0, 1, 2
    server.sysctl(key='net.ipv4.conf.default.rp_filter', value=loose, persist=True)

    if is_pi:
        pi_cgroup_setup()


def config_and_run_service():
    download_k3s()
    service_name = 'k3s.service' if host.name == server_node else 'k3s-node.service'
    role = 'server' if host.name == server_node else 'agent'
    which_conf = 'config-server.yaml.j2' if host.name == server_node else 'config-agent.yaml.j2'

    # /var/lib/rancher/k3s/server/node-token is the source of the string in secrets/k3s_token,
    # so this presumes a previous run
    if host.name == server_node:
        token = "ununsed"
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
    files.template(
        src='templates/kube/k3s.service.j2',
        dest=f'/etc/systemd/system/{service_name}',
        role=role,
    )
    systemd.service(service=service_name, daemon_reload=True, enabled=True, restarted=True)


if host.name in nodes + [server_node]:
    host_prep()
    files.directory(path='/etc/rancher/k3s')

    # docs: https://rancher.com/docs/k3s/latest/en/installation/private-registry/
    # user confusions: https://github.com/rancher/k3s/issues/1802
    files.template(src='templates/kube/registries.yaml.j2', dest='/etc/rancher/k3s/registries.yaml')
    # also note that podman dropped the default `docker.io/` prefix on image names (see https://unix.stackexchange.com/a/701785/419418)
    config_and_run_service()

if host.name in admin_from:
    files.directory(path='/etc/rancher/k3s')
    install_skaffold()
    files.link(path='/usr/local/bin/kubectl', target='/usr/local/bin/k3s')
    files.directory(path='/home/drewp/.kube', user='drewp', group='drewp')
    files.line(path="/home/drewp/.zshrc", line="KUBECONFIG", replace='export KUBECONFIG=/etc/rancher/k3s/k3s.yaml')

    # assumes our pyinfra process is running on server_node
    files.put(
        src='/etc/rancher/k3s/k3s.yaml',
        dest='/etc/rancher/k3s/k3s.yaml',  #
        user='root',
        group='drewp',
        mode='640')
    server.shell(f"kubectl config set-cluster default --server=https://{master_ip}:6443 --kubeconfig=/etc/rancher/k3s/k3s.yaml")
