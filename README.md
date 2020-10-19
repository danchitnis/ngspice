## [Live Demo 🚀](https://danchitnis.github.io/ngspice/emcc/)

# ngspice container tools

Docker environment to build [ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/) from source with a focus on command-line operations

## Browser

We use [Emscripten](https://emscripten.org/) to compile the ngspice codebased into [WASM](https://webassembly.org/) to run inside [compatible browsers](https://caniuse.com/?search=wasm).

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

TBA

## GUI debug container

TBA

Notice that the docker image is based on [container-xrdp](https://github.com/danchitnis/container-xrdp)

## Details

TBD
