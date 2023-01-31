To build:

`make clean`

To run:

`make up`


## Re-orgs

I use the MongoDB Upsert operation to deal with re-orgs: if the block # does not exist we simply insert it into the database, otherwise if there's an existing entry this means the block was affected by a re-org and we update the entry with the live data provided by the API instead.

In the case of re-orgs, there may be stale data from "future" blocks in our local database (e.g. head is at 5 due to a re-org but we will have database entries for blocks 6, 7, etc.) 

To bypass/fix this we can filter all entries with a block number greater than the current head. (not implemented)

## Syncing 

To sync blocks, I check for the latest entry in the database, and retrieve:
1. Live data from the API for that block
2. The current head of the chain

If the data from the latest entry in the database does not match the live data returned from #1, this means that an re-org happened while the indexer was offline and some of the data in our database is stale. 

(e.g. latest entry was block 5 with data "message_5", but API shows block 5 with data "message_10")

To fix this, moving backwards and starting from the first stale database entry I cross-reference with the live data from the API until I find the first database entry that has matching data with the API. I use this point as the starting block for the sync.

To perform the sync, I retrieve all blocks between my starting point and the current head of the chain, either updating data if it's stale or inserting missing blocks.

## Data Processing & Etc.

To process the block data in an asynchronous manner, I use a ThreadPool with individual workers which "performs" the computation on each block (just sleeps for 2.5 seconds). 

I've added an endpoint in the server API to return the `BLOCK_MAPPING` object. I retrieve and print this out at the end to compare to the database indexer and data collections. 

I've mocked the data computation but we can check from the output at the end that the data (message #) in the database for storing computation results matches the server's `BLOCK_MAPPING` and the database index, so we can be sure that it is re-org compatible and would have the correct data if we chose to perform 1 million iteration hashing like in the example.

Note: I'm only mining/indexing 25 blocks here before shutting off, but in production we would keep the indexer on.

There's also code commented out which can be used to test the behavior of the sync function.