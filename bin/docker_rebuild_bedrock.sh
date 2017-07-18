#!/bin/bash

# Usage: docker_install_opal.sh $ID $PACKAGE
# $ID 		- ID of the running Bedrock Docker container
# $BEDROCK_ROOT 	- Root directory for Bedrock
# $ID is populated if docker is started with this command from the bedrock-core directory:
#		docker build -t bedrock . && ID=$(docker run -p 81:81 -p 82:82 -d bedrock)

display_usage() {
	echo -e "\tdocker_install_opal.sh is used to install an opal in a running docker container"
	echo -e "\tUsage: docker_install_opal.sh ID PACKAGE"
	echo -e "\t\tID - ID of the running Bedrock Docker container"
	echo -e "\t\tPACKAGE - Name of the package to run. \$PACKAGE.tar.gz should exist in the current directory \n"
	}

# if less than two arguments supplied, display usage
if [ $# -le 1 ]
then
	display_usage
	exit 1
fi

ID=$1
BEDROCK_ROOT=$2

docker exec $ID mkdir -p /opt/bedrock/package/
docker cp $BEDROCK_ROOT/. $ID:/opt/bedrock/package/
docker exec $ID service apache2 reload
