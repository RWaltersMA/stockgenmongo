import datetime
#from io import BytesIO
from os import error
import random
from random import randint
import argparse
#import jsonschema
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import timedelta, datetime as dt
from kafka.admin import KafkaAdminClient, NewTopic
import configparser
import json
import os
from confluent_kafka import Producer as KafkaProducer
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry import Schema

from typing import List
import decimal
import threading
import sys
import time
#from fastavro import * # schema, datafile, io
#from fastavro.schema import load_schema
#from fastavro.validation import validate

from io import BytesIO


volatility = 1  # .001
lock = threading.Lock()
total_events=0

#arrays used to store ficticous securities
company_symbol=[]
company_name=[]
company_exchange=[]

#kafka_config={ 'bootstrap_servers':"pkc-n00kk.us-east-1.aws.confluent.cloud:9092", 'client_id':'stockgenclient','security_protocol':'SASL_SSL','sasl_mechanism':'PLAIN','sasl_plain_username':'ZCA4BEYHK2HZPAHJ','sasl_plain_password':'KlKinxV24vcGRb00/Hk4McnWJhUVCwquzn19sk4QJXcj4TeHzapj+1/ELjn8nafW'}
#defaults
config = configparser.ConfigParser()

#the following two functions are used to come up with some fake stock securities
def generate_symbol(a,n,e):
    for x in range(1,len(a)):
        symbol=str(a[:x]+n[:1]+e[:1])
        if symbol not in company_symbol:
            return symbol

def generate_securities(numberofsecurities):
    cn=[]
    cs=[]
    ce=[]
    with open('adjectives.txt', 'r') as f:
        adj = f.read().splitlines()
    with open('nouns.txt', 'r') as f:
        noun = f.read().splitlines()
    with open('endings.txt', 'r') as f:
        endings = f.read().splitlines()
    for i in range(0,numberofsecurities,1):
        a=adj[randint(0,len(adj)-1)].upper()
        n=noun[randint(0,len(noun))].upper()
        e=endings[randint(0,len(endings)-1)].upper()
        cn.append(a + ' ' + n + ' ' + e)
        cs.append(generate_symbol(a,n,e))
        if config['SETUP']['include_exchange']=='True':
            if random.choice([True, False])==True:
                ce.append("NYSE")
            else:
                ce.append("NASDAQ")
    return cn,cs,ce
#this function is used to randomly increase/decrease the value of the stock, tweak the random.uniform line for more dramatic changes
def getvalue(old_value):
    change_percent = volatility * \
        random.uniform(0.0, .001)  # 001 - flat .01 more
    change_amount = old_value * change_percent
    if bool(random.getrandbits(1)):
        new_value = old_value + change_amount
    else:
        new_value = old_value - change_amount
    return round(new_value, 2)

def checkmongodbconnection():
    try:
        print('\nAttempting to connect to %s \n\n' % config['MONGODB']['connection'] )
        c=MongoClient(host=config['MONGODB']['connection'], server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
        c.admin.command('ismaster')
        time.sleep(2)
        c.close()
        return True
    except:
        print('\nCould not connect to MongoDB.\n\n')
        return False

def checkkafkaconnection():
    try:

        admin_client = KafkaAdminClient(bootstrap_servers=config['KAFKA']['bootstrap_servers'],
                                       client_id=config['KAFKA']['client_id'],
                                       security_protocol=config['KAFKA']['security_protocol'],
                                       api_version=(0, 10),
                                       sasl_mechanism=config['KAFKA']['sasl_mechanism'],
                                       sasl_plain_username=config['KAFKA']['sasl_plain_username'],
                                       sasl_plain_password=config['KAFKA']['sasl_plain_password'])
        topic_list = []
        topic_list=admin_client.list_topics()
        for x in topic_list:
            if x==config['KAFKA']['topic']:
                print('Topic exists, skipping creation\n')
                return
        
        print('\nAttempting to create topic %s \n\n' % config['KAFKA']['topic'])
        topic_list = []
        topic_list.append(NewTopic(name=config['KAFKA']['topic'], num_partitions=int(config['KAFKA']['partitions']), replication_factor=3)) #changed from partitions
        admin_client.create_topics(new_topics=topic_list, validate_only=False)

    except Exception as e:
        print('%s - skipping topic creation' % e )
        return True

def get_schema_from_schema_registry(schema_registry_url, schema_registry_subject,schema_client_config):
    print(schema_registry_url)
    sr = SchemaRegistryClient(schema_client_config) #{'url': schema_registry_url})
    latest_version = sr.get_latest_version(schema_registry_subject)

    return sr, latest_version
def register_schema(schema_registry_url, schema_registry_subject, schema_str,schema_client_config):
    sr = SchemaRegistryClient(schema_client_config) #{'url': schema_registry_url})
    schema = Schema(schema_str, schema_type="AVRO")
    schema_id = sr.register_schema(subject_name0000=schema_registry_subject, schema=schema)

    return schema_id

#def serialize_avro_data(data,avro_schema):
    # Create Avro data writer
 #   try:
        #d={"company_symbol": "DSC", "company_name": "DEFIANT STATUE CORPORATION", "price": 48.33, "tx_time": "2023-12-16T15:31:36Z"}
       # print ('val='+validate(d, avro_schema))
      #  print (json.loads(data))
  #      fo = BytesIO()
        #print (json.dumps(data))
    #    fastavro.schemaless_writer(fo, avro_schema, data)
   #     #fastavro.writer(fo,avro_schema,data)
        
     
 #   except Exception as ex:
 #       print('Error converting to avro - %s' % str(ex))
 #       exit(1)
 #   return fo #avro_data_bytes


def delivery_report(errmsg, msg):
    if errmsg is not None:
        print("Delivery failed for Message: {} : {}".format(msg.key(), errmsg))
        return
    #print('Message: {} successfully produced to Topic: {} Partition: [{}] at offset {}'.format(msg.key(), msg.topic(), msg.partition(), msg.offset()))

def publish_message(kafka_producer, topic_name, key, value):
    try:   
        if config['KAFKA']['serialize']=='AVRO':
            # print('AVRO' + value)
            #avro_data_key = serialize_avro_data(key,avro_schema_stock_key)
            key_bytes = bytes(key, encoding='utf-8')
           # avro_data_value = serialize_avro_data(value,avro_schema_stock_value)
            kafka_producer.produce(topic=topic_name, key=key_bytes,value=value, on_delivery=delivery_report)
           # kafka_producer.produce(topic_name, key=key_bytes, value=value,callback=on_delivery)
        else:
            # print('NOT AVRO k='+key + ' value='+value)
            key_bytes = bytes(key, encoding='utf-8')
            value_bytes = bytes(value, encoding='utf-8')
            kafka_producer.produce(topic_name, key=key_bytes, value=value_bytes)
            #kafka_producer.flush()
    except Exception as ex:
        print('Error writing to Kafka - %s' % str(ex))
        exit(1)

def quitwrite(counter,starttime):
    print('\n\nStop execution.\n\n')
    printstats(counter,starttime)
    elapsed=(dt.now()-starttime)
    print('\n\nElapsed time: %s' % elapsed)

    os._exit(1)

def printstats(counter,starttime):
    b=dt.now()
    s=(b-starttime).total_seconds()
    t=round(decimal.Decimal(counter)/decimal.Decimal(s),2)
    print('Generated %s records. Rate %s/s' % (counter,t), end='\r')

def loadconfig():
    f=""

    if len(args.config)>0:
         f=args.config
    else:
        f='config.ini'
    
    if os.path.isfile(f)==False:
        print('\nConfiguration file ''config.ini'' does not exist.  Create one using the ''-createconfig'' parameter')
        exit()

    config.read(f)
    print('Loaded configuration file ' +f)

def createconfig():
    config['SETUP']={'type':'MONGODB', 'symbols':5, 'duration':0, 'include_exchange':True, 'threads':1,'time_as':'STRING'}
    config['KAFKA']={ 'bootstrap_servers':"localhost:9092", 'client_id':'stockgenclient','security_protocol':'SASL_SSL','sasl_mechanism':'PLAIN','sasl_plain_username':'','sasl_plain_password':'','topic':'Stocks','partitions':6,'serialize':'JSON','schema_registry_url':'onlyneededforAVRO','schema_registry_username':'onlyneededforAVRO','schema_registry_password':'onlyneededforAVRO'}
    config['MONGODB']={'connection':'mongodb://127.0.0.1','database':'StockData','collection':'Stocks'}
    with open('config.ini', 'x') as configfile:
        config.write(configfile)
    print('\n\nStockgen connection configuration file template written to ''config.ini''\n\nModify this file then restart stockgen application.\n\n')

def drop():
    if config['SETUP']['type']=='KAFKA':
        topic_list=[]
        print('dropping topic %s \n\n' % config['KAFKA']['topic'])
        topic_list.append(config['KAFKA']['topic'])
        try:
            admin_client = KafkaAdminClient(bootstrap_servers=config['KAFKA']['bootstrap_servers'],
                                        client_id=config['KAFKA']['client_id'],
                                        security_protocol=config['KAFKA']['security_protocol'],
                                        api_version=(0, 10),
                                        sasl_mechanism=config['KAFKA']['sasl_mechanism'],
                                        sasl_plain_username=config['KAFKA']['sasl_plain_username'],
                                        sasl_plain_password=config['KAFKA']['sasl_plain_password'])
            admin_client.delete_topics(topics=topic_list)
            print('Topic dropped!')
            exit()
        except Exception as e:
            print("Topic Doesn't Exist : " + str(e))
            exit()
    #if not Kafka it is mongodb
    try:
        c=MongoClient(host=config['MONGODB']['connection'], server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
        mydb = c[config['MONGODB']['database']]
        mydb.drop_collection(str(config['MONGODB']['collection']))
        print(str(config['MONGODB']['database'])+'.'+str(config['MONGODB']['collection'])+' dropped.')
    except Exception as ex:
        print('Error dropping collection - %s' % str(ex))

    
def main():
    global args

    parser = argparse.ArgumentParser()
    parser.add_argument("-createconfig","--createconfig",help="Create a configuration file template 'config.ini'",action="store_true")
    parser.add_argument("-config","--config",type=str, default='', help="Connection configuration file")
    parser.add_argument("-drop","--drop",help="Clears the destination collection or topic as defined in the configuration file",action="store_true")
    parser.add_argument("-ts","--timeseries",help="Creates the collection as a timeseries collection",action="store_true")
    parser.add_argument("-sa","--stopafter",type=int, default=0,help="Stop after X number of events")
    parser.add_argument('-e',"--errors", help="Add random errors to stream",action="store_true")

    args = parser.parse_args()

    #if the user wants to create a config, create one then exit
    if args.createconfig:
        createconfig()
        exit()

    loadconfig()


    #if user specifies -drop we attempt to delete the kafka topic and exit the program
    if args.drop:
        drop()
        exit()

    #If they want Kafka, load the schema registry as well, mainly only used with AVRO
    kafka_url = config['KAFKA']['bootstrap_servers']
    if config['KAFKA'].get('schema_registry_url') is not None:
        schema_registry_url = config['KAFKA']['schema_registry_url']
    else:
        schema_registry_url =''
    kafka_topic = config['KAFKA']['topic']
    schema_registry_subject = f"{kafka_topic}-value"

    if config['SETUP']['type']=='KAFKA':
            if config['KAFKA']['serialize']=='AVRO':
                    schema_client_config = {
                        'url': schema_registry_url,
                        'basic.auth.user.info': config['KAFKA']['schema_registry_username'] + ':' + config['KAFKA']['schema_registry_password']
                    }
                    print('Grabbing latest schema from registry')
                    sr, latest_version = get_schema_from_schema_registry(schema_registry_url, schema_registry_subject,schema_client_config)
                    value_avro_serializer = AvroSerializer(schema_registry_client = sr,
                                                schema_str = latest_version.schema.schema_str,
                                                conf={
                                                    'auto.register.schemas': False
                                                    }
                                                )

    #override config file with any parameters user specified then config becomes source of truth
    if int(config['SETUP']['symbols'])<1:
        config['SETUP']['symbols']=1

    threads = []

    if args.timeseries:
        if config['SETUP']['time_as']!='STRING': 
            print('\n** Time series collections require timeseries field to be in datetime field, ignoring --AsString parameter **\n\n')

    if config['SETUP']['type']=='KAFKA':
        #Wait until Kafka is online and ready for data
        while True:
            print('Checking Kafka Connection')
            if checkkafkaconnection()==False:
                print('Problem connecting to Kafka, sleeping 10 seconds')
                time.sleep(10)
            else:
                break
        print('Successfully connected to Kafka')
    else:
        #Wait until MongoDB Server is online and ready for data
        while True:
            print('Checking MongoDB Connection')
            if checkmongodbconnection()==False:
                print('Problem connecting to MongoDB, sleeping 10 seconds')
                time.sleep(10)
            else:
                break
        print('Successfully connected to MongoDB')

    txtime = dt.now() # use for ficticous timestamps in events
    txtime_end=txtime+timedelta(minutes=int(config['SETUP']['duration']))

    if int(config['SETUP']['duration'])==0:
        print('CONTINOUS WRITE MODE - press Control-C to exit program')
    
    if config['SETUP']['type']=='KAFKA':
        conf = {
            'bootstrap.servers':config['KAFKA']['bootstrap_servers'],
            'client.id':config['KAFKA']['client_id'],
            'security.protocol':config['KAFKA']['security_protocol'],
          #  'api.version':(0, 10),
            'sasl.mechanism':config['KAFKA']['sasl_mechanism'],
            'sasl.username':config['KAFKA']['sasl_plain_username'],
            'sasl.password':config['KAFKA']['sasl_plain_password'],
            'linger.ms':0
        }

        if config['KAFKA']['serialize']=='AVRO':
            producer = SerializingProducer({
                'bootstrap.servers': kafka_url,
                'security.protocol': config['KAFKA']['security_protocol'],
                'sasl.mechanism':config['KAFKA']['sasl_mechanism'],
                'sasl.username':config['KAFKA']['sasl_plain_username'],
                'sasl.password':config['KAFKA']['sasl_plain_password'],
                'value.serializer': value_avro_serializer,
                'delivery.timeout.ms': 1000,
                'enable.idempotence': 'true'
            })
        else:
            producer=KafkaProducer(conf)
    else:
        producer = MongoClient(config['MONGODB']['connection'], server_api=ServerApi("1", strict=False),maxPoolSize=None)
        db = producer.get_database(name=config['MONGODB']['database'])
        if args.timeseries:
            collection = db.create_collection(name=config['MONGODB']['collection'],timeseries= {"timeField": "tx_time", "granularity": "seconds"})
            print('Create timeseries collection result=' + collection.full_name)
     
    for i in range(0, int(config['SETUP']['threads'])): # parallel threads
        if config['SETUP']['type']=='MONGODB':
            t = threading.Thread(target=worker, args=[int(i), int(config['SETUP']['symbols']),db,txtime,txtime_end,'M'])
            threads.append(t)
        else:
            t = threading.Thread(target=worker, args=[int(i), int(config['SETUP']['symbols']),producer,txtime,txtime_end,'K'])
            threads.append(t)
    display_thread = threading.Thread(target=display_sum_per_second)
    display_thread.daemon = False
    threads.append(display_thread)

    for x in threads:
        x.start()
    for y in threads:
        y.join()

def display_sum_per_second():
    while True:
        # Store the current counter value
        with lock:
            current_counter = total_events

        # Sleep for 1 second
        time.sleep(1)

        # Calculate the difference in counter values
        with lock:
            counter_difference = total_events - current_counter

        # Display the sum of counters per second
        print(f"Sum of counters per second: {counter_difference} total_events: {total_events}")

        if args.stopafter>0:
            if total_events>=args.stopafter:
                print('Stopping!')
                exit(0)
        if threading.active_count()==2:
            return

def worker(workerthread, numofsymbols,producer,txtime,txtime_end,ptype):
    #ptype=K or M, Kafka or MongoDB
    #Create an initial value for each security
    #each thread spawns numerofsymbols

    company_name,company_symbol,company_exchange=generate_securities(int(config['SETUP']['symbols']))

    threadnum=str(workerthread)


    with lock:
        print('----------------------------------------------\nThread Start #',threadnum)
        print('\nData Generation Summary:\n{:<12} {:<12}\n{:<12} {:<12}\n{:<12} {:<12}'.format('# symbols',config['SETUP']['symbols'],'Bootstrap server ',config['KAFKA']['bootstrap_servers'],'Topic',config['KAFKA']['topic']))
        print('\n{:<8}  {:<50}'.format('Symbol','Company Name'))
        for x in range(len(company_name)):
            print('{:<8}  {:<50}'.format(company_symbol[x],company_name[x]))
        print('\n{:<12} {:<12}'.format('Start time',txtime.strftime('%Y-%m-%d %H:%M:%S')))
        if int(config['SETUP']['duration'])>0:
            print('{:<12} {:<12}\n'.format('End time',txtime_end.strftime('%Y-%m-%d %H:%M:%S')))
        else:
            print('No end time \n\n')

    last_value=[]
    print(config['SETUP']['time_as'])

    for i in range(0,int(config['SETUP']['symbols'])):
        last_value.append(round(random.uniform(1, 100), 2))
    try:
        txtime = dt.now()
        counter=0
        global total_events
        bContinue=True
        
        cache=[] # used for MongoDB insert_many
        while bContinue:
            for i in range(0,numofsymbols):
                #Get the last value of this particular security
                #time.sleep(1) can be used to throttle write speed
                x = getvalue(last_value[i])
                last_value[i] = x
                try:
                    if config['SETUP']['time_as']=='EPOCH':
                        thetime=int(txtime.timestamp()) #in epoch time
                    else:
                        thetime=txtime.strftime('%Y-%m-%dT%H:%M:%SZ')
                    if config['SETUP']['include_exchange']=='True':
                        ticker={'exchange':company_exchange[i],'company_symbol' : company_symbol[i], 'company_name': company_name[i],'price': x, 'tx_time':thetime} # txtime.strftime('%Y-%m-%dT%H:%M:%SZ')}
                        if args.errors:
                                if random.random()>0.95:
                                    ticker={'exchange':company_exchange[i],'company_symbol' : company_symbol[i], 'company_name': company_name[i],'error_num':100,'error_msg':'Failed to retrieve'}
                    else:
                        ticker={'company_symbol' : company_symbol[i], 'company_name': company_name[i],'price': x, 'tx_time': thetime} #txtime.isoformat()} #.timestamp()} #txtime.strftime('%Y-%m-%dT%H:%M:%SZ')}
                    if ptype=='K':
                       # print('time=='+thetime)
                        publish_message(kafka_producer=producer,topic_name=config['KAFKA']['topic'],key=company_symbol[i],value=json.dumps(ticker))
                        if counter%100==0:
                            producer.flush()
                    else:
                        cache.append({'company_symbol' : company_symbol[i], 'company_name': company_name[i],'price': x, 'tx_time': thetime})
                        if counter%100==0:
                            producer[config['MONGODB']['collection']].insert_many(cache)
                            cache=[]
                    counter=counter+1
                    total_events+=1
                    txtime+=timedelta(seconds=1)
                    if int(config['SETUP']['duration'])>0:
                      if txtime > txtime_end:
                        bContinue=False
                        continue
                    if args.stopafter>0:
                        if total_events>=args.stopafter:
                            print('Stopping!')
                            bContinue=False
                            break
                except Exception as e:
                    print("error: " + str(e))
        duration=txtime - dt.now()
        print('\nFinished - ' + str(duration).split('.')[0])
        if producer is not None:
            if config['SETUP']['type']=='MONGODB':
                producer.close()
            else:
                producer.flush()
        return
    except:
        print('Unexpected error:', sys.exc_info()[0])
        raise

if __name__ == '__main__':
    main()
