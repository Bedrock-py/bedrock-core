bedrock-core
============

THIS NOTICE APPLIES TO ALL FILES CONTAINED WITHIN THIS REPOSITORY

Copyright (c) 2015, Georgia Tech Research Institute All rights reserved.

This unpublished material is the property of the Georgia Tech Research Institute and is protected under copyright law. The methods and techniques described herein are considered trade secrets and/or confidential. Reproduction or distribution, in whole or in part, is forbidden except by the express written permission of the Georgia Tech Research Institute.

###Documentation available [here](https://github.gatech.edu/pages/Bedrock/bedrock-core).


## Getting started

For development of bedrock-core one can use a conda environment named bedrock
which is described in the `environment.yml` file in the root of the project
directory. To load the environment use `conda env create evironment.yml`. then
`source activate bedrock` this will install all the dependencies into a virtual
environment managed by conda. We use conda instead of virtualenv because of the
dependencies on the pydata stack which is easier to use with anaconda. if you
want to install everything by hand you can read this `environment.yml` to see
what is required. After updating a dependency of the project using pip, you can
modify the `requirements.txt` file and run `conda env export > environment.yml`
to reflect the changes in the conda environment.

### Running in docker

The file test_docker.sh is a script that uses docker to build a working
installation of the bedrock server and runs the unit tests. See this script for
the up to date run commands. The run commands will look something like below.
You need to run and then exec because we need mongo to be running in the
container in order to finish the installation of the opals. Ideally we could
remove this step by installing a preconfigured mongo into the server or removing
the dependency of the opals on a running mongo. As for now you need to run the
container which starts the server and then exec into it the opal install script.

```sh
docker build -t bedrock .
ID=$(docker run -p 81:81 -p 82:82 -d  bedrock)
docker exec $ID sh -c 'cd /var/www/bedrock && ./bin/setup.py'
```

### Running without docker
If you would like to run this without docker, see the Dockerfile for the
required software on your server and then run the scripts by hand. You should
need 

- bin/install.sh
- bin/setup.py

As this procedure will change over time, consult the Dockerfile for steps that
work.

### Code organization

The codebase is organized so that there is a common module of code in source
with tests and scripts in ./test ./bin respectively. Each flask app is a top
level wsgi app in the src directory, with common code in src/core.

```
.
|-- Dockerfile
|-- bin
|-- conf
|-- docs
|-- src
|   |-- CONSTANTS.py
|   |-- analytics
|   |-- core
|   |-- dataloader
|   |-- memo
|   |-- user
|   |-- visualization
|   `-- workflows
|-- test
|-- validation
`-- var
```

## Api Documentation

See Swagger.js docs for detailed documentation about the web api.

Bedrock uses a flask restful web api to allow frontend developers to access
machine learning and data analytics codes on remote machines and include these
algorithms in their end user applications. As such all apis use json to
communicate and are organized into three large categories. 

The bedrock services is composed of both a bedrock-core server and a collection
of packages/modules/libraries called opals. The opals implement the data loading
(ETL), analytics (ML/statistics), and the visualizations. A developer of a new
technique in one of these categories will write an opal to implement it and then
the bedrock server will manage the data, permissions, and scheduling for these
implementations. The bedrock-core will provide python libraries for allowing an
opal to ignore the backend data storage mechanism as well as the job scheduling
mechanism. In fact data may live in multiple backend stores and compute can
happen on multiple job schedulers without the opal having explicit knowledge of
this fact.

The contract for an opal is that data will come in the form of a DataFrame (from
either pandas or SparkSQL) and outputs will be represented in either a DataFrame
or a json document. The json documents will go into some NoSQL storage system
and DataFrames will go into either a NoSQL document store or a relational
database management system RDBMS.

The analytics opals consume DataFrames and produce outputs, the visualization
opals consume dataframes and return visualizations that can be shown in the web
browser.


