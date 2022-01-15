from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

is_wifi = host.name in ['frontdoor', 'living', 'plus']
prime_public_addr = '162.243.138.136'
prime_gateway = '162.243.138.1'


def cleanup():
    # past attempts
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

    apt.packages(packages=['network-manager'], present=False)


if host.name in [
        'garage',
        'dash',
        'slash',
        'frontbed',
        'prime',
]:
    cleanup()

    addr = host.host_data['addr']
    if addr.startswith('10.'):
        net = addr[:4]
        gateway = net + '.0.1'
        dns = gateway
    elif addr == prime_public_addr:
        gateway = prime_gateway
        dns = '10.5.0.1 8.8.8.8 8.8.4.4'
    else:
        raise ValueError(addr)

    if is_wifi:
        files.put(src="secrets/wpa_supplicant.conf", dest="/etc/wpa_supplicant/wpa_supplicant.conf")

    files.template(src="templates/house.network.j2",
                   dest="/etc/systemd/network/99-house.network",
                   mac=host.host_data['mac'],
                   addr=addr,
                   gateway=gateway,
                   dns=dns)
    systemd.service(service='systemd-networkd.service', running=True, restarted=True)

    # ns = '10.2.0.1'
    # if host.name == 'prime':
    #     ns = '8.8.8.8'
    # elif host.name in ['slash']:
    #     ns = '10.1.0.1'
    # files.template(src='templates/resolv.conf.j2', dest='/etc/resolv.conf', ns=ns)

if host.name == 'plus':
    apt.packages(packages=['network-manager'], present=True)

if host.name == 'bang':
    files.template(src='templates/bang_interfaces.j2', dest='/etc/network/interfaces', user='root', group='root', mode='644')

    # Now using a HW router for this firewall. No incoming connections.
    # test connections from the outside:
    # http://www.t1shopper.com/tools/port-scanner/
    apt.packages(packages=['ufw'], present=False)

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
