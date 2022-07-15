from pyinfra import host
from pyinfra.facts.server import LinuxDistribution
from pyinfra.operations import files, systemd

is_pi = host.get_fact(LinuxDistribution)['name'] in ['Debian', 'Raspbian GNU/Linux']

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

if not is_pi:
    files.line(path='/etc/ssh/sshd_config', line="^UseDNS\b", replace="UseDNS no")
    systemd.service(service='sshd', reloaded=True)
