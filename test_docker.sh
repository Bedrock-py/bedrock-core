#!/usr/bin/env bash
# Run the necessary docker commands to prepare the container
# for bedrock to run.
# then restart the container with bedrock running.
# then run the client side tests test.py
# if you can get data back through the client, then everything is good.
# possible failure points are:
# ## getting setup.py running inside the container.
#    - can fail to run mongo inside first
# ## getting container restarted
#    - make sure that mongo and apache are running when you restart the container.
#    - make sure the ports are mapped correctly. If another instance is hogging port 81 you need to change test.py

# BEGIN SETUP PHASE that should run in the dockerfile but doesn't
docker build -t bedrock .
# assuming the source code was added in the docker file
ID=$(docker run -p 81:81 -p 82:82 -d  bedrock)
# for debugging you can mount the source code in the docker container and changes will be reflected live.
# you need to remove the ADD ./ /var/www/bedrock line from the Dockerfile in order to make this work.
# ID=$(docker run -p 81:81 -p 82:82 -d -v $(pwd):/var/www/bedrock bedrock)
echo "docker container ID:$ID is running"
# TODO find a better way to wait for mongo to start.
sleep 5
docker exec $ID sh -c 'cd /var/www/bedrock && ./setup.py'
# END SETUP PHASE

echo "ran setup.py"
docker ps
docker start $ID
echo "restarted the docker $ID"
echo "current running containers are:"
docker ps
echo "processes running on $ID are:"
docker top $ID
# BEGIN TESTING PHASE which runs on the client
echo "running clientside tests ./test.py:"
python test.py --port 81
# END TESTING PHASE

# BEGIN CLEANUP PHASE
# optional cleanup routine
# docker rm -f $ID
# END CLEANUP PHASE
