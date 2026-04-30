FROM debian:sid-slim

RUN DEBIAN_FRONTEND=noninteractive apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install sudo --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install wget --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install ca-certificates --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install iptables --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install qemu-utils --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install p7zip-full --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install openssh-server --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install htop --no-install-recommends --yes
RUN DEBIAN_FRONTEND=noninteractive apt-get install ethtool --no-install-recommends --yes

RUN rm --recursive --force /var/lib/apt/lists/*

RUN update-alternatives --set iptables /usr/sbin/iptables-legacy
RUN update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy

# https://www.speedtest.net/apps/cli
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/speedtest --output-document /usr/local/bin/speedtest
RUN chmod +x /usr/local/bin/speedtest

# https://github.com/fastfetch-cli/fastfetch/actions/workflows/ci.yml?query=event%3Apush+is%3Asuccess+branch%3Adev
# Click on the latest run then download "fastfetch-linux-amd64" file under "Artifacts"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/fastfetch --output-document /usr/local/bin/fastfetch
RUN chmod +x /usr/local/bin/fastfetch

# https://pkgs.tailscale.com/unstable
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/tailscale --output-document /usr/local/bin/tailscale
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/tailscaled --output-document /usr/local/bin/tailscaled
RUN chmod +x /usr/local/bin/tailscale
RUN chmod +x /usr/local/bin/tailscaled

# https://github.com/moby/moby/actions/workflows/buildkit.yml?query=event%3Apush+is%3Asuccess+branch%3Amaster
# Click on the latest run then download the "binary" file under "Artifacts"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/docker-proxy --output-document /usr/local/bin/docker-proxy
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/dockerd --output-document /usr/local/bin/dockerd
RUN chmod +x /usr/local/bin/docker-proxy
RUN chmod +x /usr/local/bin/dockerd

# https://github.com/docker/cli/actions/workflows/build.yml?query=event%3Apush+is%3Asuccess+branch%3Amaster
# Click on the latest run then download the "binary-linux-amd64" file under "Artifacts"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/docker-linux-amd64 --output-document /usr/local/bin/docker
RUN chmod +x /usr/local/bin/docker

# https://github.com/containerd/containerd/actions/workflows/release.yml?query=event%3Apush+is%3Asuccess+branch%3Amain
# Click on the latest run then download the "release-tars-linux-amd64" file under "Artifacts"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/containerd-shim-runc-v2 --output-document /usr/local/bin/containerd-shim-runc-v2
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/containerd --output-document /usr/local/bin/containerd
RUN chmod +x /usr/local/bin/containerd-shim-runc-v2
RUN chmod +x /usr/local/bin/containerd

# https://github.com/opencontainers/runc/actions/workflows/validate.yml?query=event%3Apush+is%3Asuccess+branch%3Amain
# Click on the latest run then download the "release-XXXXXXXXXXX" file under "Artifacts"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/runc.amd64 --output-document /usr/local/bin/runc
RUN chmod +x /usr/local/bin/runc

# https://github.com/docker/compose/actions/workflows/ci.yml?query=event%3Apush+is%3Asuccess+branch%3Amain
# Click on the latest run then download the "compose" file under "Artifacts"
RUN mkdir --parents /usr/local/lib/docker/cli-plugins
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/docker-compose-linux-x86_64 --output-document /usr/local/lib/docker/cli-plugins/docker-compose
RUN chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# https://github.com/docker/buildx/actions/workflows/build.yml?query=event%3Apush+is%3Asuccess+branch%3Amaster
# Click on the latest run then download the "buildx" file under "Artifacts"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/buildx.linux-amd64 --output-document /usr/local/lib/docker/cli-plugins/docker-buildx
RUN chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

# https://github.com/cli/cli/releases/latest
# Download the "GitHub CLI 2.XX.X linux amd64" file under "Assets"
RUN wget https://github.com/ItzLevvie/artifacts/releases/latest/download/gh --output-document /usr/local/bin/gh
RUN chmod +x /usr/local/bin/gh
