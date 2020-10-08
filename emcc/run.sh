#!/bin/bash
echo Entryponit script is Running...

cd /opt
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh

echo -e "\n"
echo -e "installing ngspice...\n"

cd /opt

git clone https://git.code.sf.net/p/ngspice/ngspice ngspice-ngspice

cp ./misc_time.c ./ngspice-ngspice/src/misc

cd ngspice-ngspice

./autogen.sh
mkdir release
cd release

emconfigure ../configure --disable-debug

wait

emmake make

wait



cd src
mv ngspice ngspice.js
mkdir -p /mnt/build
\cp ngspice.js ngspice.wasm /mnt/output


echo -e "\n"
echo -e "This script is ended\n"





