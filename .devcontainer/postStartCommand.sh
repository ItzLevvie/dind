export REPOSITORY=github

rm --force /var/run/docker.pid
rm --force /var/run/docker/containerd/containerd.pid

sysctl --write net.ipv4.ip_forward=1
sysctl --write net.ipv6.conf.all.forwarding=1

ethtool --features eth0 rx-udp-gro-forwarding on
ethtool --features eth0 rx-gro-list off

swapoff /tmp/swap
fallocate --length 16G /tmp/swap
chmod 600 /tmp/swap
mkswap /tmp/swap
swapon /tmp/swap

dockerd --seccomp-profile unconfined --experimental &> /dev/null &
