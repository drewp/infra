# run key dns lookups everywhere
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
bang.bigasterisk.com
bang.bigasterisk.com.
prime
projects.bigasterisk.com
etc

(or another idea: wireguard everywhere all the time)
'''

if host.name in ['dash', 'bang', 'slash']:
    check('dash', '10.2.0.212')
    check('projects.bigasterisk.com', '10.2.0.1')
elif host.name in ['prime']:
    check('dash', '10.5.0.5')
    check('projects.bigasterisk.com', '10.2.0.1')  # expected the public addr, but fine
else:
    check('dash', '10.2.0.212')
    check('projects.bigasterisk.com', '10.2.0.1')

if host.name in ['prime']:
    check('bang', '10.5.0.1')
    check('slash', '10.5.0.6')
else:
    check('bang', '10.2.0.1')
    check('slash', '10.2.0.127')

check('bang5', '10.5.0.1')
check('prime', '10.5.0.2')

