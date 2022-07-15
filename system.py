import os

from pyinfra import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, server, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

TZ = 'America/Los_Angeles'

server.hostname(hostname=host.name)

def timezone():
    files.link(path='/etc/localtime', target=f'/usr/share/zoneinfo/{TZ}')
    files.replace(path='/etc/timezone', text='.*', replace=TZ)
    apt.packages(update=True,
                cache_time=86400,
                packages=['tzdata'],
                force=True,
                _env={
                    'TZ': TZ,
                    'LANG': 'en_US.UTF-8',
                    'DEBIAN_FRONTEND': 'noninteractive'
                })

def fstab():
    fstab_file = f'files/fstab/{host.name}'
    if os.path.exists(fstab_file):
        files.put(src=fstab_file, dest='/etc/fstab')

def pi_tmpfs():
    for line in [
            'tmpfs /var/log tmpfs defaults,noatime,mode=0755 0 0',
            'tmpfs /tmp tmpfs defaults,noatime 0 0',
    ]:
        files.line(path="/etc/fstab", line=line, replace=line)

    # stop SD card corruption (along with some mounts in fstab)
    apt.packages(packages=['dphys-swapfile'], present=False)


# don't try to get aufs-dkms on rpi-- https://github.com/docker/for-linux/issues/709
def podman_inecure_registry():
    files.template(src='templates/kube/podman_registries.conf.j2', dest='/etc/containers/registries.conf.d/bang.conf')


def no_sleep():
    server.shell(commands=['systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target'])

def nfs_server():
    apt.packages(packages=['nfs-kernel-server'])
    files.template(src='templates/bang_exports.j2', dest='/etc/exports')

    # sudo zfs set sharenfs="rw=10.5.0.0/16" stor6

def smaller_journals():
    files.line(name='shorter systemctl log window, for disk space',
               path='/etc/systemd/journald.conf',
               line='MaxFileSec',
               replace="MaxFileSec=7day")

    for port in [80, 443]:
        files.template(src="templates/webforward.service.j2", dest=f"/etc/systemd/system/web_forward_{port}.service", port=port)
        systemd.service(service=f'web_forward_{port}', enabled=True, restarted=True)

timezone()
fstab()

if not is_pi:
    files.line(path='/etc/update-manager/release-upgrades', line="^Prompt=", replace="Prompt=normal")

if is_pi and host.name != 'pipe':
    pi_tmpfs()

if not is_pi:    
    podman_inecure_registry()

if host.name in ['bang', 'pipe']:
    no_sleep()

if host.name == 'bang':
    nfs_server()

if host.name == 'prime':
    smaller_journals()