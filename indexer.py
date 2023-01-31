import requests
import time
from concurrent.futures import ThreadPoolExecutor, wait
from pymongo import MongoClient, ASCENDING, DESCENDING

def process_data(collection, block):
    data = block["data"]
    # do some expensive computation here that takes 2.5 seconds
    time.sleep(2.5)
    res = collection.update_one({"block": block["block"]}, {"$set": {"result": data}}, upsert=True)
    print("DATA: Processed block ", block, " block reorged? : ", res.raw_result["updatedExisting"], flush=True)

def connect():
    client = MongoClient("mongodb://db:27017/")
    db = client["succinct"]
    return db

def mine_block():
    try:
        r = requests.get('http://server:8000/head')
        head = r.json()["head"]
        return head
    except requests.exceptions.RequestException as e:
        return "Request failed: {}".format(e)

def retrieve_block(block_num):
    try:
        r = requests.get("http://server:8000/block/{}".format(block_num))
        return r.json()
    except requests.exceptions.RequestException as e:
        return "Request failed: {}".format(e)

def sync_blocks(db, pool, futures):
    def get_last_inserted():
        entries = list(db.get_collection("blocks").find().sort("_id", DESCENDING).limit(1))
        return entries[0] if entries else None
    
    previous_block = get_last_inserted()
    if not previous_block:
        block_num=0
    else:
        block_num = previous_block["block"]
    print("Last added: ", previous_block, flush=True)
    
    # Find last entry with correct data
    while previous_block and db.get_collection("blocks").find_one({"block": block_num})["data"] != retrieve_block(block_num).get("data", -1):
        if block_num < 1:
            break
        block_num -= 1
    
    # Retrieve the current head of chain and insert all intermediary blocks starting from the most recently indexed one
    head = mine_block()
    start, end = block_num+1, head+1
    for block_num in range(start, end):
        block = retrieve_block(block_num)
        res = db.get_collection("blocks").update_one({"block": block["block"]}, {"$set": {"data": block["data"]}}, upsert=True)
        print("Syncing block ", block, " block reorged? : ", res.raw_result["updatedExisting"], flush=True)
        future = pool.submit(process_data, db.get_collection("data"), block)
        futures.append(future)

if __name__ == '__main__':
    
    # Create database connection and data processing queue
    db = connect()
    pool = ThreadPoolExecutor()
    futures = []
    
    # Create indices on block # for both collections
    blocks, data = db.get_collection("blocks"), db.get_collection("data")
    blocks.create_index([("block", ASCENDING)], unique=True)
    data.create_index([("block", ASCENDING)], unique=True)
    
    # Commented code here was used to test sync function
    # for _ in range(10):
    #     h = mine_block()
    #     block = retrieve_block(h)
    #     res = blocks.update_one({"block": block["block"]}, {"$set": {"data": block["data"]}}, upsert=True)
    #     future = pool.submit(process_data, data, block)
        
    # for _ in range(10):
    #     mine_block()
        
    # Sync to database
    sync_blocks(db, pool, futures)
    
    for _ in range(25):
        head = mine_block()
        block = retrieve_block(head)
        # Index block
        res = blocks.update_one({"block": block["block"]}, {"$set": {"data": block["data"]}}, upsert=True)
        print("Block ", block, " block reorged? : ", res.raw_result["updatedExisting"], flush=True)
        # Enqueue data
        future = pool.submit(process_data, data, block)
        futures.append(future)
        time.sleep(1)
    
    # Wait for data to finish processing
    wait(futures)
    
    # Print index collection
    print("Block index: ", flush=True)
    cursor = blocks.find({})
    for document in cursor:
        print(document, flush=True)
    
    # Print out the mapping from server to check that it matches the data in our databases
    r = requests.get("http://server:8000/all")
    print("BLOCK_MAPPING:", flush=True)
    for k, v in r.json().items():
        print("{ block: ", k, ", data: ", "message_{}".format(v), " }", flush=True)
    
    # Print data collection
    print("Data: ", flush=True)
    cursor = data.find({})
    for document in cursor:
        print(document, flush=True)
    pool.shutdown()