import subprocess
import requests
import tempfile

# this would be nice to write a hosts file for dhcp so it gives better names to
# stuff like webcams, but it needs lanscape to be up.

def prepare_dhcp_hosts():
    lanscape_ip = subprocess.check_output([
        'kubectl',
        'get',
        'svc',
        'lanscape',
        "-o=jsonpath={.spec.clusterIP}",
    ],
                                          encoding='ascii')
    url = f'http://{lanscape_ip}/dnsConfig'
    resp = requests.get(url)
    resp.raise_for_status()
    lanscape_config = resp.json()

    dhcp_hosts = tempfile.NamedTemporaryFile(mode='wt', encoding='ascii')
    dhcp_hosts.write("# written by pyinfra\n\n")
    for row in lanscape_config['dhcp_table']:
        dhcp_hosts.write(f'{row["mac"]},{row["hostname"]},{row["ip"]},24h\n')
    dhcp_hosts.flush()
    return dhcp_hosts