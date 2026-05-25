#!/bin/bash
set -e

echo "========================================"
echo " Building ngspice Linux Executable"
echo "========================================"

# 1. Clone the ngspice source from the mirror
if [ -d "ngspice-ngspice" ]; then
    echo "Removing existing ngspice-ngspice directory..."
    rm -rf ngspice-ngspice
fi
echo "Cloning ngspice source..."
git clone --depth 1 https://github.com/danchitnis/ngspice-sf-mirror.git ngspice-ngspice

# 2. Build the Docker image
echo "Building Docker image..."
docker build -t ngspice-build .

# 3. Copy the ngspice sources into the docker
# We do this by creating a container and using docker cp
echo "Creating temporary builder container..."
docker rm -f ngspice-builder > /dev/null 2>&1 || true
docker create --name ngspice-builder -w /workspace ngspice-build sleep infinity
docker start ngspice-builder

echo "Copying sources into the container..."
docker cp ngspice-ngspice ngspice-builder:/workspace/

# 4. Run the ngspice build steps inside docker
echo "Starting build inside the container (this may take a few minutes)..."
docker exec ngspice-builder sh -c "
    cd /workspace/ngspice-ngspice
    ./autogen.sh
    mkdir -p release
    cd release
    ../configure --disable-debug --enable-openmp --with-readline=no
    make -j$(nproc)
"

# 5. Copy out the ngspice executable
echo "Extracting the compiled ngspice executable..."
docker cp ngspice-builder:/workspace/ngspice-ngspice/release/src/ngspice ./ngspice

# 6. Cleanup the docker container
echo "Cleaning up..."
docker rm -f ngspice-builder

echo ""
echo "Build complete! The ngspice executable is ready in $(pwd)/ngspice"
ls -l ngspice
