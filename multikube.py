# leave kube.py running single-host and try again
import os

from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import Arch, LinuxDistribution
from pyinfra.operations import files, server, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

from multikube_config import server_node, master_ip,nodes, admin_from, k3s_version, skaffold_version

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
    server.sysctl(key='net.ipv6.conf.all.disable_ipv6' , value='1',persist=True)
    server.sysctl(key='fs.inotify.max_user_instances', value='8192', persist=True)
    server.sysctl(key='fs.inotify.max_user_watches', value='524288', persist=True)

    # https://sysctl-explorer.net/net/ipv4/rp_filter/
    #none, strict, loose = 0, 1, 2
    #server.sysctl(key='net.ipv4.conf.default.rp_filter', value=loose, persist=True)

    if is_pi:
        pi_cgroup_setup()

def service_name():
    return 'k3s.service' if host.name == server_node else 'k3s-node.service'

def config_and_run_service():
    download_k3s()
    role = 'server' if host.name == server_node else 'agent'
    which_conf = 'config-server.yaml.j2' if host.name == server_node else 'config-agent.yaml.j2'

    if host.name == server_node:
        token = "unused"
    else:
        token = open('/tmp/k3s-token', 'rt').read().strip()
    files.template(
        src=f'templates/kube/{which_conf}',
        dest='/etc/k3s_config.yaml',
        master_ip=master_ip,
        token=token,
        wg_ip=host.host_data['mk_addr'],#wireguard_address'],
    )

    files.template(
        src='templates/kube/k3s.service.j2',
        dest=f'/etc/systemd/system/{service_name()}',
        role=role,
    )
    systemd.service(service=service_name(), daemon_reload=True, enabled=True, restarted=True)

    if host.name == server_node:
       files.get(src='/var/lib/rancher/k3s/server/node-token', dest='/tmp/k3s-token')
       files.get(src='/etc/rancher/k3s/k3s.yaml', dest='/tmp/k3s-yaml')

if host.name in nodes + [server_node]:
    host_prep()
    files.directory(path='/etc/rancher/k3s')

    config_and_run_service()

    # docs: https://rancher.com/docs/k3s/latest/en/installation/private-registry/
    # user confusions: https://github.com/rancher/k3s/issues/1802
    files.template(src='templates/kube/registries.yaml.j2', dest='/etc/rancher/k3s/registries.yaml')
    # for the possible registries update:
    systemd.service(service=service_name(), daemon_reload=True, enabled=True, restarted=True)

if host.name in admin_from:
    files.directory(path='/etc/rancher/k3s')
    install_skaffold()
    files.link(path='/usr/local/bin/kubectl', target='/usr/local/bin/k3s')
    files.directory(path='/home/drewp/.kube', user='drewp', group='drewp')
    # .zshrc has: export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

    # assumes our pyinfra process is running on server_node
    if host.name != server_node:
        files.put(src='/tmp/k3s-yaml', dest='/etc/rancher/k3s/k3s.yaml')

    files.file(path='/etc/rancher/k3s/k3s.yaml', user='root', group='drewp', mode='640')
    server.shell(f"kubectl config set-cluster default --server=https://{master_ip}:6443 --kubeconfig=/etc/rancher/k3s/k3s.yaml")
