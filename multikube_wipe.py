from pyinfra import host
from pyinfra.operations import files, server, systemd

from multikube_config import server_node, nodes

def k3s_wipe():
    files.put(dest='/usr/local/bin/k3s-killall.sh', src='files/kube/k3s-killall.sh', mode='a+rx')
    files.put(dest='/usr/local/bin/k3s-uninstall.sh', src='files/kube/k3s-uninstall.sh', mode='a+rx')
    server.shell(['k3s-uninstall.sh'])

if host.name in nodes + [server_node]:
    k3s_wipe()
