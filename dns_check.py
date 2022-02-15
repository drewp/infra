# run key dns lookups everywhere
import subprocess
import tempfile

import requests
from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

def check(name, addr):
    server.shell(commands=[
        # note: one big string
        f"out=`dnsget -q {name}`; "
        f'[ -n "$out" ] || exit 1; '
        f"if [ $out != {addr} ]; then echo got $out >&2 ; exit 1; fi"
        ])

'''
idea: read a file that looks like this:

on host:   bang       dash      slash     prime
lookup:
bang       127.0.1.1  10.1.0.1  10.1.0.1  10.5.0.1
bang5      10.5.0.1   10.5.0.1  10.5.0.1  10.5.0.1
dash       10.1.0.5   127.0.1.1 10.1.0.5  10.5.0.5
etc

(or another idea: wireguard everywhere all the time)
'''

# outside k8s
if host.name in ['dash', 'bang', 'slash']:
    check('dash', '10.1.0.5')
elif host.name in ['prime']:
    check('dash', '10.5.0.5')
else:
    check('dash', '10.1.0.5')

if host.name in ['bang']:
    check('bang', '10.2.0.1')
elif host.name in ['prime']:
    check('bang', '10.5.0.1')
else:
    check('bang', '10.2.0.1')

check('bang5', '10.5.0.1')
check('prime', '10.5.0.2')
check('slash', '10.1.0.6')

# inside k8s