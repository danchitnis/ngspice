#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status.

echo "Started..."

git clone https://github.com/danchitnis/ngspice-sf-mirror.git ngspice-ngspice || { echo "Git clone failed"; exit 1; }

cd ngspice-ngspice || { echo "Failed to change directory to ngspice-ngspice"; exit 1; }
./autogen.sh || { echo "autogen.sh failed"; exit 1; }
mkdir release || { echo "Failed to create release directory"; exit 1; }
cd release || { echo "Failed to change directory to release"; exit 1; }
../configure --disable-debug --enable-openmp --with-readline=no || { echo "Configure failed"; exit 1; }

make || { echo "Make failed"; exit 1; }

cd src || { echo "Failed to change directory to src"; exit 1; }
mkdir -p /mnt/build || { echo "Failed to create /mnt/build directory"; exit 1; }
cp ngspice /mnt/build || { echo "Failed to copy ngspice to /mnt/build"; exit 1; }

echo -e "\n"
echo -e "This script has completed successfully\n"