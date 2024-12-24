from datetime import datetime, timezone
from typing import Dict, List, Optional
from bson import Code
from pymongo.errors import PyMongoError
from flask import current_app
from flask import logging
from models.cluster import Cluster, Source
from utils.database import clusters_collection

class ClusterService:
    def __init__(self):
        self.collection = clusters_collection

    def create(self, cluster: Cluster):
        try:
            # Convert cluster to dict, and insert into MongoDB collection
            cluster_dict = cluster.to_dict()
            result = self.collection.insert_one(cluster_dict)
            cluster_id = cluster.cluster_id
            current_app.logger.info(f"Cluster {cluster_id} created successfully.")
            return cluster_id

        except PyMongoError as e:
            current_app.logger.error(f"Error occurred while inserting cluster: {e}")
            raise

        except Exception as e:
            current_app.logger.error(f"Unexpected error occurred: {e}")
            raise

    def get(self, cluster_id: str) -> Optional[Cluster]:
        data = self.collection.find_one({"cluster_id": cluster_id})
        if not data:
            return None
        return self._from_dict(data)
    
    def get_all(self) -> Optional[list[Cluster]]:
        data = self.collection.find()
        if not data:
            return None
        return [ self._from_dict(d) for d in data ]

    def update(self, cluster_id: str, updated_data: Cluster):
        return self.collection.update_one({"cluster_id": cluster_id}, {"$set": updated_data.to_dict()})

    # TODO: check the function of replace or create
    def upsert(self, cluster_id: str, updated_data: Cluster):
        data = updated_data.to_dict()

        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
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
        result = clusters_collection.update_one(
            {"cluster_id": cluster_id},
            set_operations,
            upsert=True
        )
        return cluster_id, result
    
    def delete(self, cluster_id: str):
        result = self.collection.delete_one({"cluster_id": cluster_id})
        if result.deleted_count == 0:
            return None
        return cluster_id

    def find_network_inconsistencies(self, cluster_id: str, return_all: bool = True):
        # Define the JavaScript function to compute inconsistencies
        with open("utils/networkCheck.js") as f:
            js_function = Code(f.read())

        # Define the aggregation pipeline
        pipeline = [
            {
                "$match": {
                    "cluster_id": cluster_id
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
    # def upsert_source(self, cluster_id: str, source_name: str, networks: List[Dict]):
    #     cluster = self.collection.find_one({"cluster_id": cluster_id})
    #     if not cluster:
    #         raise ValueError("Cluster not found")

    #     sources = cluster.get("sources", {})
    #     source_data = {
    #         "networks": networks,
    #         "last_updated": datetime.now().isoformat()
    #     }
    #     sources[source_name] = source_data
        
    #     self.collection.update_one(
    #         {"cluster_id": cluster_id},
    #         {"$set": {"sources": sources, "last_updated": datetime.now().isoformat()}}
    #     )

    def _from_dict(self, data: Dict) -> Cluster:
        return Cluster.from_dict(data)
