from typing import Dict, Optional
from bson import Code
from flask import Blueprint, request, jsonify
from flask_deprecate import deprecate_route
from flask import current_app
from bson.objectid import ObjectId
from datetime import datetime, timezone
from services import AlreadyExistError, DataNotFoundError
from utils.database import servers_collection
from models.server import Server, Source
from pymongo.errors import PyMongoError

servers_api = Blueprint('servers_api', __name__)

class ServerService:
    def __init__(self):
        self.collection = servers_collection

    def create(self, server: Server):
        """Create a new server."""
        try:
            data = server.to_dict()
            # result = servers_collection.insert_one(data)
            result = self.collection.update_one(
                {"server_id": server.server_id},
                {"$setOnInsert": data},
                upsert=True
            )
            if result.matched_count != 0 and result.upserted_id is None:
                raise AlreadyExistError(f"Server {data.get('server_id')} already exist.")
            current_app.logger.info(f"Server {data.get('server_id')} created successfully.")
            return data.get("server_id")
        except PyMongoError as e:
            current_app.logger.error(f"Error occurred while inserting server: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Unexpected error occurred: {e}")
            raise

    # okk
    def get(self, server_id: str):
        """Get a single server by ID."""
        data = self.collection.find_one({"server_id": server_id})
        if not data:
            return None
        server = self._from_dict(data)
        return server

    # okk
    def get_all(self):
        """Get all servers."""
        servers = list(self.collection.find())
        if not servers:
            return None
        servers = [self._from_dict(server) for server in servers]
        return servers

    def get_paginated(self, page, limit):
        """Fetch paginated server data."""
        skip = (page - 1) * limit
        cursor = servers_collection.find().skip(skip).limit(limit)
        total_count = servers_collection.count_documents({})
        servers = [self._from_dict(doc) for doc in cursor]
        return servers, total_count
    
    def update(self, server_id: str, server_data: Server):
        """Update a server by ID."""
        server = find_server_by_id(server_id)
        if not server:
            return DataNotFoundError("Server not found")
        
        data = server_data.to_dict()
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        servers_collection.update_one({"server_id": server_id}, {"$set": data})
        return server_id
    
    # TODO: check the function of replace or create
    def upsert(self, server_id: Optional[str] = None, server: Optional[Server] = None, filter: Optional[Dict] = None):
        """Create or update a server."""
        if not server:
            raise ValueError("Server data is required")
        
        data = server.to_dict()

        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        if not filter:
            filter = {"server_id": server_id}
            
        set_operations = [
            {
                "$set": { key: value for key, value in data.items() if key != "sources"}
            }
        ]
        
        if "sources" in data.keys() and data['sources']:
            set_operations.append({
                '$set': {
                    'sources': {
                        '$mergeObjects': ['$sources', data['sources']]
                    }
                }
            })
        result = servers_collection.update_one(
            filter,
            set_operations,
            upsert=True
        )
        return server_id, result

    # TODO: patch or create
    def patch(self, server_id: str, server_data: Server):
        """Patch a server by ID."""
        server = find_server_by_id(server_id)
        if not server:
            return DataNotFoundError("Server not found")
        
        data = server_data.to_dict()
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        servers_collection.update_one({"server_id": server_id}, {"$set": data})
        return server_id
    
    def delete(self, server_id: str):
        """Delete a server by ID."""
        result = self.collection.delete_one({"server_id": server_id})
        if result.deleted_count == 0:
            return None
        return server_id
    
    def create_or_update_source(self, server_id: str, source_name: str, source_data: Source):
        """Create a new source for a server."""
        # Convert the source_data into a dictionary
        data = source_data.to_dict()

        # Find the server by its ID to check if it exists
        server = servers_collection.find_one({"server_id": server_id})
        if not server:
            return jsonify({"error": "Server not found"}), 404

        # Check if the source already exists
        # if f"sources.{source_name}" in server.get("sources", {}):
        #     return jsonify({"error": f"Source '{source_name}' already exists"}), 400

        # Update only the specific source in the sources dictionary
        update_result = servers_collection.update_one(
            {"server_id": server_id},  # Query filter
            {"$set": {f"sources.{source_name}": data}}  # Add the new source
        )

        if update_result.modified_count == 1:
            return jsonify({"message": f"Source '{source_name}' added successfully"}), 201
        else:
            return jsonify({"error": "Failed to add source"}), 500

    # add a new parameter to the function to let it return the server data even there is no inconsistency
    def find_network_inconsistencies(self, server_id: str, return_all: bool = True):
        # Define the JavaScript function to compute inconsistencies
        with open("utils/networkCheck.js") as f:
            js_function = Code(f.read())
            
        # Define the aggregation pipeline
        pipeline = [
            {
                "$match": {
                    "server_id": server_id
                }
            },
            {
                "$addFields": {
                    "inconsistencies": {
                        "$function": {
                            "body": js_function,
                            "args": ["$networks", "$sources"],
                            "lang": "js"
                        }
                    }
                }
            }
        ]
        if not return_all:
            pipeline.append({
                "$match": {
                    "inconsistencies.0": {"$exists": True}  # Only include documents with inconsistencies
                }
            })

        # Run the aggregation pipeline and return results
        results = list(self.collection.aggregate(pipeline))
        result = results[0] if results else {}
        return result

    def find_network_inconsistencies_all(self):
        # Define the JavaScript function to compute inconsistencies
        
        with open("utils/networkCheck.js") as f:
            js_function = Code(f.read())
        
        # Define the aggregation pipeline
        pipeline = [
            {
                "$addFields": {
                    "inconsistencies": {
                        "$function": {
                            "body": js_function,
                            "args": ["$networks", "$sources"],
                            "lang": "js"
                        }
                    }
                }
            },
            {
                "$match": {
                    "inconsistencies.0": {"$exists": True}  # Only include documents with inconsistencies
                }
            }
        ]

        # Run the aggregation pipeline and return results
        return list(self.collection.aggregate(pipeline))

    def count(self):
        return self.collection.count_documents({})
    
    def _from_dict(self, data: Dict) -> Server:
        return Server.from_dict(data)
    
# ------------------------------
# Utility functions
# ------------------------------
def clean_data(data):
    # Define the allowed template keys
    template_keys = {
        "server_id", "hostname", "serial_number", "location", "datacenter", 
        "room", "rack", "unit", "os", "owner", "cluster", "additional_info", 
        "networks", "sources", "last_updated"
    }
    
    # Remove keys that are not in the template
    cleaned_data = {key: value for key, value in data.items() if key in template_keys}
    
    # Clean networks and sources substructures recursively if they exist
    if "networks" in cleaned_data:
        cleaned_data["networks"] = [
            {key: value for key, value in network.items() if key in ["name", "type", "ip", "subnet_mask", "mac"]}
            for network in cleaned_data["networks"]
        ]
    
    if "sources" in cleaned_data:
        cleaned_data["sources"] = {
            source: {
                "networks": [
                    {key: value for key, value in network.items() if key in ["name", "type", "ip", "subnet_mask", "mac"]}
                    for network in source_data["networks"]
                ],
                **{key: value for key, value in source_data.items() if key != "networks"}
            }
            for source, source_data in cleaned_data["sources"].items()
        }
    
    return cleaned_data

def validate_data(data):
    # Define the allowed template keys
    template_keys = {
        "server_id", "hostname", "serial_number", "location", "datacenter", 
        "room", "rack", "unit", "os", "owner", "cluster", "additional_info", 
        "networks", "sources", "last_updated"
    }
    
    # Check if the server_id is missing
    if "server_id" not in data:
        return False, f"Missing required field: server_id"
    
    # Check if there are any extra keys not in the template
    extra_keys = set(data.keys()) - template_keys
    if extra_keys:
        return False, f"Extra keys found: {extra_keys}"
    
    # Additional validation for networks and sources
    if "networks" in data:
        for network in data["networks"]:
            if not all(key in network for key in ["name", "type", "ip", "subnet_mask", "mac"]):
                return False, f"Missing required field in: {network}"
    
    if "sources" in data:
        for source, source_data in data["sources"].items():
            if "networks" in source_data:
                for network in source_data["networks"]:
                    if not all(key in network for key in ["name", "type", "ip", "subnet_mask", "mac"]):
                        return False, f"Missing required field in: {source}"

    # If all checks pass, return True
    return True, None

def find_server_by_id(server_id):
    """Finds a server by ID."""
    return servers_collection.find_one({"server_id": server_id})


@servers_api.route("/batch", methods=["PUT"])
def batch_update_servers():
    """Batch update servers."""
    data = request.json  # Expects a list of server updates
    for update in data:
        server_id = update.pop("_id", None)
        if server_id:
            servers_collection.update_one({"_id": ObjectId(server_id)}, {"$set": update})
    return jsonify({"message": "Batch update completed"}), 200

# ------------------------------
# Sources API
# ------------------------------
@servers_api.route("/<string:server_id>/sources/<string:source_name>", methods=["PUT"])
def update_source(server_id, source_name):
    """Create or update data for a single source."""
    data = request.json
    server = find_server_by_id(server_id)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    # Check if the source exists in the dictionary
    sources = server.get("sources", {})
    if source_name not in sources:
        # Create new source
        sources[source_name] = {
            "networks": data.get("networks", []),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    else:
        # Update existing source
        sources[source_name]["networks"] = data.get("networks", sources[source_name]["networks"])
        sources[source_name]["last_updated"] = datetime.now(timezone.utc).isoformat()

    servers_collection.update_one({"_id": ObjectId(server_id)}, {"$set": {"sources": sources}})
    return jsonify({"message": "Source created or updated"}), 200

@servers_api.route("/batch/<string:source_name>", methods=["PUT"])
def batch_update_source(source_name):
    """Batch update data of a source."""
    data = request.json  # Expects a list of updates for a specific source
    for update in data:
        server_id = update.pop("server_id", None)
        if not server_id:
            continue

        server = find_server_by_id(server_id)
        if not server:
            continue

        # Check if the source exists in the dictionary
        sources = server.get("sources", {})
        if source_name in sources:
            sources[source_name]["networks"] = update.get("networks", sources[source_name]["networks"])
            sources[source_name]["last_updated"] = datetime.now(timezone.utc).isoformat()
            servers_collection.update_one({"_id": ObjectId(server_id)}, {"$set": {"sources": sources}})

    return jsonify({"message": "Batch source update completed"}), 200




