from pyinfra import host
from pyinfra.facts.hardware import Ipv4Addrs
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, server, systemd

bang_is_old = True
is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']
is_wifi = host.name in ['frontdoor', 'living', 'plus']
ssh_host = host.host_data.get('ssh_hostname', host.name)

if is_wifi:
    # todo: netplan could do this, below
    files.put(src="secrets/wpa_supplicant.conf", dest="/etc/wpa_supplicant/wpa_supplicant.conf")

files.template(src='templates/hosts.j2', dest='/etc/hosts')

if host.name == 'prime':
    # prime should have gotten this through netplan, but i give up.
    #
    # Note the DNS list: this list is tried randomly, not in order, so we could have
    # some trouble with internal names
    files.template(src='templates/prime_resolved.conf.j2', dest='/etc/systemd/resolved.conf')
else:
    files.template(src='templates/resolved.conf.j2', dest='/etc/systemd/resolved.conf')
systemd.service(service='systemd-resolved.service', running=True, restarted=True)

ns = '10.2.0.1'
if host.name == 'prime':
    ns = '8.8.8.8'
elif host.name in ['dash', 'slash']:
    ns = '10.1.0.1'
files.template(src='templates/resolv.conf.j2', dest='/etc/resolv.conf', ns=ns)

if host.name in ['dash', 'slash', 'garage', 'frontbed', 'dot']:
    # might need to upgrade pi systemd if there are errors in this part
    apt.packages(packages=['netplan.io'])
    for bad in [
            '01-netcfg.yaml',
            '01-network-manager-all.yaml',
            '00-installer-config.yaml',
            '99-ansible-written.yaml',
            '99-dns.conf',
            ]:
        files.file(path=f'/etc/netplan/{bad}', present=False)
    addrs = host.get_fact(Ipv4Addrs)
    ipv4Interface = host.host_data['interface']
    ipv4Address = host.host_data['addr']
    files.template(src='templates/netplan.yaml.j2',
                   dest='/etc/netplan/99-pyinfra-written.yaml',
                   ipv4Interface=ipv4Interface,
                   ipv4Address=ipv4Address)
    server.shell(commands=['netplan apply'])

apt.packages(packages=['network-manager'], present=host.name in ['plus'])

if host.name == 'bang':
    files.template(src='templates/bang_interfaces.j2', dest='/etc/network/interfaces', user='root', group='root', mode='644')
    apt.packages(packages=['iptables', 'openntpd', 'ntpdate'])
    server.shell(commands=['systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target'])

    apt.packages(packages=['nfs-kernel-server'])
    files.template(src='templates/bang_exports.j2', dest='/etc/exports')

    # Now using a HW router for this firewall. No incoming connections.
    # test connections from the outside:
    # http://www.t1shopper.com/tools/port-scanner/
    apt.packages(packages=['ufw'], present=False)

    apt.packages(packages=['dnsmasq'])
    systemd.service(service='dnsmasq', enabled=False, running=False)
    files.directory(path='/opt/dnsmasq')

    for net_name in ['10.1', '10.2', '10.5']:
        files.directory(path=f'/opt/dnsmasq/{net_name}')
        files.template(src='templates/dnsmasq/dnsmasq.conf.j2', dest=f'/opt/dnsmasq/{net_name}/dnsmasq.conf', net=net_name)
        files.template(src='templates/dnsmasq/hosts.j2', dest=f'/opt/dnsmasq/{net_name}/hosts', net=net_name)
        files.template(src='templates/dnsmasq/dhcp_hosts.j2', dest=f'/opt/dnsmasq/{net_name}/dhcp_hosts', net=net_name)

        files.template(src='templates/dnsmasq/dnsmasq.service.j2',
                       dest=f'/etc/systemd/system/dnsmasq_{net_name}.service',
                       net=net_name)
        systemd.service(service=f'dnsmasq_{net_name}', restarted=True, daemon_reload=True)

if host.name == 'prime':
    # using digitalocean network config:
    # https://cloud.digitalocean.com/networking/firewalls/f68899ae-1aac-4469-b379-59ce2bbc988f/droplets?i=7c5072
    apt.packages(packages=['ufw'], present=False)

    files.line(name='shorter systemctl log window, for disk space',
               path='/etc/systemd/journald.conf',
               line='MaxFileSec',
               replace="MaxFileSec=7day")

    for port in [80, 443]:
        files.template(src="templates/webforward.service.j2", dest=f"/etc/systemd/system/web_forward_{port}.service", port=port)
        systemd.service(service=f'web_forward_{port}', enabled=True, restarted=True)
