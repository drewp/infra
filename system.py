import os

from pyinfra import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, server, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

TZ = 'America/Los_Angeles'

server.hostname(hostname=host.name)

#
# timezone
#

files.link(path='/etc/localtime', target=f'/usr/share/zoneinfo/{TZ}')
files.replace(path='/etc/timezone', match='.*', replace=TZ)
apt.packages(update=True,
             cache_time=86400,
             packages=['tzdata'],
             force=True,
             env={
                 'TZ': TZ,
                 'LANG': 'en_US.UTF-8',
                 'DEBIAN_FRONTEND': 'noninteractive'
             })

#
# fstab
#

fstab_file = f'files/fstab/{host.name}'
if os.path.exists(fstab_file):
    files.put(src=fstab_file, dest='/etc/fstab')
if is_pi:
    for line in [
            'tmpfs /var/log tmpfs defaults,noatime,mode=0755 0 0',
            'tmpfs /tmp tmpfs defaults,noatime 0 0',
    ]:
        files.line(path="/etc/fstab", line=line, replace=line)

    # stop SD card corruption (along with some mounts in fstab)
    apt.packages(packages=['dphys-swapfile'], present=False)

#
# docker (delete this?)
#

# don't try to get aufs-dkms on rpi-- https://github.com/docker/for-linux/issues/709
if not is_pi:
    apt.packages(packages=['docker.io'], no_recommends=True)
    files.put(src='files/docker_daemon.json', dest='/etc/docker/daemon.json')
    systemd.service(service='docker', running=True, enabled=True, restarted=True)

if not is_pi:
    files.line(path='/etc/update-manager/release-upgrades', line="^Prompt=", replace="Prompt=normal")

    files.line(path='/etc/ssh/sshd_config', line="^UseDNS\b", replace="UseDNS no")
    systemd.service(service='sshd', reloaded=True)
