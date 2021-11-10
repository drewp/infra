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
def system(ctx):
    ctx.run(cmd + 'inventory.py system.py', pty=True)


@task
def net(ctx):
    # workaround for https://github.com/Fizzadar/pyinfra/issues/702
    ctx.run(cmd + '-vv inventory.py exec -- rm -f /tmp/pyinfra-7ed098bf43cef74d8ab8ea095e4a95c92605c61c', pty=True)

    ctx.run(cmd + '-vv inventory.py net.py --limit slash ', pty=True)


@task
def wireguard(ctx):
    ctx.run(cmd + 'inventory.py wireguard.py', pty=True)


@task
def get_fact(ctx, host='dash', fact='server.LinuxDistribution'):
    ctx.run(cmd + f'{host} fact {fact}', pty=True)
