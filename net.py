from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

is_wifi = host.name in ['frontdoor', 'living', 'plus']

if host.name in [
        'garage',
        'dash',
        'slash',
        'frontbed',
        'prime',
]:
    # previous version
    files.file(path='/etc/netplan/99-pyinfra-written.yaml', present=False)

    for search_dir in [
            # search path per `man systemd.network`:
            # /lib/systemd/network              # These OS files are ok.
            '/usr/local/lib/systemd/network/',  # Probably no such dir.
            '/run/systemd/network/',  # Previous netplan attempts dumped in here.
            '/etc/systemd/network/',  # I'm going to work in here.
    ]:
        files.sync(
            src="files/empty_dir/",
            dest=search_dir,
            delete=True,
        )

    addr = host.host_data['addr']
    if addr.startswith('10.'):
        net = addr[:4]
        gateway = net + '.0.1'
        dns = gateway
    elif addr == '162.243.138.136':
        gateway = '162.243.138.1'
        dns = '10.5.0.1 8.8.8.8 8.8.4.4'
    else:
        raise ValueError(addr)
    files.template(src="templates/house.network.j2",
                   dest="/etc/systemd/network/99-house.network",
                   mac=host.host_data['mac'],
                   addr=addr,
                   gateway=gateway,
                   dns=dns)
    systemd.service(service='systemd-networkd.service', running=True, restarted=True)

    # you may have to rm this file first: https://github.com/Fizzadar/pyinfra/issues/719
    files.link(path='/etc/resolv.conf', target='/run/systemd/resolve/resolv.conf', force=True)
    files.template(src='templates/resolved.conf.j2', dest='/etc/systemd/resolved.conf')

    if is_wifi:
        files.put(src="secrets/wpa_supplicant.conf", dest="/etc/wpa_supplicant/wpa_supplicant.conf")

    files.template(src='templates/hosts.j2', dest='/etc/hosts')

    systemd.service(service='systemd-resolved.service', running=True, restarted=True)

    # ns = '10.2.0.1'
    # if host.name == 'prime':
    #     ns = '8.8.8.8'
    # elif host.name in ['slash']:
    #     ns = '10.1.0.1'
    # files.template(src='templates/resolv.conf.j2', dest='/etc/resolv.conf', ns=ns)

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
