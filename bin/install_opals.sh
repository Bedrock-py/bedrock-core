#!/bin/bash

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
