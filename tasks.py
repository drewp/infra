from invoke import task

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
    # workaround for https://github.com/Fizzadar/pyinfra/issues/702
    ctx.run(cmd + 'inventory.py exec -- rm -f /tmp/pyinfra-7ed098bf43cef74d8ab8ea095e4a95c92605c61c', pty=True, warn=True)

    ctx.run(cmd + 'inventory.py net.py', pty=True)


@task
def wireguard(ctx):
    ctx.run(cmd + 'inventory.py wireguard.py', pty=True)


@task
def kube(ctx):
    ctx.run(cmd + 'inventory.py kube.py ', pty=True)


@task
def sync(ctx):
    ctx.run(cmd + 'inventory.py sync.py ', pty=True)


@task
def mail(ctx):
    ctx.run(cmd + 'inventory.py mail.py -vv', pty=True)


@task
def get_fact(ctx, host='dash', fact='server.LinuxDistribution'):
    ctx.run(cmd + f'{host} -vv fact {fact}', pty=True)
