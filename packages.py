from pyinfra import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, ssh, server

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']
is_wifi_pi = host.name in ['frontdoor', 'living']

if not is_pi:
    apt.key(keyserver='keyserver.ubuntu.com', keyid='8B48AD6246925553')

if is_pi:
    apt.packages(packages=['mandb', 'apt-listchanges'], present=False)
    files.template(src='templates/pi_sources.list.j2', dest='/etc/apt/sources.list', rel='bullseye')
    # 'apt upgrade'?
    apt.packages(
        update=False,  # see system.py
        packages=['dirmngr', 'gnupg2', 'apt-utils'])

    apt.key(src='https://ftp-master.debian.org/keys/archive-key-8.asc')
    apt.key(src='https://ftp-master.debian.org/keys/archive-key-8-security.asc')
    apt.key(src='https://ftp-master.debian.org/keys/archive-key-9-security.asc')
    apt.key(keyserver='keyserver.ubuntu.com', keyid='04EE7237B7D453EC')
    apt.key(keyserver='keyserver.ubuntu.com', keyid='648ACFD622F3D138')

    files.file(path='/etc/apt/sources.list.d/raspi.list', present=False)

    if is_wifi_pi:
        files.put(dest="/etc/network/interfaces.d/wlan0", src="files/pi_wlan0_powersave")
        ssh.command(host.name, "iw wlan0 set power_save off")

    files.template(src='templates/boot_config.txt.j2', dest='/boot/config.txt')

if not is_pi and host.name != 'prime':
    apt.key(src='https://dl.google.com/linux/linux_signing_key.pub')
    apt.repo(src='deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main')

    apt.key(src='https://packages.microsoft.com/keys/microsoft.asc')
    apt.repo(src="deb [arch=amd64,arm64,armhf] http://packages.microsoft.com/repos/code stable main")

    apt.key(keyserver='keyserver.ubuntu.com', keyid='F24AEA9FB05498B7')
    apt.repo(src="deb [arch=amd64,i386] https://repo.steampowered.com/steam/ stable steam")

apt.packages(packages=[
    'build-essential',
    # 'i2c-tools',
    'rsync',
    'dstat',
    'ifstat',
    'mosquitto-clients',
    'ncdu',
    "udns-utils",
    "atool",
])

if not is_pi:
    apt.packages(packages=[
        'keychain',
        'python3-docker',
        'python3-invoke',
        'python3-pip',
        'python3-virtualenv',
        'sysstat',
        'debian-goodies',
        'lxterminal',
        'iotop',
        'lpr',
        'nodejs',
        'npm',
    ])
    vers = '0.24.4' # see https://github.com/kovidgoyal/kitty/releases
    home = '/home/drewp'
    local = f"{home}/.local/kitty"
    dl = f'/tmp/kitty-{vers}-x86_64.txz'
    files.download(src=f"https://github.com/kovidgoyal/kitty/releases/download/v{vers}/kitty-{vers}-x86_64.txz",
                   dest=dl)
    files.makedirs(local, exist_ok=True)
    server.shell([
        f"mkdir -p {local}",  # https://github.com/Fizzadar/pyinfra/issues/777
        f"aunpack --extract-to={local} {dl}",
    ])
    files.link(target="{local}/bin/kitty", path="{home}/bin/kitty")

    server.shell([
        "npm install -g pnpm@6.32.3",
        ])

if not is_pi and not (host.name == 'prime'):
    apt.packages(packages='mlocate', present=False)
    apt.packages(packages='plocate')

if host.name == "bang":
    apt.packages(packages=[
        'iptables',
        'openntpd',
        'ntpdate',
        'zfsutils-linux',
        'zfs-zed',
        'zfs-auto-snapshot',
    ])

if host.name == 'plus':
    apt.packages(packages=['network-manager'])
