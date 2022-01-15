from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

if host.name == 'bang':
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

if host.name in [
        'garage',
        'dash',
        'slash',
        'frontbed',
        'prime',
]:
    files.template(src='templates/hosts.j2', dest='/etc/hosts')

    files.link(path='/etc/resolv.conf', target='/run/systemd/resolve/resolv.conf')
    files.template(src='templates/resolved.conf.j2', dest='/etc/systemd/resolved.conf')

    systemd.service(service='systemd-resolved.service', running=True, restarted=True)
