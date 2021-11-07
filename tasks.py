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
def get_fact(ctx, host='dash', fact='server.LinuxDistribution'):
    ctx.run(cmd + f'{host} fact {fact}', pty=True)
