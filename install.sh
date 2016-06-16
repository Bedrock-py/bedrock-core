#!/bin/bash
set -e
DIR=`pwd`
TARGET=/var/www/bedrock

if ! [ -d $DIR ]; then
    echo "FATA: cannot find DIR:$DIR" >&2
    exit 1
fi
echo "Bedrock code found in $DIR"
echo "Bedrock code installing to $TARGET"
# sudo ln -s "$DIR" "$TARGET"
# ls "$TARGET"
echo "Bedrock installed in $TARGET..."

const_link () {
    API=$1
    TPATH="$TARGET/$API/CONSTANTS.py"
    DSTPATH="$TARGET/CONSTANTS.py"
    if ! [ -r "$TPATH" ]; then
        sudo ln -s "$DSTPATH" "$TPATH"
        return $?
    fi
}
const_link dataloader
const_link workflows
const_link analytics
const_link visualization

# ln -s /var/www/opals-sources /var/www/bedrock/
OPAL_TAR="/var/www/opals.tar.gz"
if [ -r $OPAL_TAR ]; then
    echo "Extracting $OPAL_TAR into $(pwd)"
    tar xzf $OPAL_TAR
else
    echo "WARN: Cannot find $OPAL_TAR, opals may not be available."
fi

echo "INFO: setting up apache for bedrock"
sudo ln -s /var/www/bedrock/conf/bedrock.conf /etc/apache2/sites-available/
sudo a2ensite bedrock.conf
# sudo service apache2 reload

echo "INFO: making links for bedrock"
sudo ln -s /var/www/bedrock/opal.sh /usr/local/bin/opal
sudo mkdir /var/www/bedrock/analytics/data
sudo chown www-data /var/www/bedrock/analytics/data
sudo mkdir /var/www/bedrock/dataloader/data
sudo chown www-data /var/www/bedrock/dataloader/data
sudo chown www-data /var/www/bedrock/analytics/opals
