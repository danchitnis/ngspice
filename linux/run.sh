#!/bin/bash
echo started...

git clone https://github.com/danchitnis/ngspice-sf-mirror.git ngspice-ngspice

wait

cd ngspice-ngspice
./autogen.sh
mkdir release
cd release
../configure --disable-debug --enable-openmp

wait

#make 2>&1 | tee make.log
make

wait

cd src
mkdir -p /mnt/build
\cp ngspice /mnt/build

echo -e "\n"
echo -e "This script is ended\n"