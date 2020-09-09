FROM fedora:latest

RUN dnf -y update

RUN dnf -y groupinstall xfce

RUN bash -c 'echo PREFERRED=/usr/bin/xfce4-session > /etc/sysconfig/desktop'

RUN dnf install -y xrdp xorgxrdp

RUN dnf -y install sudo nload passwd nano gedit

#### END of GUI

RUN dnf -y install python3 python3-pip



# bzip2 and libgconf-2-4 are necessary for extracting firefox and running chrome, respectively
RUN dnf -y install autoconf automake make\
  gcc-c++ libstdc++-static.x86_64

RUN dnf -y install libX11-devel libXaw-devel libXt-devel

RUN dnf -y install libtool bison

#RUN dnf -y install autoremove


## ADD user
RUN useradd foo
RUN usermod -aG wheel foo

## Emscripten
## https://emscripten.org/docs/getting_started/downloads.html
RUN dnf -y install git wget curl

#USER foo

#RUN mkdir ~/emsdk && cd ~ && git clone https://github.com/emscripten-core/emsdk.git
#RUN cd ~/emsdk && ./emsdk install latest


#USER foo

COPY ./Docker/compile.sh /home/foo/compile.sh
#RUN rm -rf ~/.cache/pip

#USER root
#RUN chmod +x /home/foo/spice3f5/build/*.sh
#RUN pip3 install matplotlib

#### END of dev

#USER root

RUN dnf clean all

COPY ./Docker/xrdp.ini /etc/xrdp/

COPY ./Docker/fedora-sesman.ini /etc/xrdp/
RUN mv /etc/xrdp/fedora-sesman.ini /etc/xrdp/sesman.ini

COPY ./Docker/startwm-xfce.sh /etc/xrdp/
RUN mv /etc/xrdp/startwm-xfce.sh /etc/xrdp/startwm.sh

RUN chmod a+x /etc/xrdp/startwm.sh

COPY ./Docker/run.sh /
RUN chmod +x /run.sh

EXPOSE 3389

ENTRYPOINT ["/run.sh"]




