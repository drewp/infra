import os
from pyinfra import host
from pyinfra.operations import server, files, apt, ssh, systemd
from pyinfra.facts.server import LinuxDistribution

bang_is_old = True  # remove after upgrade
is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']
is_wifi_pi = host.name in ['frontdoor', 'living']

TZ = 'America/Los_Angeles'

#
# system
#

server.hostname(hostname=host.name)
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

fstab_file = f'files/{host.name}_fstab'
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
# pkgs
#

if not is_pi:
    apt.key(keyserver='keyserver.ubuntu.com', keyid='8B48AD6246925553')

if is_pi:
    apt.packages(packages=['mandb', 'apt-listchanges'], present=False)
    files.template(src='templates/pi_sources.list.j2', dest='/etc/apt/sources.list', rel='bullseye')
    # 'apt upgrade'?
    apt.packages(update=True, packages=['dirmngr', 'gnupg2', 'apt-utils'])

    apt.key(src='https://ftp-master.debian.org/keys/archive-key-8.asc')
    apt.key(src='https://ftp-master.debian.org/keys/archive-key-8-security.asc')
    apt.key(src='https://ftp-master.debian.org/keys/archive-key-9-security.asc')

    files.file(path='/etc/apt/sources.list.d/raspi.list', present=False)

    if is_wifi_pi:
        files.put(dest="/etc/network/interfaces.d/wlan0", src="files/pi_wlan0_powersave")
        ssh.command(host.name, "iw wlan0 set power_save off")

    # see https://www.raspberrypi.org/documentation/configuration/config-txt/memory.md#:~:text=txt-,gpu_mem,-Specifies
    # to port to pyinfra
    #- name: unused display; give ram to OS
    #  lineinfile: dest=/boot/config.txt line="gpu_mem=16" regexp="^gpu_mem="
    #  when: "'with_x11' not in group_names"

    # for beacon
    #enable_uart=1
    #dtoverlay=pi3-miniuart-bt
    #core_freq=250

    # for tiny_screen
    #to port to pyinfra
    #- lineinfile: dest=/boot/config.txt line="dtparam=spi=on" regexp="^dtparam=spi="

    # i hope this is deletable
    # downgrade strictness so I can install from https://archive.raspberrypi.org/
    # https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=907788
    #- lineinfile: dest=/etc/ssl/openssl.cnf line="#CipherString = DEFAULT@SECLEVEL=2" regexp="CipherString ?="

    # may be fixed in k3s, not sure
    # raspbian defaults to `iptables -V` -> iptables v1.8.4 (nf_tables), which won't work with k3s
    # - command: update-alternatives --set iptables /usr/sbin/iptables-legacy
if not is_pi:
    apt.key(src='https://dl.google.com/linux/linux_signing_key.pub')
    apt.repo(src='deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main')

    apt.key(src='https://packages.microsoft.com/keys/microsoft.asc')
    apt.repo(src="deb [arch=amd64,arm64,armhf] http://packages.microsoft.com/repos/code stable main")

    apt.ppa(src="ppa:savoury1/blender")

    apt.key(keyserver='keyserver.ubuntu.com', keyid='F24AEA9FB05498B7')
    apt.repo(src="deb [arch=amd64,i386] https://repo.steampowered.com/steam/ stable steam")

if False and is_pi:
    apt.key(src="https://download.docker.com/linux/raspbian/gpg")
    apt.repo(src="deb [arch=armhf] https://download.docker.com/linux/raspbian stretch stable")
    apt.repo(src='deb http://deb.debian.org/debian/ unstable main')  # maybe for WG

apt.packages(packages=[
    'build-essential',
#    'i2c-tools',
    'rsync',
])

if not is_pi:
    apt.packages(packages=[
        'keychain',
        'python3-docker',
        'python3-invoke',
        'python3-pip',
        'python3-virtualenv',
        'sysstat',
    ])

if not is_pi and not bang_is_old:
    apt.packages(packages='mlocate', present=False)
    apt.packages(packages='plocate')

#
# ssh
#

systemd.service(
    service='ssh',
    running=True,
    enabled=True,
)

files.line(path='/etc/ssh/ssh_config', line="HashKnownHosts", replace="HashKnownHosts no")

if is_pi:
    auth_keys = '/home/pi/.ssh/authorized_keys'
    files.file(path=auth_keys, user='pi', group='pi', mode=600)
    for pubkey in [
            'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNlR7hereUHqw/RHQau0F7+vQZKAxduM+SD4R76FhC+4Zi078Pv04ZLe9qdM/NBlB/grLGhG58vaGmnWPpJ3QJs= drewp@plus',
            'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBOR+iV8Qm/rAfmq0epXYfnp5ZTfBl8eidFzw1GmyZ3fPUFAshWn839fQ5DPj9xDPtMy9kTtrB5bK1SnynFzDqzQ= drewp@bang',
    ]:
        files.line(path=auth_keys, line=pubkey, replace=pubkey)

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

#
# special hosts
#

if host.name == "bang":
    apt.packages(packages=[
        'libzfs2linux',
        'zfsutils-linux',
        'zfs-zed',
        'zfs-auto-snapshot',
    ])

# This is usable on pi where we don't care when they reboot:
#- name: apt_upgrade
#  apt: upgrade=full
#- name: Check if a reboot is required
#  register: file
#  stat: path=/var/run/reboot-required get_md5=no
#- name: Reboot the server
#  command: /sbin/reboot
#  when: file.stat.exists == true
