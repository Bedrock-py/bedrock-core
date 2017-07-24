FROM ubuntu:16.04

MAINTAINER "James Fairbanks" <james.fairbanks@gtri.gatech.edu>

# Import MongoDB public GPG key AND create a MongoDB list file
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
RUN echo "deb http://repo.mongodb.org/apt/ubuntu $(cat /etc/lsb-release | grep DISTRIB_CODENAME | cut -d= -f2)/mongodb-org/3.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.4.list

#Install oracle java prerequisites
RUN apt-get update -y                                                                         \
    && apt-get dist-upgrade -y                                                                \
    && apt-get install -y software-properties-common python-software-properties apt-utils     \
    && add-apt-repository ppa:webupd8team/java

# Install oracle java for the LEAN Library not necessarily necessary anymore
RUN apt-get update -qq && apt-get upgrade -qq -y                                    \
    && echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true  \
            | /usr/bin/debconf-set-selections

RUN apt-get update


# Install what we can from with APT
RUN apt-get install -qq -y \
                ant                         \
                apache2                     \
                build-essential             \
                cmake                       \
                curl                        \
                cython                      \
                ed                          \
                gfortran                    \
                git                         \
                jq                          \
                libapache2-mod-wsgi         \
                libcurl4-openssl-dev        \
                libevent-dev                \
                libmysqlclient-dev          \
                libpq-dev                   \
                libssl-dev                  \
                libxml2-dev                 \
                littler                     \
                mongodb-org-server          \
                mongodb-org-mongos          \
                mongodb-org-shell           \
                libnlopt-dev                \
                oracle-java8-installer      \
                oracle-java8-set-default    \
                python-dev                  \
                python-numpy                \
                python-scipy                \
                python-sklearn              \
                python-virtualenv           \
                r-cran-lme4                 \
                ssh                         \
                unzip                       \
                wget                        \
                vim
RUN wget https://bootstrap.pypa.io/get-pip.py && python get-pip.py

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
ADD ./bin/                  /opt/bedrock/bin
RUN ls -lah /opt/bedrock/bin
RUN bash /opt/bedrock/bin/installR.sh

RUN mkdir -p /data/db
RUN mkdir -p /opt/bedrock/conf
RUN mkdir -p /opt/bedrock/bin
RUN mkdir -p /opt/bedrock/package

ADD ./conf/bedrock.conf     /opt/bedrock/conf/bedrock.conf
ADD .                       /opt/bedrock/package
ADD ./conf/mongod.init.d    /etc/init.d/mongod

RUN /opt/bedrock/bin/install.sh

# to test this you can run ./test_docker.sh which will build, run, and test the container.
CMD service mongod start && /usr/sbin/apache2ctl -D FOREGROUND; /usr/sbin/apache2ctl -D FOREGROUND; /usr/sbin/apache2ctl -D FOREGROUND
