from invoke import task

'🛁 bang(pts/2):/my/proj/infra% sudo inv users ssh system packages net dns wireguard kube sync mail'

cmd = '''
HOME=/root
export HOME
eval `keychain --quiet --eval id_ecdsa`
cd /my/proj/infra
env/bin/pyinfra '''


@task
def users(ctx):
    ctx.run(cmd + 'inventory.py users.py', pty=True)


@task
def ssh(ctx):
    ctx.run(cmd + 'inventory.py ssh.py', pty=True)


@task
def system(ctx):
    ctx.run(cmd + 'inventory.py system.py', pty=True)


@task
def packages(ctx):
    ctx.run(cmd + 'inventory.py packages.py', pty=True)


@task
def net(ctx):
    ctx.run(cmd + 'inventory.py net.py -v', pty=True)


@task
def dns(ctx):
    ctx.run(cmd + 'inventory.py dns.py -v', pty=True)
    ctx.run(cmd + 'inventory.py dns_check.py -v', pty=True)

@task
def dns_check(ctx):
    ctx.run(cmd + 'inventory.py dns_check.py -v', pty=True)


@task
def wireguard(ctx):
    ctx.run(cmd + 'inventory.py wireguard.py', pty=True)


@task
def kube(ctx):
    ctx.run(cmd + 'inventory.py kube.py -vv ', pty=True)


@task
def sync(ctx):
    ctx.run(cmd + 'inventory.py sync.py ', pty=True)


@task
def mail(ctx):
    ctx.run(cmd + 'inventory.py mail.py ', pty=True)


@task
def get_fact(ctx, host='dash', fact='server.LinuxDistribution'):
    ctx.run(cmd + f'{host} -vv fact {fact}', pty=True)
