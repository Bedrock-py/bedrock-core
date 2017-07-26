FROM bedrockgtri/bedrockserver:latest

MAINTAINER "James Fairbanks" <james.fairbanks@gtri.gatech.edu>

ADD .                       /opt/bedrock/package
ADD bin/install_opals.sh    /opt/bedrock/bin/install_opals.sh

RUN service mongod start && /opt/bedrock/bin/install_opals.sh

# to test this you can run ./test_docker.sh which will build, run, and test the container.
CMD service mongod start && /usr/sbin/apache2ctl -D FOREGROUND; /usr/sbin/apache2ctl -D FOREGROUND; /usr/sbin/apache2ctl -D FOREGROUND
