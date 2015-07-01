#!/bin/bash

DIR=`pwd`
TARGET=/var/www/bedrock

sudo ln -s $DIR $TARGET
echo "Bedrock installed in $TARGET..."

sudo ln -s $TARGET/CONSTANTS.py $TARGET/dataloader/CONSTANTS.py
sudo ln -s $TARGET/CONSTANTS.py $TARGET/workflows/CONSTANTS.py
sudo ln -s $TARGET/CONSTANTS.py $TARGET/analytics/CONSTANTS.py
sudo ln -s $TARGET/CONSTANTS.py $TARGET/visualization/CONSTANTS.py

sudo ln -s /var/www/bedrock/conf/bedrock.conf /etc/apache2/sites-available/
sudo a2ensite bedrock.conf
sudo service apache2 reload

sudo ln -s /var/www/bedrock/opal.sh /usr/local/bin/opal
sudo mkdir /var/www/bedrock/analytics/data
sudo chown www-data /var/www/bedrock/analytics/data
sudo mkdir /var/www/bedrock/dataloader/data
sudo chown www-data /var/www/bedrock/dataloader/data
sudo chown www-data /var/www/bedrock/analytics/opals
