from pyinfra import host
from pyinfra.operations import apt, files, systemd


def resolv_conf_use_systemd_networkd():
    files.link(path='/etc/resolv.conf', target='/run/systemd/resolve/resolv.conf', force=True)


def resolv_conf_static_file():
    files.file(path='/etc/resolv.conf', present=False, force=True)
    files.template(
        src='templates/resolv.conf.j2',
        dest='/etc/resolv.conf',
        # review this- it's probably a bad dep on bang. maybe both 10.5.0.1 and a public ns would be ok
        ns='10.5.0.1' if host.name in ['prime', 'plus'] else '10.2.0.3',
        force=True)


def dnsmasq_instance(net_name, house_iface, dhcp_range, router):
    files.directory(path=f'/opt/dnsmasq/{net_name}')
    files.template(
        src='templates/dnsmasq/dnsmasq.conf.j2',
        dest=f'/opt/dnsmasq/{net_name}/dnsmasq.conf',
        net=net_name,
        house_iface=house_iface,
        dhcp_range=dhcp_range,
        router=router,
        dhcp_enabled=net_name == '10.2' and host.name == 'pipe')
    files.template(src='templates/dnsmasq/hosts.j2', dest=f'/opt/dnsmasq/{net_name}/hosts', net=net_name)
    files.template(src='/dev/null', dest=f'/opt/dnsmasq/{net_name}/dhcp_hosts', net=net_name)

    files.template(src='templates/dnsmasq/dnsmasq.service.j2',
                   dest=f'/etc/systemd/system/dnsmasq_{net_name}.service',
                   net=net_name)
    if net_name == '10.2':
        systemd.service(service=f'dnsmasq_{net_name}', enabled=True, restarted=True, daemon_reload=True)


files.template(src='templates/hosts.j2', dest='/etc/hosts')
resolv_conf_use_systemd_networkd()
files.template(src='templates/resolved.conf.j2', dest='/etc/systemd/resolved.conf')
systemd.service(service='systemd-resolved.service', running=True, restarted=True)

if host.name == 'bang':
    apt.packages(packages=['dnsmasq'])
    systemd.service(service='dnsmasq', enabled=False, running=False)
    files.directory(path='/opt/dnsmasq')

    dnsmasq_instance('10.5', house_iface='unused', dhcp_range='unused', router='unused')  # only works after wireguard is up

elif host.name == 'pipe':
    apt.packages(packages=['dnsmasq'])
    systemd.service(service='dnsmasq', enabled=False, running=False)
    files.directory(path='/opt/dnsmasq')
    dnsmasq_instance('10.2', house_iface='eth1', dhcp_range='10.2.0.20,10.2.0.120', router='10.2.0.3')

else:
    pass
