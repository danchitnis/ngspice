FROM ubuntu:latest
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 build-essential cmake git ca-certificates curl wget autoconf automake libtool bison flex pkg-config libzstd-dev libedit-dev zlib1g-dev lsb-release software-properties-common gnupg && \
    rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://sh.rustup.rs -o /tmp/rustup-init.sh && \
    sh /tmp/rustup-init.sh -y --profile minimal --default-toolchain stable && \
    rm /tmp/rustup-init.sh
ENV PATH=/root/.cargo/bin:$PATH
COPY linux/osdi/*.py linux/osdi/EEcircuit-engine-LICENSE.txt /opt/ngspice-osdi/
COPY examples/asap7/inverter.cir.in /opt/ngspice-osdi/examples/asap7/inverter.cir.in
COPY examples/pkp3/inverter.cir.in /opt/ngspice-osdi/examples/pkp3/inverter.cir.in
WORKDIR /work
