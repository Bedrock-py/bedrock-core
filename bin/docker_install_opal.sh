# Usage: install_in_docker.sh $ID $PACKAGE
# $ID 		- ID of the running Bedrock Docker container
# $PACKAGE 	- Name of the installation package
# $ID is populated if docker is started with this command from the bedrock-core directory:
#		docker build -t bedrock . && ID=$(docker run -p 81:81 -p 82:82 -d bedrock)

ID=$1
PACKAGE=$2

docker cp $PACKAGE.tar.gz $ID:/opt/bedrock/package/
docker exec $ID tar -zxf /opt/bedrock/package/$PACKAGE.tar.gz -C /opt/bedrock/package
docker exec $ID pip install -e /opt/bedrock/package/$PACKAGE
docker exec $ID service apache2 reload

