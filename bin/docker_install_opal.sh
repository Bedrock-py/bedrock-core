#!/bin/bash 
 
# Usage: docker_install_opal.sh $ID $PACKAGE
# $ID 		- ID of the running Bedrock Docker container
# $PACKAGE 	- Name of the installation package
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
PACKAGE=$2

docker cp $PACKAGE.tar.gz $ID:/opt/bedrock/package/
docker exec $ID tar -zxf /opt/bedrock/package/$PACKAGE.tar.gz -C /opt/bedrock/package
docker exec $ID pip install -e /opt/bedrock/package/$PACKAGE
docker exec $ID service apache2 reload

