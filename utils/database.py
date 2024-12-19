import os
import pymongo
from utils.config import mongo_uri, mongo_database, mongo_userame, mongo_password, mongo_servers_collection, mongo_clusters_collection, mongo_cilium_collection

# =============================================================================
# Connect to MongoDB
# =============================================================================
def connect_to_database(target_collection=''):
    """
    Connect to MongoDB and return the specified collection or database.

    :param target_collection: Name of the collection to connect to (optional)
    :return: A MongoDB collection or database object
    """
    try:
        if mongo_userame and mongo_password:
            # Authenticate with username and password
            mongo_client = pymongo.MongoClient(mongo_uri, username=mongo_userame, password=mongo_password)
        else:
            # Connect without authentication
            mongo_client = pymongo.MongoClient(mongo_uri)
    except Exception as error:
        print(f"[Error] Failed to connect to MongoDB: {error}")
        return None

    print("[Success] Connected to MongoDB successfully")

    # Select database
    database = mongo_client[mongo_database]

    if not target_collection:
        return database

    # Select collection
    collection = database[target_collection]

    # Check if collection exists
    existing_collections = database.list_collection_names()
    if target_collection in existing_collections:
        print(f"[Info] Collection '{target_collection}' already exists.")
    else:
        print(f"[Info] Collection '{target_collection}' does not exist. It will be created when data is added.")

    return collection

# Establish connection to database and collections
db = connect_to_database()
servers_collection = db[mongo_servers_collection] if db is not None else None
clusters_collection = db[mongo_clusters_collection] if db is not None else None
cilium_collection = db[mongo_cilium_collection] if db is not None else None
