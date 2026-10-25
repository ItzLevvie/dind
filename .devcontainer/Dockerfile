# syntax=docker/dockerfile:1
ARG BASE_IMAGE=debian:trixie-slim
FROM ${BASE_IMAGE}

# Use matching, supported Docker components instead of unrelated nightly builds.
# The optional CA secret is for builds in a managed workspace with an HTTPS proxy.
RUN --mount=type=secret,id=proxy_ca \
    set -eu; \
    if [ -s /run/secrets/proxy_ca ]; then \
      export SSL_CERT_FILE=/run/secrets/proxy_ca; \
      printf 'Acquire::https::CaInfo "/run/secrets/proxy_ca";\n' > /etc/apt/apt.conf.d/99-build-ca; \
    fi; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes \
      ca-certificates curl docker.io docker-cli docker-compose docker-buildx \
      qemu-utils 7zip python3 git gh openssh-client openssh-server iptables iproute2 ethtool \
      procps util-linux htop; \
    rm -f /etc/ssh/ssh_host_*; \
    rm -f /etc/apt/apt.conf.d/99-build-ca; \
    rm -rf /var/lib/apt/lists/*

ARG TAILSCALE_VERSION=1.102.4
RUN --mount=type=secret,id=proxy_ca \
    set -eu; \
    ca_file=/etc/ssl/certs/ca-certificates.crt; \
    if [ -s /run/secrets/proxy_ca ]; then ca_file=/run/secrets/proxy_ca; fi; \
    curl --fail --location --retry 3 --cacert "$ca_file" \
      "https://pkgs.tailscale.com/stable/tailscale_${TAILSCALE_VERSION}_amd64.tgz" \
      --output /tmp/tailscale.tgz; \
    curl --fail --location --retry 3 --cacert "$ca_file" \
      "https://pkgs.tailscale.com/stable/tailscale_${TAILSCALE_VERSION}_amd64.tgz.sha256" \
      --output /tmp/tailscale.sha256; \
    cd /tmp; \
    printf '%s  tailscale.tgz\n' "$(cut -d ' ' -f 1 tailscale.sha256)" | sha256sum --check -; \
    tar -xzf tailscale.tgz; \
    install -m 0755 "tailscale_${TAILSCALE_VERSION}_amd64/tailscale" /usr/local/bin/tailscale; \
    install -m 0755 "tailscale_${TAILSCALE_VERSION}_amd64/tailscaled" /usr/local/bin/tailscaled; \
    rm -rf tailscale.tgz tailscale.sha256 "tailscale_${TAILSCALE_VERSION}_amd64"

RUN update-alternatives --set iptables /usr/sbin/iptables-legacy \
    && update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
