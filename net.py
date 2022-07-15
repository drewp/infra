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

    apt.packages(packages=['network-manager', 'connman'], present=False)

    # On bang:
    #   Now using a HW router for this firewall. No incoming connections.
    #   test connections from the outside:
    #   http://www.t1shopper.com/tools/port-scanner/
    # On prime:
    #   using digitalocean network config:
    #   https://cloud.digitalocean.com/networking/firewalls/f68899ae-1aac-4469-b379-59ce2bbc988f/droplets?i=7c5072
    apt.packages(packages=['ufw'], present=False)

server.sysctl(key='net.ipv6.conf.all.disable_ipv6', value=1, persist=True)

files.directory('/etc/systemd/network')
if host.name == 'prime':
    cleanup()

    files.template(
        src="templates/net/prime.network.j2",
        dest="/etc/systemd/network/99-prime.network",
        mac=host.host_data['mac'],
    )

elif host.name == 'bang':
    cleanup()

    files.template(src="templates/net/bang_10.2.network.j2", dest="/etc/systemd/network/99-10.2.network")
    files.file(path="/etc/systemd/network/99-isp.network", present=False)
    files.file(path="/etc/systemd/system/house_net.service", present=False)
    systemd.service(service='house_net.service', enabled=False, running=False)

elif host.name == 'plus':
    pass

elif host.name == 'pipe':   
    cleanup()

    files.template(src="templates/net/pipe_10.2.network.j2", dest="/etc/systemd/network/99-10.2.network")
    files.template(src="templates/net/pipe_isp.network.j2", dest="/etc/systemd/network/99-isp.network")
    server.sysctl(key='net.ipv4.ip_forward', value=1, persist=True)
    files.template(src="templates/net/house_net.service.j2", dest="/etc/systemd/system/house_net.service", out_interface='eth0')
    systemd.service(service='house_net.service', daemon_reload=True, enabled=True, running=True, restarted=True)


else:
    cleanup()

    if is_wifi:
        files.put(src="secrets/wpa_supplicant.conf", dest="/etc/wpa_supplicant/wpa_supplicant.conf")

    files.template(
        src="templates/net/singlenic.network.j2",
        dest="/etc/systemd/network/99-bigasterisk.network",
        create_remote_dir=True,
    )

systemd.service(service='systemd-networkd.service', enabled=True, running=True, restarted=True)