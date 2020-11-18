FROM fedora:latest

RUN dnf -y update


RUN dnf -y install python3 python3-pip

# bzip2 and libgconf-2-4 are necessary for extracting firefox and running chrome, respectively
RUN dnf -y install autoconf automake make\
  gcc-c++ libstdc++-static.x86_64

#RUN dnf -y install libX11-devel libXaw-devel libXt-devel

RUN dnf -y install libtool bison flex

RUN dnf -y install git wget curl

RUN dnf clean all


COPY ./run.sh /
RUN chmod +x /run.sh


ENTRYPOINT ["/run.sh"]




