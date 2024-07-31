
#!/bin/bash

# Function to handle errors
handle_error() {
    echo "Error: $1" >&2
    exit 1
}

echo "Entrypoint script is Running..."

NGSPICE_HOME="https://github.com/danchitnis/ngspice-sf-mirror"
#NGSPICE_HOME="https://git.code.sf.net/p/ngspice/ngspice"

echo -e "Ngspice git repository is $NGSPICE_HOME\n"

cd /opt || handle_error "Failed to change directory to /opt"
git clone https://github.com/emscripten-core/emsdk.git || handle_error "Failed to clone emsdk repository"
cd emsdk || handle_error "Failed to change directory to emsdk"
./emsdk install latest || handle_error "Failed to install latest emsdk"
./emsdk activate latest || handle_error "Failed to activate latest emsdk"
source ./emsdk_env.sh || handle_error "Failed to source emsdk environment"

echo -e "\n"
echo -e "Installing ngspice...\n"

cd /opt || handle_error "Failed to change directory to /opt"

git clone $NGSPICE_HOME ngspice-ngspice || handle_error "Failed to clone ngspice repository"

cd ngspice-ngspice || handle_error "Failed to change directory to ngspice-ngspice"

#https://www.cyberciti.biz/faq/how-to-use-sed-to-find-and-replace-text-in-files-in-linux-unix-shell/
#https://sourceforge.net/p/ngspice/patches/99/
#https://sed.js.org/
sed -i 's/-Wno-unused-but-set-variable/-Wno-unused-const-variable/g' ./configure.ac || handle_error "Failed to modify configure.ac (1)"
sed -i 's/AC_CHECK_FUNCS(\[time getrusage\])/AC_CHECK_FUNCS(\[time\])/g' ./configure.ac || handle_error "Failed to modify configure.ac (2)"

./autogen.sh || handle_error "Failed to run autogen.sh"
mkdir release || handle_error "Failed to create release directory"
cd release || handle_error "Failed to change directory to release"

emconfigure ../configure --disable-debug || handle_error "Failed to run emconfigure"

wait

emmake make || handle_error "Failed to run emmake make"

wait

cd src || handle_error "Failed to change directory to src"
mv ngspice ngspice.js || handle_error "Failed to rename ngspice to ngspice.js"
mkdir -p /mnt/build || handle_error "Failed to create /mnt/build directory"
cp ngspice.js ngspice.wasm /mnt/build || handle_error "Failed to copy files to /mnt/build"

echo -e "\n"
echo -e "This script has completed successfully\n"






