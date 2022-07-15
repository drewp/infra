from pyinfra import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, files, server

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']


def kitty():
    vers = '0.25.2'  # see https://github.com/kovidgoyal/kitty/releases
    home = '/home/drewp'
    local = f"{home}/.local/kitty"
    dl = f'/tmp/kitty-{vers}-x86_64.txz'
    files.download(src=f"https://github.com/kovidgoyal/kitty/releases/download/v{vers}/kitty-{vers}-x86_64.txz", dest=dl)
    files.directory(local)
    server.shell([
        f"mkdir -p {local}",  # https://github.com/Fizzadar/pyinfra/issues/777
        f"aunpack --extract-to={local} {dl}",
    ])
    files.link(target="{local}/bin/kitty", path="{home}/bin/kitty")


def pnpm():
    server.shell([
        # https://github.com/pnpm/pnpm/releases
        # but also https://pnpm.io/installation#compatibility
        "npm install -g pnpm@6.32.22",
    ])


def proper_locate():
    apt.packages(packages='mlocate', present=False)
    if not is_pi and host.name not in ['prime', 'pipe']:
        apt.packages(packages='plocate')


def pi_sources():
    apt.packages(packages=['mandb', 'apt-listchanges'], present=False)
    files.template(src='templates/pi_sources.list.j2', dest='/etc/apt/sources.list', rel='bullseye')
    # 'apt upgrade'?
    apt.packages(
        update=False,  # see system.py
        packages=['dirmngr', 'gnupg2', 'apt-utils', 'aptitude'])

    apt.key(src='https://ftp-master.debian.org/keys/archive-key-8.asc')
    apt.key(src='https://ftp-master.debian.org/keys/archive-key-8-security.asc')
    apt.key(src='https://ftp-master.debian.org/keys/archive-key-9-security.asc')
    apt.key(keyserver='keyserver.ubuntu.com', keyid='04EE7237B7D453EC')
    apt.key(keyserver='keyserver.ubuntu.com', keyid='648ACFD622F3D138')

    files.file(path='/etc/apt/sources.list.d/raspi.list', present=False)

    files.template(src='templates/boot_config.txt.j2', dest='/boot/config.txt')


if not is_pi:
    apt.key(keyserver='keyserver.ubuntu.com', keyid='8B48AD6246925553')

if host.name == 'pipe':
    apt.packages(packages=['mandb', 'apt-listchanges'], present=False)
    files.template(src='templates/odroid_sources.list.j2', dest='/etc/apt/sources.list', rel='focal')
elif is_pi:
    pi_sources()

if not is_pi:
    if host.name != 'prime':
        apt.key(src='https://dl.google.com/linux/linux_signing_key.pub')
        apt.repo(src='deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main')

        apt.key(src='https://packages.microsoft.com/keys/microsoft.asc')
        apt.repo(src="deb [arch=amd64,arm64,armhf] http://packages.microsoft.com/repos/code stable main")

        apt.key(keyserver='keyserver.ubuntu.com', keyid='F24AEA9FB05498B7')
        apt.repo(src="deb [arch=amd64,i386] https://repo.steampowered.com/steam/ stable steam")

    apt.packages(packages=[
        'debian-goodies',
        'ethtool',
        'htop',
        'iotop',
        'keychain',
        'lpr',
        'mercurial',
        'mtr-tiny',
        'net-tools',
        'nodejs',
        'npm',
        'oping',
        'python3-invoke',
        'python3-pip',
        'python3-virtualenv',
        'speedtest-cli',
        'sysstat',
        'tcpdump',
    ])
    if host.name in ['dash', 'slash', 'bang']:
        apt.packages(packages=[
            'podman-docker',
        ])
    if host.name != 'pipe':
        apt.packages(packages=[
            'reptyr',
        ])

    kitty()
    pnpm()

apt.packages(packages=[
    'build-essential',
    'dstat',
    'ifstat',
    'iproute2',  # needed for wireguard
    'kitty-terminfo',
    'mosquitto-clients',
    'ncdu',
    'rsync',
    'xosview',
    'zsh',
    "atool",
    "udns-utils",
    "wireguard-tools",
])

proper_locate()

if host.name == "bang":
    apt.packages(packages=[
        'dnsmasq',
        'iptables',
        'ntpdate',
        'openntpd',
        'zfs-auto-snapshot',
        'zfs-zed',
        'zfsutils-linux',
    ])

if host.name == 'plus':
    apt.packages(packages=[
        'network-manager',
    ])
