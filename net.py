from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

is_wifi = host.name in ['frontdoor', 'living', 'plus']


def cleanup():
    # past attempts
    files.file(path='/etc/netplan/99-pyinfra-written.yaml', present=False)
    files.file(path='/etc/network/interfaces', present=False)

    for search_dir in [
            # search path per `man systemd.network`:
            # /lib/systemd/network              # These OS files are ok.
            '/usr/local/lib/systemd/network/',  # Probably no such dir.
            '/run/systemd/network/',  # Previous netplan attempts dumped in here.
            #'/etc/systemd/network/',  # I'm going to work in here.
    ]:
        files.sync(
            src="files/empty_dir/",
            dest=search_dir,
            delete=True,
        )

    apt.packages(packages=['network-manager'], present=False)

    # On bang:
    #   Now using a HW router for this firewall. No incoming connections.
    #   test connections from the outside:
    #   http://www.t1shopper.com/tools/port-scanner/
    # On prime:
    #   using digitalocean network config:
    #   https://cloud.digitalocean.com/networking/firewalls/f68899ae-1aac-4469-b379-59ce2bbc988f/droplets?i=7c5072
    apt.packages(packages=['ufw'], present=False)


if host.name == 'prime':
    cleanup()

    files.directory('/etc/systemd/network')
    files.template(
        src="templates/net/prime.network.j2",
        dest="/etc/systemd/network/99-prime.network",
        mac=host.host_data['mac'],
    )

elif host.name == 'bang':
    cleanup()

    files.directory('/etc/systemd/network')

    files.template(src="templates/net/bang_10.2.network.j2", dest="/etc/systemd/network/99-10.2.network")
    files.template(src="templates/net/bang_isp.network.j2", dest="/etc/systemd/network/99-isp.network")
    systemd.service(service='systemd-networkd.service', enabled=True, running=True, restarted=True)
    server.sysctl(key='net.ipv4.ip_forward', value=1, persist=True)
    files.template(src="templates/net/house_net.service.j2", dest="/etc/systemd/system/house_net.service", out_interface='ens4')
    systemd.service(service='house_net.service', daemon_reload=True, enabled=True, running=True, restarted=True)

elif host.name == 'plus':
    pass

elif host.name == 'pipe':   
    cleanup()

    files.directory('/etc/systemd/network')

    files.template(src="templates/net/pipe_10.2.network.j2", dest="/etc/systemd/network/99-10.2.network")
    files.template(src="templates/net/pipe_isp.network.j2", dest="/etc/systemd/network/99-isp.network")
    systemd.service(service='systemd-networkd.service', enabled=True, running=True, restarted=True)
    server.sysctl(key='net.ipv4.ip_forward', value=1, persist=True)
    files.template(src="templates/net/house_net.service.j2", dest="/etc/systemd/system/house_net.service", out_interface='eth0')
    systemd.service(service='house_net.service', daemon_reload=True, enabled=True, running=True, restarted=True)


else:
    cleanup()

    if is_wifi:
        files.put(src="secrets/wpa_supplicant.conf", dest="/etc/wpa_supplicant/wpa_supplicant.conf")

    # addr = host.host_data['addr']
    # net = addr[:4]
    # gateway = net + '.0.1'
    # dns = gateway

    files.template(
        src="templates/net/singlenic.network.j2",
        dest="/etc/systemd/network/99-bigasterisk.network",
        create_remote_dir=True,
        mac=host.host_data['mac'],
    )
    systemd.service(service='systemd-networkd.service', enabled=True, running=True, restarted=True)
