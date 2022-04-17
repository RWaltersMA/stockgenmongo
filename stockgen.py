import random
from random import seed
from random import randint
import argparse
import pymongo
from pymongo import errors
import signal

from datetime import date, timedelta, datetime as dt
import threading
import sys
import time

lock = threading.Lock()

start_time = dt.now()

volatility = 1  # .001

#arrays used to store ficticous securities
company_symbol=[]
company_name=[]

#the following two functions are used to come up with some fake stock securities
def generate_symbol(a,n,e):
    #we need to break this out into its own function to do checks to make sure we dont have duplicate symbols
    for x in range(1,len(a)):
        symbol=str(a[:x]+n[:1]+e[:1])
        if symbol not in company_symbol:
            return symbol

def generate_securities(numberofsecurities):
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
        company_name.append(a + ' ' + n + ' ' + e)
        company_symbol.append(generate_symbol(a,n,e))

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

#When the conainters launch, we want to not crash out if the MongoDB Server container isn't fully up yet so here we wait until we can connect
def checkmongodbconnection():
    try:
        c = pymongo.MongoClient(MONGO_URI)
        c.admin.command('ismaster')
        time.sleep(2)
        c.close()
        return True
    except pymongo.errors.ServerSelectionTimeoutError as e:
        print('Could not connect to server: %s',e)
        return False

def sigint_handler(signal, frame):
    time_elapsed = dt.now() - start_time
    print('\n\Duration:',time_elapsed)
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def main():
    global args
    global MONGO_URI
    # capture parameters from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--symbols", type=int, default=5, help="number of financial stock symbols")
    parser.add_argument("-c","--connection",type=str, default='mongodb://127.0.0.1:27017/?directConnection=true', help="MongoDB connection string")
    parser.add_argument("-db","--database", default='Stocks', help="MongoDB database name")
    parser.add_argument("-col","--collection", default='StockData', help="MongoDB collection name")
    parser.add_argument("-as","--timeasstring", action='store_true', help="Store tx_time as string instead of ISODate")
    parser.add_argument("-q","--quiet", action='store_true', help="Summarize write information")
    parser.add_argument("-n","--numberofsamples", type=int, default=0, help="Number of samples to generate (0=infinite)")    
    args = parser.parse_args()

    if args.symbols:
        if args.symbols < 1:
            args.symbols = 1

    MONGO_URI=args.connection

    threads = []

    generate_securities(args.symbols)

    print('\nGenerating stock ticker data for the following securities\n\n')
    #print summary information
    for i in range(0,int(args.symbols)):
        print(company_symbol[i] + '\t' + company_name[i])

    # this is an artifact left over from another demo, I left it in here in case you want to make parallel threads
    for i in range(0, 1): # parallel threads
        t = threading.Thread(target=worker, args=[int(i), int(args.symbols)])
        threads.append(t)
    for x in threads:
        x.start()
    for y in threads:
        y.join()

def worker(workerthread, numofsymbols):
    try:
        #Create an initial value for each security
        last_value=[]
        for i in range(0,numofsymbols):
            last_value.append(round(random.uniform(1, 100), 2))

        #Wait until MongoDB Server is online and ready for data
        while True:
            print('\n\nChecking MongoDB Connection')
            if checkmongodbconnection()==False:
                print('Problem connecting to MongoDB, sleeping 10 seconds')
                time.sleep(10)
            else:
                break
        print('Successfully connected to MongoDB')

        c = pymongo.MongoClient(MONGO_URI)
        db = c.get_database(args.database)
        iCounter=0
        print('\nStart time: {}\n'.format(start_time))
        
        while True:
            for i in range(0,numofsymbols):
                #Get the last value of this particular security
                x = getvalue(last_value[i])
                last_value[i] = x
                txtime = dt.now()
                iCounter=iCounter+1
                try:
                    if args.timeasstring is True:
                        result=db[args.collection].insert_one( { 'company_symbol' : company_symbol[i], 'company_name': company_name[i],'price': x, 'tx_time': txtime.strftime('%Y-%m-%dT%H:%M:%SZ')})
                    else:
                        result=db[args.collection].insert_one( { 'company_symbol' : company_symbol[i], 'company_name': company_name[i],'price': x, 'tx_time': txtime})
                    if iCounter%100==0:
                        if args.numberofsamples>0:
                            fPercent=(1-(args.numberofsamples-iCounter)/args.numberofsamples)*100
                            print(f"Wrote {iCounter} documents ({fPercent:.0f}%)", end = "\r")
                        print(f"Wrote {iCounter} documents", end = "\r")    
                    if args.quiet is not True:
                        print(str(iCounter) + ' _id=' + str(result.inserted_id) + '   ' + company_symbol[i] + ' ' + company_name[i] + ' traded at ' + str(x) + ' ' + txtime.strftime('%Y-%m-%d %H:%M:%S'))
                except Exception as e:
                    print("Error: " + str(e))
            time.sleep(1)
            if args.numberofsamples>0:
                if iCounter>args.numberofsamples:
                    break
        c.close()
        time_elapsed = dt.now() - start_time 
        print('\n\nElapsed time: ',time_elapsed)
    except:
        print('Unexpected error:', sys.exc_info()[0])
        raise


main()

