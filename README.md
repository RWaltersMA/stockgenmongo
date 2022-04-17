# Stock Ticker Generation tool for MongoDB

  

This application will randomly create fictitious company names, stock symbols and sample data and insert them into a MongoDB collection.  This repository contains both the python application and optional docker compose scripts if you choose to run the application within a docker container. 

Sample console output:

```
Generating stock ticker data for the following securities


ABT     ANXIOUS BOUNDARY TECHNOLOGIES
QHV     QUIZZICAL HATRED VENTURES
ZCI     ZANY CREPE INNOVATIONS
LFF     LITTLE FLICK FOODS
FDT     FLUTTERING DISABILITY TECHNOLOGIES


Checking MongoDB Connection
Successfully connected to MongoDB

Start time: 2022-04-17 10:48:37.674838

1 _id=625c28c746b17c01d3f2e58b   ABT ANXIOUS BOUNDARY TECHNOLOGIES traded at 89.34 2022-04-17 10:48:39
2 _id=625c28c746b17c01d3f2e58c   QHV QUIZZICAL HATRED VENTURES traded at 5.4 2022-04-17 10:48:39
3 _id=625c28c746b17c01d3f2e58d   ZCI ZANY CREPE INNOVATIONS traded at 34.62 2022-04-17 10:48:39
4 _id=625c28c746b17c01d3f2e58e   LFF LITTLE FLICK FOODS traded at 90.95 2022-04-17 10:48:39
5 _id=625c28c746b17c01d3f2e58f   FDT FLUTTERING DISABILITY TECHNOLOGIES traded at 92.25 2022-04-17 10:48:39
6 _id=625c28c846b17c01d3f2e590   ABT ANXIOUS BOUNDARY TECHNOLOGIES traded at 89.38 2022-04-17 10:48:40
7 _id=625c28c846b17c01d3f2e591   QHV QUIZZICAL HATRED VENTURES traded at 5.4 2022-04-17 10:48:40
8 _id=625c28c846b17c01d3f2e592   ZCI ZANY CREPE INNOVATIONS traded at 34.64 2022-04-17 10:48:40
9 _id=625c28c846b17c01d3f2e593   LFF LITTLE FLICK FOODS traded at 90.99 2022-04-17 10:48:40
10 _id=625c28c846b17c01d3f2e594   FDT FLUTTERING DISABILITY TECHNOLOGIES traded at 92.32 2022-04-17 10:48:40
11 _id=625c28c946b17c01d3f2e595   ABT ANXIOUS BOUNDARY TECHNOLOGIES traded at 89.41 2022-04-17 10:48:41
12 _id=625c28c946b17c01d3f2e596   QHV QUIZZICAL HATRED VENTURES traded at 5.4 2022-04-17 10:48:41
13 _id=625c28c946b17c01d3f2e597   ZCI ZANY CREPE INNOVATIONS traded at 34.67 2022-04-17 10:48:41
14 _id=625c28c946b17c01d3f2e598   LFF LITTLE FLICK FOODS traded at 91.04 2022-04-17 10:48:41
15 _id=625c28c946b17c01d3f2e599   FDT FLUTTERING DISABILITY TECHNOLOGIES traded at 92.38 2022-04-17 10:48:41


Elapsed time:  0:00:05.195619

```

## Configuration Parameters

This `stockgen.py` application accepts the following parameters:
  

| Command line parameter | Description | Default |
|--|--|--|
|-s | Number of company symbols | 5 |
|-c | MongoDB Connection String | mongodb://127.0.0.1:27017/?directConnection=true' |
|-db | Destination database name | Stocks |
|-col | Destination collection name | StockData |
|-as | Store time as string | |
|-q | Quiet mode, only write summarization | |
|-n | Number of samples to generate (0=infinite) | 0 |
  

The company names are generated from reading three text files, adjectives.txt, nouns.text and endings.txt. You can modify these files to generate more unique names.



### Sample use of the generator 

To create 10 seconds of fictitious data to the local MongoDB cluster:

`python3 stockgen.py -n 10    `

Continuously create sample data every second in perpetuity (until you hit Control-C) for 10 securities writing to a MongoDB Atlas cluster in quiet mode:

`python3 stockgen.py -c "mongodb+srv://<username>:<password>@cluster0.ee68b.mongodb.net/myFirstDatabase?retryWrites=true&w=majority" -s 10 -q`


### Running in a container

Build the image:
`docker build -t stockgenmongo:1.0 . `

Running the container:
`docker run stockgenmongo:1.0 -n 10 -c "mongodb+srv://<username>:<password>@<some atlas cluster>/?retryWrites=true&w=majority" -db MyStocks -col Securities`

Note: If your MongoDB is on another network within Docker you may need to add the `--network`parameter.  In the example above we are accessing MongoDB Atlas which lives in the cloud so no network parameter needed.

Alternatively this tool is available on Docker Hub, simply call it

`docker run robwma/stockgenmongo:1.0 `
