from invoke import task

cmd = '''
HOME=/root
export HOME
eval `keychain --quiet --eval id_ecdsa`
cd /my/proj/infra
env/bin/pyinfra inventory.py '''

@task
def users(ctx):
    ctx.run(cmd + 'users.py', pty=True)

@task
def system(ctx):
    ctx.run(cmd + 'system.py', pty=True)
