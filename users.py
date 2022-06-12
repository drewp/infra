from pyinfra import host
from pyinfra.operations import server
from pyinfra.facts.server import LinuxDistribution

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

# raspbian took 1000 for 'pi' group, but drewp is rarely used on pi
# setups so hopefully it won't matter much that drew group has a
# different id.
drewp_gid = 1000 if (not is_pi and host.name != 'pipe') else 501
drewp_uid = 501
drewp_groups = [
    'lp', 'adm', 'dialout', 'cdrom', 'sudo', 'audio', 'video', 'plugdev',
    'games', 'users', 'netdev', 'i2c', 'input', 'spi', 'gpio', 'fuse',
    'docker', 'render'
]

for group in [
        'fuse',
        'spi',
        'gpio',
        'i2c',
        'input',
        'netdev',
        'docker',
        'render',
]:
    server.group(group=group)

server.group(group='drewp', gid=drewp_gid)
server.user(user='drewp', group='drewp', groups=drewp_groups)

if not is_pi:
    server.group(group='adm', gid=4)
    server.group(group='cdrom', gid=24)
    server.group(group='dialout', gid=20)
    server.group(group='dip', gid=30)
    server.group(group='lp', gid=7)
    # prime has something on 109
    server.group(group='lpadmin', gid=200)
    server.group(group='plugdev', gid=46)
    server.group(group='docker', system=True)

    server.group(group='damon', gid=3011)
    server.group(group='ffg', gid=3008)

    server.group(group='drewnote', gid=1009)

    server.user(user='drewp',
                uid=drewp_uid,
                group='drewp',
                groups=drewp_groups)

    server.group(group='ari', gid=3019)
    server.user(user='ari',
                uid=3019,
                group='ari',
                groups=['audio', 'dialout', 'docker', 'lp', 'lpadmin', 'sudo', 'video'])

    server.user(user='ffg', uid=3013, group='ffg')

    server.user(user='darcsweb')

    server.user(user='newsbru', uid=1019)
    server.user(user='dmcc', uid=1013)

    server.group(group='elastic', gid=3018)
    server.user(user='elastic', uid=3018, group='elastic')

    server.group(group='kelsi', gid=1008)
    server.user(user='kelsi', uid=1008, group='elastic')

    server.group(group='drewnote', gid=1009)
    server.user(user='drewnote', uid=1009)

    server.group(group='prometheus', gid=1010)
    server.user(user='prometheus', uid=1010)

if is_pi:
    server.group(group='fuse')
    server.user(user='pi',
                uid=1000,
                group=7,
                groups=[
                    'lp', 'adm', 'dialout', 'cdrom', 'sudo', 'audio', 'video',
                    'plugdev', 'games', 'users', 'netdev', 'i2c', 'input',
                    'spi', 'gpio', 'fuse', 'docker'
                ])
