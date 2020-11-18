## [Live Demo 🚀](https://danchitnis.github.io/ngspice/emcc/)

# ngspice container tools

![EMCC Build CI](https://github.com/danchitnis/ngspice/workflows/EMCC%20Build%20CI/badge.svg)

Docker environment to build [ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/) from source with a focus on command-line operations

## WASM

We use [Emscripten](https://emscripten.org/) to compile the ngspice codebased into [WASM](https://webassembly.org/) to run client-side inside [compatible browsers](https://caniuse.com/?search=wasm).

First clone the repository:

```bash
git clone https://github.com/danchitnis/ngspice.git
cd ngspice
```

Build the [Docker](https://www.docker.com/) image:

```bash
cd emcc
sudo docker build -t ngspice:emcc .
```

Run the Docker image:

```bash
docker run -it -v $(realpath .):/mnt ngspice:emcc
```

This will create a new directory `build` which has the generated JS and WASM runtime files.

## Linux

First clone the repository:

```bash
git clone https://github.com/danchitnis/ngspice.git
cd ngspice
```

Build the [Docker](https://www.docker.com/) image:

```bash
cd linux
sudo docker build -t ngspice:linux .
```

Run the Docker image:

```bash
docker run -it -v $(realpath .):/mnt ngspice:linux
```

This will create a new directory `build` which contains the generated `ngspice` executable

## Windows

TBA

## GUI debug container

TBA

Notice that the docker image is based on [container-xrdp](https://github.com/danchitnis/container-xrdp)

## Ngspice mirror

![Mirror CI](https://github.com/danchitnis/ngspice/workflows/Mirror%20CI/badge.svg)

https://github.com/danchitnis/ngspice-sf-mirror

## Details

See: https://sourceforge.net/p/ngspice/patches/99/

## Contributions

[ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/)

[Emscripten](https://emscripten.org/)

[SPICE3f5](https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/spice/spice.html)
