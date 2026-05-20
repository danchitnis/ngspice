# ngspice container tool


Docker environment to build [ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/) from source with a focus on command-line operations



## Linux

![Linux Build CI](https://github.com/danchitnis/ngspice/workflows/Linux%20Build%20CI/badge.svg)

First clone the repository:

```bash
git clone https://github.com/danchitnis/ngspice.git
cd ngspice
```

Build the [Docker](https://www.docker.com/) image:

```bash
cd linux
sudo docker build -t ngspice .
```

Run the Docker image:

```bash
docker run -it -v $(realpath .):/mnt ngspice
```

This will create a new directory `build` which contains the generated `ngspice` executable



## WASM

For WASM build please [EEcircuit-engine](https://github.com/eelab-dev/EEcircuit-engine)



## Ngspice mirror

![Mirror CI](https://github.com/danchitnis/ngspice/workflows/Mirror%20CI/badge.svg)

https://github.com/danchitnis/ngspice-sf-mirror

## Details

See: https://sourceforge.net/p/ngspice/patches/99/

## Contributions

[ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/)

[SPICE3f5](https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/spice/spice.html)
