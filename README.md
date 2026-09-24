# ngspice container tool


Docker environment to build [ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/) from source with a focus on command-line operations



## Linux

[![Ubuntu Build CI](https://github.com/danchitnis/ngspice/actions/workflows/linux.yml/badge.svg)](https://github.com/danchitnis/ngspice/actions/workflows/linux.yml)

Clone the repository and run the standard Linux build (Docker is required):

```bash
git clone https://github.com/danchitnis/ngspice.git
cd ngspice
./linux/build.sh
```

The executable is written to `linux/ngspice`.

### Optional ASAP7 and PKP3 OSDI build

From the repository root, run:

```bash
./linux/build.sh --osdi
```

The executable is written to `linux/build/osdi/ngspice`. It is a Linux ngspice build with OSDI support enabled. The compiled model implementations are in the separate `linux/build/osdi/catalog.osdi` library; the generated examples load it with `pre_osdi`. The standard build's `linux/ngspice` is without OSDI support.

The output directory also contains model cards under `models/asap7/` and `models/pkp3/`, one small inverter example for each available process corner under `examples/`, licenses, and `manifest.json`. The `linux/osdi/` directory contains build scripts, not the finished executable.

From the repository root, run an example in the build image:

```bash
docker run --rm -v "$(pwd)/linux/build/osdi:/bundle" -w /bundle ngspice-osdi-builder \
  ./ngspice -b examples/asap7/tt.cir
```

On Linux, you can also run the executable directly if its architecture matches your machine. From the repository root:

```bash
(cd linux/build/osdi && ./ngspice -b examples/asap7/tt.cir)
(cd linux/build/osdi && ./ngspice -b examples/pkp3/fs.cir)
```

The OSDI build fetches the current default branches of ngspice, OpenVAF Reloaded, VA-Models, ASAP7, and PKP3 inside Docker each time. It builds OpenVAF to compile BSIM-CMG and PKP3 into `catalog.osdi`; ASAP7 uses that BSIM-CMG implementation with adapted process cards. The build exports every discovered flavor and corner, verifies both polarities with DC simulations, and records the resolved commits and tool versions in `manifest.json`. An upstream source change that the adapters cannot translate stops the build for review. Downloaded model sources are not placed in the example folders or exported bundle.

Use OSDI `N` devices with drain, gate, source, bulk terminals. ASAP7 uses `L=21n NFIN=1`; PKP3 uses `L=16n W=35n NF=1` in the included examples.

## WASM

For a WASM build, see [EEcircuit-engine](https://github.com/eelab-dev/EEcircuit-engine).

## Ngspice mirror

![Mirror CI](https://github.com/danchitnis/ngspice/workflows/Mirror%20CI/badge.svg)

https://github.com/danchitnis/ngspice-sf-mirror

## Contributions

[ngspice](https://sourceforge.net/p/ngspice/ngspice/ci/master/tree/)

[SPICE3f5](https://ptolemy.berkeley.edu/projects/embedded/pubs/downloads/spice/spice.html)
