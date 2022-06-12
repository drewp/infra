import subprocess
import tempfile

import requests
from pyinfra import host
from pyinfra.operations import apt, files, server, systemd


def prepare_dhcp_hosts():
    lanscape_ip = subprocess.check_output([
        'kubectl',
        'get',
        'svc',
        '--field-selector=metadata.name=lanscape',
        "-o=jsonpath={.items[0].spec.clusterIP}",
    ],
                                          encoding='ascii')
    url = f'http://{lanscape_ip}/dnsConfig'
    resp = requests.get(url)
    resp.raise_for_status()
    lanscape_config = resp.json()

    dhcp_hosts = tempfile.NamedTemporaryFile(mode='wt', encoding='ascii')
    dhcp_hosts.write("# written by pyinfra\n\n")
    for row in lanscape_config['dhcp_table']:
        dhcp_hosts.write(f'{row["mac"]},{row["hostname"]},{row["ip"]},24h\n')
    dhcp_hosts.flush()
    return dhcp_hosts


#files.link('/etc/resolv.conf', '/run/systemd/resolve/stub-resolv.conf')

# files.file(path='/etc/resolv.conf', present=False)
# files.link(path='/etc/resolv.conf', present=False)  # bug
# server.shell(["rm -f /etc/resolv.conf"])  # broken fix
files.template(src='templates/resolv.conf.j2',
               dest='/etc/resolv.conf',
               # review this- it's probably a bad dep on bang. maybe both 10.5.0.1 and a public ns would be ok
               ns='10.5.0.1' if host.name in ['prime', 'plus'] else '10.2.0.1',
               force=True)

if host.name == 'bang':
    apt.packages(packages=['dnsmasq'])
    systemd.service(service='dnsmasq', enabled=False, running=False)
    files.directory(path='/opt/dnsmasq')

    dhcp_hosts = prepare_dhcp_hosts()

    for net_name in ['10.2', '10.5']:
        files.directory(path=f'/opt/dnsmasq/{net_name}')
        files.template(src='templates/dnsmasq/dnsmasq.conf.j2', dest=f'/opt/dnsmasq/{net_name}/dnsmasq.conf', net=net_name)
        files.template(src='templates/dnsmasq/hosts.j2', dest=f'/opt/dnsmasq/{net_name}/hosts', net=net_name)
        files.template(src=dhcp_hosts.name, dest=f'/opt/dnsmasq/{net_name}/dhcp_hosts', net=net_name)

        files.template(src='templates/dnsmasq/dnsmasq.service.j2',
                       dest=f'/etc/systemd/system/dnsmasq_{net_name}.service',
                       net=net_name)
        systemd.service(service=f'dnsmasq_{net_name}', enabled=True, restarted=True, daemon_reload=True)

if host.name in [
        'garage',
        'dash',
        'slash',
        'frontbed',
        'prime',
        'pipe'
]:
    files.template(src='templates/hosts.j2', dest='/etc/hosts')
    files.template(src='templates/resolved.conf.j2', dest='/etc/systemd/resolved.conf')
    systemd.service(service='systemd-resolved.service', running=True, restarted=True)
