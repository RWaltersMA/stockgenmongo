# Stock Ticker Generation tool


This application will randomly create fictitious company names, stock symbols and sample data and insert them into a MongoDB collection or an Apache Kafka Topic.  This repository contains both the python application and optional docker compose scripts if you choose to run the application within a docker container. 

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

## Configuration File

This `stockgen.py` uses a configuration file called 'config.ini'.  You can create a template of this file by issuing the following:

`stockgen.py -createconfig`

Modify the output file config.ini as needed.  The following is the output of the config.ini:
```
[SETUP]
type = MONGODB
symbols = 5
duration = 0
include_exchange = True
threads = 1
time_as = STRING

[KAFKA]
bootstrap_servers = localhost:9092
client_id = stockgenclient
security_protocol = SASL_SSL
sasl_mechanism = PLAIN
sasl_plain_username = 
sasl_plain_password = 
topic = Stocks
partitions = 6
serialize = JSON
schema_registry_url = neededforAVRO
schema_registry_username = neededforAVRO
schema_registry_password = neededforAVRO

[MONGODB]
connection = mongodb://127.0.0.1
database = StockData
collection = Stocks
```

The stockgen application can write to either MongoDB or Kafka.  Most of the parameters are self-explanatory.  Here are a few key points:

```
[SETUP]
type = MONGODB | KAFKA

When set you can ignore the other configuration values.  e.g. if you set KAFKA you can ignore anything in [MONGODB]


symbols = 5 | any valid integer above 0

This is how many securities will be created each second


include_exchange = True | False    

This parameters randomly adds "exchange":"NASDAQ" or "exchange":"NYSE"


time_as = STRING | EPOCH 

This parameter will write the value of the date as a string or an epoch time


[KAFKA]
serialize=JSON | AVRO 

AVRO is new to this tool, working out bugs.  You need to provide schema_registry_url,schema_registry_username and schema_registry_password if using Confluent

```

This application was tested with SASL_SSL, PLAIN if you use a different one and it doesn't work.  Please consider filing a PR to help others.


## Command line parameters 

Stockgen application accepts the following parameters:
  

| Command line parameter | Description | Default |
|--|--|--|
|-createconfig | Creates a configuration template file | |
|-config | Configuration file name | config.ini |
|-drop | Connects to Kafka or MongoDB and drops the topic or collection specified in the config file | |
|-ts | MongoDB: Creates the collection as timeseries |  |
|-col | Destination collection name | StockData |
|-sa | Stop after X minutes.  Default 0 which is never | 0 |
|-e | Add ranom errors to stream | |

The company names are generated from reading three text files, adjectives.txt, nouns.text and endings.txt. You can modify these files to generate more unique names.



### Sample use of the generator writing to MongoDB

**Continually write fictitious data to the local MongoDB cluster:**

```
[SETUP]
type = MONGODB
symbols = 5
duration = 0
include_exchange = True
threads =1
time_as=DATE

[MONGODB]
connection=mongodb+srv://<username>:<password>@stockcluster.asdfasdf.mongodb.net/?retryWrites=true&w=majority
database = StockData
collection = Stocks
```

**Continually write to KAFKA topic** 

```
[SETUP]
type = KAFKA
symbols = 5
duration = 0
include_exchange = True
threads =1
time_as=DATE

[KAFKA]
bootstrap_servers = sxxxxk.us-east-1.aws.confluent.cloud:9092
client_id = stockgenclient
security_protocol = SASL_SSL
sasl_mechanism = PLAIN
sasl_plain_username = ZZZZZEYHK2HZPAHJ
sasl_plain_password = KlKinxV24vsdfjasdjkfazxcvzxcvzxcvzxcvzcxvzxcv1/ELjn8nafW
topic = Stocks
partitions =1
serialize = JSON

```

Sample data output in Kafka Topic
```
{
  "exchange": "NASDAQ",
  "company_symbol": "QCF",
  "company_name": "QUAINT COLLATERAL FOODS",
  "price": 75.3,
  "tx_time": "2024-01-25T08:59:40Z"
}
```

### Example Usage

To start the generator
`python3 stockgen.py -config config.ini`

(Note you might need to install the pre-reqs `pip3 install -r requirements.txt` before first time use )

Use control-C to stop the data generation

To drop the topic or collection use --drop

`python3 stockgen.py -config config.ini --drop`


### Running on a Mac
if on mac you might need to create a virtual environment then install the libraries as follows:

`python3 -m venv my_env`
`source my_env/bin/activate` 

then
`pip3 install -r requirements.txt`