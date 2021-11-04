from invoke import task

@task
def playbook(ctx):
    ctx.run('''
HOME=/root
export HOME
eval `keychain --quiet --eval id_ecdsa`
cd /my/proj/infra
env/bin/pyinfra inventory.py users.py
    ''', pty=True)
