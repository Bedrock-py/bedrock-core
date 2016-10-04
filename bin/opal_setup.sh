#!/usr/bin/env bash

# service start mongodb
# service start apache2

BEDROCK_DIR="/root/bedrock"
cd $BEDROCK_DIR
opal install application applications/default.json
