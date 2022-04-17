# Stock Ticker Generation tool for MongoDB

This application will randomly create ficticuous company names, stock symbols and sample data.  These data will be perpetually insert data into MongoDB.  

To start generating data into the local MongoDB cluster that is created with the Kafka tutorial, launch the following commmand:

```
docker run stockgenmongo:0.1
```

Note that if you are running MongoDB within another Docker Network be sure to add the --network parameter.  By default the tool will create 5 securities and connect to the following URL: mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0.  See parameters below to change these default settings.



## Configuraiton Parameters
The Docker container launches a python application called, "stockgen.py".  This application accepts the following parameters:

| Command line parameter | Description  | Default |
|--|--|--|
|-s  | Number of company symbols  | 5 |
|-c  | MongoDB Connection String  | mongodb://mongo1:27017,mongo2:27018,mongo3:27019/?replicaSet=rs0 |

The company names are generated from reading three text files, adjectives.txt, nouns.text and endings.txt.  You can modify these files to generate more unique names.
