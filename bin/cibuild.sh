#!/usr/bin/bash
set -e
echo "INFO: ls $(pwd)"
ls .
echo "INFO: ls pwd/src"
ls src
# echo "INFO: downloading smallk"
# if [ ! -r libsmallk_20150909-1_amd64.deb ]; then
#     wget --quiet http://130.207.211.77/packages/libsmallk_20150909-1_amd64.deb
# fi

# if [ ! -r pysmallk_20150909-1_amd64.deb ]; then
#     wget --quiet http://130.207.211.77/packages/pysmallk_20150909-1_amd64.deb
# fi

# echo "INFO: installing smallk"
# dpkg -i libsmallk_20150909-1_amd64.deb pysmallk_20150909-1_amd64.deb

pip install -q -r requirements.txt
export PATH="$(pwd)/bin:$PATH"
export PYTHONPATH="$(pwd):$PYTHON_PATH"
python -c "import sys; print('PYTHONPATH: ' + str(sys.path))"
python -c "import src.analytics; import src.client; import src.dataloader; import src.visualization"
echo "INFO: can import bedrock src"

if [ ! -r opals.tar.gz ]; then
    echo "INFO: Downloading opals"
    pushd /var/www && curl --silent http://130.207.211.77/packages/opals.tar.gz | tar xz
    echo "INFO: downloaded opals into /var/www/opal-sources"
    ls /var/www/opal-sources
    popd
else
    echo "INFO: opals already downloaded make sure they are installed too."
fi

echo "INFO: Installing with ./bin/install.sh"
./bin/install.sh
echo "INFO: running setup.py with "
python ./bin/setup.py
echo "running tests"
curl localhost:81 > /dev/null
python CONSTANTS.py
pytest
