#!/bin/bash

echo "INFO: setting up apache for bedrock"
ln -s "/opt/bedrock/conf/bedrock.conf" /etc/apache2/sites-available/
echo "INFO: moving static files into /var/www/html"
cp /opt/bedrock/package/static/* /var/www/html/
# ls $TARGET
a2ensite bedrock
# sudo service apache2 reload

# Make directories for data (TODO: Shift this and the constants to be a HDFS store)
mkdir -p /opt/bedrock/dataloader/data
mkdir -p /opt/bedrock/analytics/data

chown -R www-data:www-data /opt/bedrock/package/src
chown -R www-data:www-data /opt/bedrock/dataloader/data
chown -R www-data:www-data /opt/bedrock/analytics/data

# Sleep is necessary to ensure the mongod init.d file is not busy when attempting to access
chmod 755 /etc/init.d/mongod
sleep 1
service mongod start

# pip install git+https://github.com/Bedrock-py/bedrock-core.git@master#egg=bedrock

# Install bedrock core and default opals
pip install -e /opt/bedrock/package
pip install git+https://github.com/Bedrock-py/opal-analytics-clustering.git@master#egg=opals-clustering
pip install git+https://github.com/Bedrock-py/opal-analytics-classification.git@master#egg=opals-classification
pip install git+https://github.com/Bedrock-py/opal-analytics-dimensionreduction.git@master#egg=opals-dimred
pip install git+https://github.com/Bedrock-py/opal-analytics-select-from-dataframe.git@master#egg=opal-analytics-select-from-dataframe

pip install git+https://github.com/Bedrock-py/opal-dataloader-ingest-spreadsheet.git@master#egg=opals-spreadsheet
pip install git+https://github.com/Bedrock-py/opal-dataloader-filter-truth.git@master#egg=opals-truth

pip install git+https://github.com/Bedrock-py/opal-visualization-roc.git@master#egg=opals-roc
pip install git+https://github.com/Bedrock-py/opal-visualization-linechart.git@master#egg=opals-linechart
pip install git+https://github.com/Bedrock-py/opal-visualization-scatterplot.git@master#egg=opals-scatterplot

