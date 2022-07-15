from pyinfra.operations import apt, files, git, server


def ntop():
    files.directory('/opt/ntop')

    apt.packages(packages=[
        "build-essential", "git", "bison", "flex", "libxml2-dev", "libpcap-dev", "libtool", "libtool-bin", "rrdtool",
        "librrd-dev", "autoconf", "pkg-config", "automake", "autogen", "redis-server", "wget", "libsqlite3-dev", "libhiredis-dev",
        "libmaxminddb-dev", "libcurl4-openssl-dev", "libpango1.0-dev", "libcairo2-dev", "libnetfilter-queue-dev", "zlib1g-dev",
        "libssl-dev", "libcap-dev", "libnetfilter-conntrack-dev", "libreadline-dev", "libjson-c-dev", "libldap2-dev", "rename",
        "libsnmp-dev", "libexpat1-dev", "libsnmp-dev", "libmaxminddb-dev", "libradcli-dev", "libjson-c-dev", "libzmq3-dev",
        "libmariadb-dev"
    ])
    git.repo(src='https://github.com/ntop/nDPI.git', dest='/opt/ntop/nDPI', branch='4.4-stable')
    git.repo(src='https://github.com/ntop/ntopng.git', dest='/opt/ntop/ntopng', branch='5.4-stable')

    server.shell('cd /opt/ntop/nDPI; ./autogen.sh; ./configure; make -j 6')
    server.shell('cd /opt/ntop/ntopng; ./autogen.sh; ./configure; make -j 6')


ntop()
