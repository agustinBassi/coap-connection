FROM debian:latest

RUN apt-get update -y && \
  apt-get install -y python3 python3-pip git autoconf automake libtool && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* build/

RUN mkdir -p /usr/src/app /usr/src/build
WORKDIR /usr/src/build

RUN python3 -m pip install --upgrade pip setuptools wheel cython

RUN git clone --depth 1 --recursive -b dtls https://github.com/home-assistant/libcoap.git && \
    cd libcoap && \
    ./autogen.sh && \
    ./configure --disable-documentation --disable-shared --without-debug CFLAGS="-D COAP_DEBUG_FD=stderr" && \
    make && \
    make install

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

WORKDIR /usr/src/app
ENV LANG=C.UTF-8
CMD /bin/bash