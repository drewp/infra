ssh_user = 'root'
ssh_key = '/root/.ssh/id_ecdsa'

big = [
    ('bang', {
        'wireguard_address': '10.5.0.1',
    }),
    ('dash', {
        'ssh_hostname': '10.1.0.5',
        'interface': 'enp2s0',
        'addr': '10.1.0.5',
        'wireguard_address': '10.5.0.5',
    }),
    ('slash', {
        'ssh_hostname': '10.1.0.6',
        'interface': 'enp3s0',
        'addr': '10.1.0.6',
        'wireguard_address': '10.5.0.6',
    }),
    ('dot', {
        'ssh_hostname': '10.2.0.57',
        'interface': 'enp3s0',
        'addr': '10.2.0.30',
        'wireguard_address': '10.5.0.30',
    })
]
pi = [
    ('frontbed', {
        'ssh_hostname': '10.2.0.17',
        'interface': 'eth0',
        'addr': '10.2.0.17',
        'wireguard_address': '10.5.0.17',
    }),
    ('garage', {
        'ssh_hostname': '10.2.0.19',
        'interface': 'eth0',
        'addr': '10.2.0.14',
        'wireguard_address': '10.5.0.14',
    }),
]

remote = [
    ('prime', {
        'ssh_hostname': 'public.bigasterisk.com',
        'wireguard_address': '10.5.0.2',
    }),
]
