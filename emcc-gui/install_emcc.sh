#!/bin/bash
echo started...

git clone https://github.com/emscripten-core/emsdk.git

wait
cd emsdk

wait
./emsdk install latest

wait
./emsdk activate latest
