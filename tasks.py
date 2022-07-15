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
    ctx.run(cmd + 'inventory.py net.py', pty=True)


@task
def dns(ctx):
    ctx.run(cmd + 'inventory.py dns.py', pty=True)


@task
def dns_check(ctx):
    ctx.run(cmd + 'inventory.py dns_check.py -v', pty=True)

@task
def dns_k8s_check(ctx):
    ctx.run('env/bin/python dns_k8s_check.py', pty=True)


@task
def wireguard(ctx):
    ctx.run(cmd + 'inventory.py wireguard.py', pty=True)


@task
def kube(ctx):
    ctx.run(cmd + 'inventory.py kube.py ', pty=True)

@task
def kube_bang(ctx):
    ctx.run(cmd + 'inventory.py kube.py --limit bang', pty=True)


@task
def sync(ctx):
    ctx.run(cmd + 'inventory.py sync.py ', pty=True)


@task
def mail(ctx):
    ctx.run(cmd + 'inventory.py mail.py ', pty=True)

@task
def pipe(ctx):
    ctx.run(cmd + 'inventory.py pipe.py --limit pipe', pty=True)


@task
def all(ctx):
    configs = [
        'users.py',
        'ssh.py',
        'system.py',
        'packages.py',
        'net.py',
        'dns.py',
        'wireguard.py',
        'kube.py',
        'sync.py',
        'mail.py',
    ]
    # https://github.com/Fizzadar/pyinfra/issues/787
    #ctx.run(' '.join([cmd, 'inventory.py'] + configs), pty=True)
    for c in configs:
        ctx.run(' '.join([cmd, 'inventory.py', c]), pty=True, warn=True)
    ctx.run('touch /my/proj/infra/ran_all.timestamp')


@task
def get_fact(ctx, host='dash', fact='server.LinuxDistribution'):
    ctx.run(cmd + f'{host} -vv fact {fact}', pty=True)
