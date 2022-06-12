import subprocess

from pyinfra import host
from pyinfra.facts.files import FindInFile
from pyinfra.operations import apt, files, server, systemd

# other options:
#   https://www.reddit.com/r/WireGuard/comments/fkr240/shortest_path_between_peers/
#   https://github.com/k4yt3x/wireguard-mesh-configurator
#   https://github.com/mawalu/wireguard-private-networking
#


def peer_block(hostname, public_key, allowed_ips, endpoint=None, keepalive=None):
    out = f'''\

[Peer]
# {hostname}
PublicKey = {public_key}
AllowedIPs = {allowed_ips}
'''
    if endpoint is not None:
        out += f'Endpoint = {endpoint}\n'
    if keepalive is not None:
        out += f'PersistentKeepalive = {keepalive}\n'
    return out


for wireguard_interface in ['wg0', 'bogasterisk']:
    if wireguard_interface == 'bogasterisk' and host.name != 'prime':
        continue

    # note- this is specific to the wg0 setup. Other conf files don't use it.
    wireguard_ip = host.host_data['wireguard_address']

    apt.packages(packages=['wireguard'])
    # new pi may fail with 'Unable to access interface: Protocol not supported'. reboot fixes.

    priv_key_lines = host.get_fact(FindInFile, path=f'/etc/wireguard/{wireguard_interface}.conf', pattern=r'PrivateKey.*')
    if not priv_key_lines:
        priv_key = subprocess.check_output(['wg', 'genkey']).strip().decode('ascii')
    else:
        priv_key = priv_key_lines[0].split(' = ')[1]

    pub_key = subprocess.check_output(['wg', 'pubkey'], input=priv_key.encode('ascii')).strip().decode('ascii')
    # todo: if this was new, it should be added to a file of pubkeys that peer_block can refer to

    files.template(
        src=f'templates/wireguard/{wireguard_interface}.conf.j2',
        dest=f'/etc/wireguard/{wireguard_interface}.conf',
        mode='600',
        wireguard_ip=wireguard_ip,
        priv_key=priv_key,
        peer_block=peer_block,
    )
    svc = f'wg-quick@{wireguard_interface}.service'

    files.template(src='templates/wireguard/wg.service.j2',
                   dest=f'/etc/systemd/system/{svc}',
                   wireguard_interface=wireguard_interface)
    systemd.service(service=f'{svc}', enabled=True, restarted=True, daemon_reload=True)

    # files.link(path=f'/etc/systemd/system/multi-user.target.wants/{svc}', target='/lib/systemd/system/wg-quick@.service')

    systemd.service(service=svc, daemon_reload=True, restarted=True, enabled=True)

if host.name == 'bang':
    # recompute, or else maybe dnsmasq_10.5 won't start
    server.shell("systemctl enable dnsmasq_10.2.service")
    server.shell("systemctl enable dnsmasq_10.5.service")
    server.shell("systemctl enable wg-quick@wg0.service")