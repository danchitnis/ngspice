FROM ubuntu:20.04

RUN apt -y update


RUN apt -y install python3 python3-pip

RUN apt install -y build-essential

# bzip2 and libgconf-2-4 are necessary for extracting firefox and running chrome, respectively
#RUN apt -y install autoconf automake make\
#  gcc-c++ libstdc++-static.x86_64

#RUN dnf -y install libX11-devel libXaw-devel libXt-devel

RUN apt -y install libtool bison flex

RUN apt -y install git wget curl

RUN apt clean all


COPY ./run.sh /
RUN chmod +x /run.sh


ENTRYPOINT ["/run.sh"]





