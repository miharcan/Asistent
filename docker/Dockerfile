FROM ubuntu:16.04

LABEL MAINTAINER mihael.arcan@insight-centre.org

RUN apt-get update && apt-get install -y vim apache2 build-essential libboost-dev libboost-all-dev cmake git-core libplack-perl libjson-perl libcgi-pm-perl python3-pip wget cron

RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf
COPY 000-default.conf /etc/apache2/sites-available/000-default.conf 

COPY html/ /var/www/
COPY cgi-bin/ /var/www/cgi-bin
COPY data/ /var/www/data

RUN apt-get update && apt-get install -q -y unzip make g++ wget git git-core mercurial bzip2 autotools-dev automake libtool zlib1g-dev libbz2-dev libboost-all-dev libxmlrpc-core-c3-dev libxmlrpc-c++8-dev build-essential pkg-config python-dev cmake libcmph-dev libcmph-tools libcmph0 libgoogle-perftools-dev liblzma-dev
RUN git clone https://github.com/moses-smt/mosesdecoder.git
WORKDIR /mosesdecoder/
RUN mkdir -p /home/tools/mosesdecoder
RUN ./bjam --prefix=/home/tools/mosesdecoder --install-scripts --with-cmph=/usr/include/cmph --with-xmlrpc-c -j2
RUN rm -rf /mosesdecoder/
WORKDIR /


RUN git clone https://github.com/eigenteam/eigen-git-mirror.git /home/tools/eigen/
ENV EIGEN3=/home/tools/eigen/
WORKDIR $EIGEN3
RUN mkdir $EIGEN3/build_dir
WORKDIR $EIGEN3/build_dir
RUN cmake /home/tools/eigen
RUN make install

#
RUN git clone https://github.com/OpenNMT/CTranslate.git /home/tools/CTranslate/
ENV CT=/home/tools/CTranslate/
WORKDIR $CT
RUN git submodule update --init
RUN mkdir -p $CT/build
WORKDIR $CT/build
RUN cmake ..
RUN make
RUN mkdir -p /home/tools/CTranslate/lib/tokenizer/build
WORKDIR $CT/lib/tokenizer/build
RUN cmake -DCMAKE_BUILD_TYPE=Release ..
RUN make

WORKDIR /

## Open port 80
EXPOSE 80
RUN a2enmod cgi
## Start Apache service
CMD service apache2 start && sleep infinity

