#!/bin/bash
echo Entryponit script is Running...

NGSPICE_HOME="https://github.com/danchitnis/ngspice-sf-mirror"
#NGSPICE_HOME="https://git.code.sf.net/p/ngspice/ngspice"

echo -e "Ngsice git repository is $NGSPICE_HOME\n"

cd /opt
git clone https://github.com/emscripten-core/emsdk.git
cd emsdk
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh

echo -e "\n"
echo -e "installing ngspice...\n"

cd /opt

git clone $NGSPICE_HOME ngspice-ngspice

cd ngspice-ngspice

#https://www.cyberciti.biz/faq/how-to-use-sed-to-find-and-replace-text-in-files-in-linux-unix-shell/
#https://sourceforge.net/p/ngspice/patches/99/
sed -i 's/-Wno-unused-but-set-variable/-Wno-unused-const-variable/g' ./configure.ac

./autogen.sh
mkdir release
cd release

emconfigure ../configure --disable-debug

wait

emmake make
#emmake make 2>&1 | tee make.log

wait



cd src
mv ngspice ngspice.js
mkdir -p /mnt/build
\cp ngspice.js ngspice.wasm /mnt/build


echo -e "\n"
echo -e "This script is ended\n"





