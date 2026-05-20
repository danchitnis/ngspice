FROM ubuntu:24.04

RUN apt -y update && \
    apt -y install python3 python3-pip build-essential libtool bison flex git wget curl && \
    apt clean all


COPY ./run.sh /
RUN chmod +x /run.sh


ENTRYPOINT ["/run.sh"]





