from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.facts.server import Arch, LinuxDistribution
from pyinfra.operations import files, server, systemd

bang_is_old = True  # remove after upgrade
is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']
is_wifi_pi = host.name in ['frontdoor', 'living']

k3s_version = 'v1.21.2+k3s1'
master_ip = "10.5.0.1"

server.sysctl(key='net.ipv4.ip_forward', value="1", persist=True)
server.sysctl(key='net.ipv6.conf.all.forwarding', value="1", persist=True)

tail = 'k3s' if host.get_fact(Arch) == 'x86_64' else 'k3s-armhf'
files.download(src=f'https://github.com/rancher/k3s/releases/download/{k3s_version}/{tail}',
               dest='/usr/local/bin/k3s',
               user='root',
               group='root',
               mode='755')

if is_pi:
    old_cmdline = host.get_fact(FindInFile, path='/boot/cmdline.txt', pattern=r'.*')[0]
    print(repr(old_cmdline))
    if 'cgroup' not in old_cmdline:
        cmdline = old_cmdline + ' cgroup_enable=cpuset cgroup_memory=1 cgroup_enable=memory'
        files.line(path='/boot/cmdline.txt', line='.*', replace=cmdline)
        # pi needs reboot now

    server.shell(commands=[
        'update-alternatives --set iptables /usr/sbin/iptables-legacy',
        'update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy',
    ])
    # needs reboot if this changed

# See https://github.com/rancher/k3s/issues/1802 and https://rancher.com/docs/k3s/latest/en/installation/private-registry/
files.directory(path='/etc/rancher/k3s')
files.template(src='templates/kube/registries.yaml.j2', dest='/etc/rancher/k3s/registries.yaml')

if host.name == 'bang':  # master
    files.template(
        src='templates/kube/k3s-server.service.j2',
        dest='/etc/systemd/system/k3s.service',
        master_ip=master_ip,
    )
    systemd.service(service='k3s.service', daemon_reload=True, enabled=True, restarted=True)

    # one-time thing at cluster create time? not sure
    # - name: Replace https://localhost:6443 by https://master-ip:6443
    #   command: >-
    #     k3s kubectl config set-cluster default
    #       --server=https://{{ master_ip }}:6443
    #       --kubeconfig ~{{ ansible_user }}/.kube/config

if host.name in ['slash', 'dash', 'frontbed', 'garage']:  # nodes
    # /var/lib/rancher/k3s/server/node-token is the source of the string in secrets/k3s_token
    token = open('secrets/k3s_token', 'rt').read().strip()

    files.template(
        src='templates/kube/k3s-node.service.j2',
        dest='/etc/systemd/system/k3s-node.service',
        master_ip=master_ip,
        token=token,
    )

    systemd.service(service='k3s-node.service', daemon_reload=True, enabled=True, restarted=True)

if host.name in ['bang', 'slash', 'dash']:  # hosts to admin from
    files.link(path='/usr/local/bin/kubectl', target='/usr/local/bin/k3s')
    files.directory(path='/home/drewp/.kube', user='drewp', group='drewp')
    files.line(path="/home/drewp/.zshrc", line="KUBECONFIG", replace='export KUBECONFIG=/etc/rancher/k3s/k3s.yaml')

    files.chown(target='/etc/rancher/k3s/k3s.yaml', user='root', group='drewp')
    files.chmod(target='/etc/rancher/k3s/k3s.yaml', mode='640')

    files.download(src='https://storage.googleapis.com/skaffold/releases/v1.34.0/skaffold-linux-amd64',
                   dest='/usr/local/bin/skaffold',
                   user='root',
                   group='root',
                   mode='755')
