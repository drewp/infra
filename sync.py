from pyinfra import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import apt, systemd

# bang instance is in k8s (/my/serv/filesync/syncthing); the rest are run with systemd.
# Configs are in ~/.config/syncthing/ on each box
if host.name in ['dash', 'dot', 'slash', 'plus']:
    apt.packages(packages=['syncthing'])

    # now we have /lib/systemd/system/syncthing@.service
    user = 'ari' if host.name == 'dot' else 'drewp'
    systemd.service(service=f'syncthing@{user}', running=True, enabled=True)

    # also consider https://github.com/Martchus/syncthingtray tray status viewer on dtops
