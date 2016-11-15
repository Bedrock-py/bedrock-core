#!/bin/bash
set -e
DIR=`pwd`
TARGET=/var/www/bedrock
mkdir -p "$TARGET"
export PATH="$(pwd)/bin/:$PATH"

if ! [ -d $DIR ]; then
    echo "FATA: cannot find DIR:$DIR" >&2
    exit 1
fi
echo "Bedrock code found in $DIR"
echo "Bedrock code installing to $TARGET"
# ln -s "$DIR/src/src" "$TARGET"
# ls "$TARGET"
echo "Bedrock installed in $TARGET..."

const_link () {
    API=$1
    TPATH="$TARGET/src/$API/CONSTANTS.py"
    DSTPATH="$TARGET/src/CONSTANTS.py"
    if ! [ -r "$TPATH" ]; then
        # ln -s "$DSTPATH" "$TPATH"
        return $?
    fi
}

const_link dataloader
const_link workflows
const_link analytics
const_link visualization

OPALPATH=/var/www/opal-sources

# echo "INFO: linking opals"
# ln -s "$OPALPATH" "$TARGET"

if [ ! -d $OPALPATH ]; then
    mkdir -p $OPALPATH
fi


OPAL_TAR="/var/www/opals.tar.gz"
if [ -r $OPAL_TAR ]; then
    echo "Extracting $OPAL_TAR into $(pwd)"
    tar xzf $OPAL_TAR
else
    echo "WARN: Cannot find $OPAL_TAR, opals may not be available."
fi

echo "INFO: setting up apache for bedrock"
ln -s "$TARGET/conf/bedrock.conf" /etc/apache2/sites-available/
# ls $TARGET
a2ensite bedrock.conf
# sudo service apache2 reload

echo "INFO: making links for bedrock"
OPALBIN=/usr/local/bin/opal
ln -s /var/www/bedrock/bin/opal.sh "$OPALBIN"
if [ ! -r "$OPALBIN" ]; then
    echo "WARN: failed to install opal.sh to $OPALBIN"
fi

mkdir -p /var/www/bedrock/src/{analytics,dataloader,visualization}/opals
mkdir -p /var/www/bedrock/src/{analytics,dataloader,visualization}/data
chown www-data /var/www/bedrock/src/{analytics,dataloader,visualization}/opals
chown www-data /var/www/bedrock/src/{analytics,dataloader,visualization}/data
touch /var/www/bedrock/src/{analytics,dataloader,visualization}/opals/__init__.py

