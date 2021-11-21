from pyinfra import host
from pyinfra.operations import apt, files, server, systemd

if host.name == 'prime':
    apt.packages(packages=['postfix', 'isync'])
    files.template(src='templates/mail/main.cf.j2', dest='/etc/postfix/main.cf')
    files.template(src='templates/mail/mydestination.j2', dest='/etc/postfix/mydestination')
    files.put(src='secrets/mail/sender_access', dest='/etc/postfix/sender_access')
    files.put(src='secrets/mail/virtual', dest='/etc/postfix/virtual')

    server.shell(commands=[
        'postmap /etc/postfix/sender_access',
        'postmap /etc/postfix/virtual',
        'postfix reload',
    ])
    systemd.service(service='postfix.service', enabled=True, running=True)
    # maybe needs 'postfix@-.service', unclear

    # something to run ~drewp/mbsync/go at startup

    # maybe freshen the mbsync client cert when we're running this deploy, too

# other machines, route mail to bang or prime for delivery
