#!/bin/bash

echo "INFO: setting up apache for bedrock"
ln -s "/opt/bedrock/conf/bedrock.conf" /etc/apache2/sites-available/
# ls $TARGET
a2ensite bedrock
# sudo service apache2 reload

# Make directories for data (TODO: Shift this and the constants to be a HDFS store)
mkdir -p /opt/bedrock/dataloader/data
mkdir -p /opt/bedrock/analytics/data

chown -R www-data:www-data /opt/bedrock/package/src
chown -R www-data:www-data /opt/bedrock/dataloader/data
chown -R www-data:www-data /opt/bedrock/analytics/data

#pip install git+ssh://git@github.gatech.edu/Bedrock/bedrock-core@pip#egg=bedrock

# Sleep is necessary to ensure the mongod init.d file is not busy when attempting to access
chmod 755 /etc/init.d/mongod
sleep 1
service mongod start

# pip install git+ssh://git@github.gatech.edu/Bedrock/bedrock-core@pip#egg=bedrock
pip install -e /opt/bedrock/package
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-dataloader-ingest-spreadsheet@pip#egg=opals-spreadsheet
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-analytics-clustering@pip#egg=opals-clustering
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-analytics-classification@master#egg=opals-classification
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-analytics-dimensionreduction@master#egg=opals-dimred
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-dataloader-filter-truth@master#egg=opals-truth
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-visualization-roc@master#egg=opals-roc
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-visualization-linechart@master#egg=opals-linechart
pip install git+ssh://git@github.gatech.edu/Bedrock/opal-visualization-scatterplot@master#egg=opals-scatterplot

# pip install git+ssh://git@github.gatech.edu/Bedrock/opal-visualization-barchart@master#egg=opals-barchart

pip install -e git+ssh://git@github.gatech.edu/Bedrock/opal-analytics-logit2@master#egg=opals-logit2
# pip install -e /opt/bedrock/package/opal-analytics-logit2

echo 'local({
  r <- getOption("repos")
  r["CRAN"] <- "http://cran.cnr.berkeley.edu/"
  options(repos = r)
})' >> /etc/R/Rprofile.site
chmod -R 777 /usr/local/lib/R/site-library
R -e 'install.packages(c("multiwayvcov","lmtest"))'
