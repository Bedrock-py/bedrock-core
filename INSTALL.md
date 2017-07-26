# Installation of Bedrock Server

Bedrock Server can be run either on [Docker](https://www.docker.com/community-edition) or on bare metal.
In this guide we show how to install Bedrock Server using Docker

## Step 1: Install Docker

[Docker can be installed](https://www.docker.com/community-edition#/download) on Windows, Linux, and Mac. 
In this guide we focus on Ubuntu Linux.

### Update software repositories and add the Docker key
```
sudo apt-get update
sudo apt-get install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
```

Verify that the output of the last command contains `9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88`

## Step 2: Clone this repository
Clone https://github.com/bedrock-py/bedrock-core/ to a local working directory. We will then build the Docker image out of this directory.

```
git clone https://github.com/Bedrock-py/bedrock-core.git
```

## Step 3: Build Bedrock Docker Image
From the working directory, build the image. This may take up to 30 minutes and use 8G of RAM.
```
cd bedrock-core
docker build -t bedrock .
```

## Step 4: Run the Docker Image
```
docker run -p 81:81 -d bedrock
```

## Step 5: Test your Installation
Assuming no errors, you should be able to view the APIs at http://localhost:81/ . The automated Python tests can be run from the `bedrock-core` directory by simply executing `pytest`.


## Step 6: Install Additional Analytics Packages

The default installation includes only a select few packages. We'll install two more with the following commands:

```
./bin/docker_install_opal.sh -g https://github.com/Bedrock-py/opal-analytics-logit2.git $ID
./bin/docker_install_opal.sh -g https://github.com/Bedrock-py/opal-analytics-summarize.git $ID
```
