FROM fedora:latest

RUN dnf -y update

RUN dnf -y install autoconf automake make bzip2

RUN dnf -y install libtool bison flex xz which

RUN dnf -y install git wget curl

RUN dnf clean all


COPY ./run.sh /
RUN chmod +x /run.sh


#ENTRYPOINT ["/run.sh"]

## run command:
## docker run -it -v $(realpath .):/mnt ngspice:emcc

## sudo dnf install mingw64-gcc mingw64-gcc-c++ mingw64-libgomp flex
## https://github.com/openvenues/libpostal/issues/134
## https://stackoverflow.com/questions/9229079/qt-compile-error-when-use-tslib-with-angstrom-g
## https://stackoverflow.com/questions/40615175/error-in-sysconf-in-c
##
## mingw64-configure ../configure --disable-debug --enable-openmp
## mingw64-make

## !!!! install flex !!!!!!
