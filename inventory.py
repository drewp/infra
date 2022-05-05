ssh_user = 'root'
ssh_key = '/root/.ssh/id_ecdsa'

big = [
    ('bang', {
        'wireguard_address': '10.5.0.1',
    }),  #
    ('dash', {
        "mac": "b8:97:5a:17:d7:1f",
        'ssh_hostname': 'dash',
        'wireguard_address': '10.5.0.5',
    }),
    ('slash', {
        'mac': 'c8:60:00:98:ec:74',
        'ssh_hostname': 'slash',
        'wireguard_address': '10.5.0.6',
    }),
    ('dot', {
        'mac': '1c:c1:de:56:e6:70',
        'ssh_hostname': 'dot',
        'wireguard_address': '10.5.0.30',
    })
]

pi = [
    ('frontbed', {
        'mac': 'b8:27:eb:e9:d3:44',
        'ssh_hostname': 'frontbed',
        'wireguard_address': '10.5.0.17',
    }),
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
    # ('plus', {
    #     'ssh_hostname': '10.2.0.136',
    #     'wireguard_address': '10.5.0.110',
    # }),
]
