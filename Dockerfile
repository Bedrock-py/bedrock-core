FROM ubuntu:14.04

MAINTAINER "James Fairbanks" <james.fairbanks@gtri.gatech.edu>

#Install oracle java prerequisites
RUN apt-get update -y                                                               \
    && apt-get install -y software-properties-common python-software-properties     \
    && add-apt-repository ppa:webupd8team/java

# Install oracle java for the LEAN Library not necessarily necessary anymore
RUN apt-get update -qq && apt-get upgrade -qq -y                                    \
    && echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true  \
            | /usr/bin/debconf-set-selections

# Install what we can from with APT
RUN apt-get install -qq -y \
                ant                         \
                apache2                     \
                cmake                       \
                curl                        \
                cython                      \
                gfortran                    \
                git                         \
                jq                          \
                libapache2-mod-wsgi         \
                libevent-dev                \
                mongodb-server              \
                oracle-java8-installer      \
                oracle-java8-set-default    \
                python-dev                  \
                python-numpy                \
                python-scipy                \
                python-virtualenv           \
                ssh                         \
                unzip                       \
                wget                        \
                vim

# Binaries built with checkmake of bedrock libraries.
RUN wget --quiet http://130.207.211.77/packages/libelemental_0.84-p1-1_amd64.deb &&   \
    wget --quiet http://130.207.211.77/packages/libflame_5.0-4648_amd64.deb    && \
    wget --quiet http://130.207.211.77/packages/libopenblas_0.2.9-1_amd64.deb  && \
    wget --quiet http://130.207.211.77/packages/libsmallk_20150909-1_amd64.deb && \
    wget --quiet http://130.207.211.77/packages/openmpi_1.8.1-1_amd64.deb      && \
    wget --quiet http://130.207.211.77/packages/pysmallk_20150909-1_amd64.deb

RUN dpkg -i ./libelemental_0.84-p1-1_amd64.deb \
            ./libflame_5.0-4648_amd64.deb      \
            ./libopenblas_0.2.9-1_amd64.deb    \
            ./libsmallk_20150909-1_amd64.deb   \
            ./openmpi_1.8.1-1_amd64.deb        \
            ./pysmallk_20150909-1_amd64.deb


# Copy over and install the python requirements
COPY ./requirements.txt /var/www/bedrock-requirements.txt

RUN pip install -U pip && hash -r && pip install -r /var/www/bedrock-requirements.txt

RUN cd /var/www && curl --silent http://10.50.76.157/packages/opals.tar.gz | tar xz
# ADD http://127.0.0.1:8000/opals.tar.gz /root/bedrock/opals-sources

# RUN mv /opals-sources /root/bedrock/opals-sources

# TODO We should run the opal_setup.sh script or ./setup.py
# in the Dockerfile, but it needs a running mongo instance to work.
# thus we run this with docker exec sh -c "cd /var/www/bedrock && ./setup.py"
# RUN cd /var/www/bedrock && ./bin/setup.py

# standard apache
EXPOSE 80
# bedrock
EXPOSE 81
# mongo
EXPOSE 27017
# mongo admin web
EXPOSE 28017
# CMD ["python", "-c ", "import scipy; print('hello from scipy')"]

# we need to start mongo and wait for it to get up and running before we can run the opal install script.
# the right thing is probably to have setup.py check if mongo is running, if not start it
# and wait for it to accept connections, then install the opals.
# this second apache2ctl command is because we need to "service apache2 reset" once.
# it is definitely a hack that should be removed (added 6/10/2016)
# we should either decompose this service or use http://phusion.github.io/baseimage-docker/#solution
# as the base image, in order run multiple processes in a single container.
RUN mkdir -p /data/db
ADD ./ /var/www/bedrock
RUN cd /var/www/bedrock/ && /var/www/bedrock/bin/install.sh

CMD  service mongodb start  &&  /usr/sbin/apache2ctl -D FOREGROUND; /usr/sbin/apache2ctl -D FOREGROUND

# to test this you can run ./test_docker.sh which will build, run, and test the container.
