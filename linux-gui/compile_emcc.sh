#!/bin/bash
echo started...

cd ~

git clone https://github.com/danchitnis/ngspice-sf-mirror.git ngspice-ngspice

wait

cd ~/emsdk
source ./emsdk_env.sh

cd ~/ngspice-ngspice

cd ngspice-ngspice
./autogen.sh
mkdir release
cd release

#emconfigure ../configure --disable-debug

wait

#emmake make
