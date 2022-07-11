ssh_user = 'root'
ssh_key = '/root/.ssh/id_ecdsa'

big = [
    ('bang', {
        'wireguard_address': '10.5.0.1',
    }),  #
    ('dash', {
        'ssh_hostname': '10.2.0.210',
        'wireguard_address': '10.5.0.5',
    }),
    ('slash', {
        'ssh_hostname': 'slash',
        'wireguard_address': '10.5.0.6',
    }),
    ('dot', {
        'ssh_hostname': 'dot',
        'wireguard_address': '10.5.0.30',
    })
]

small = [
    ('pipe', {
        'ssh_hostname': '10.2.0.3',
        'wireguard_address': '10.5.0.3',
    }),
]

pi = [
#    ('frontbed', {
#        'mac': 'b8:27:eb:e9:d3:44',
#        'ssh_hostname': 'frontbed',
#        'wireguard_address': '10.5.0.17',
#    }),
    ('garage', {
        'mac': 'b8:27:eb:81:17:92',
        'ssh_hostname': 'garage',
        'wireguard_address': '10.5.0.14',
    }),
]

remote = [
    ('prime', {
        'mac': '04:01:09:7f:89:01',
        'ssh_hostname': '162.243.138.136',
        'wireguard_address': '10.5.0.2',
    }),
    ('plus', {
        'ssh_hostname': 'plus',
        'wireguard_address': '10.5.0.110',
    }),
]
