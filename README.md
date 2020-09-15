# ngspice

Docker environment to build [ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/) from source with a focus on command-line operations

## Build

```bash
sudo docker build -t ngspice .
```

## Run

```bash
docker run -it -p 33890:3389 spice bar
```

To read and write files into the running container use the -v option when launching the container.

Then use RDP to connect the Fedora environment. Go to the home directory and run

```bash
./compile.sh
```

Notice that the docker image is based on [container-xrdp](https://github.com/danchitnis/container-xrdp)
