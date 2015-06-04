#!/bin/bash

DIR=`pwd`
TARGET=/var/www/bedrock

sudo ln -s $DIR $TARGET
echo "Bedrock installed in $TARGET..."

