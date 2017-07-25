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
