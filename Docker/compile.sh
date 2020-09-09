#!/bin/bash
echo started...

git clone https://git.code.sf.net/p/ngspice/ngspice ngspice-ngspice

wait

cd ngspice-ngspice
./autogen.sh
mkdir release
cd release
../configure --disable-debug

wait

make 2>&1 | tee make.log
