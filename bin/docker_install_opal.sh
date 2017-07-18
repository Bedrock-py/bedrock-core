#!/bin/bash

# Usage: docker_install_opal.sh $ID $PACKAGE
# $ID 		- ID of the running Bedrock Docker container
# $PACKAGE 	- Name of the installation package
# $ID is populated if docker is started with this command from the bedrock-core directory:
#		docker build -t bedrock . && ID=$(docker run -p 81:81 -p 82:82 -d bedrock)

display_usage() {
	echo -e "\tdocker_install_opal.sh is used to install an opal in a running docker container"
	echo -e "\tUsage: docker_install_opal.sh ID LOCAL_PACKAGE\n\tOR\n\tdocker_install_opal.sh -g GIT_URL ID"
	echo -e "\t\tID - ID of the running Bedrock Docker container"
	echo -e "\t\tPACKAGE - Name of the package to run. \$PACKAGE.tar.gz or PACKAGE/ should exist in the current directory \n"
	echo -e "\t\GIT_URL - URL to the git repo hosting the Opal (https only)\n"
	}

# if less than two arguments supplied, display usage
if [ $# -le 1 ]
then
	display_usage
	exit 1
fi

GIT_URL=''

while getopts 'g:' flag; do
  case "${flag}" in
    g) GIT_URL="git+${OPTARG}" ;;
  esac
done

ID=${@:$OPTIND:1}
PACKAGE=${@:$OPTIND+1:1}

docker exec $ID mkdir -p /opt/bedrock/opals/
if [[ ! -z $GIT_URL ]]; then
  docker exec $ID pip install $GIT_URL
  docker exec $ID service apache2 reload
  exit 0
elif [ -e $PACKAGE.tar.gz ]; then
  docker cp $PACKAGE.tar.gz $ID:/opt/bedrock/opals/
  docker exec $ID tar -zxf /opt/bedrock/opals/$PACKAGE.tar.gz -C /opt/bedrock/opals
elif [ -d $PACKAGE ]; then
  docker cp $PACKAGE $ID:/opt/bedrock/opals/
else
  echo "$PACKAGE does not exist as $PACKAGE.tar.gz or directory"
  exit -1
fi
docker exec $ID pip install -e /opt/bedrock/opals/$PACKAGE
docker exec $ID service apache2 reload
