from datetime import datetime
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
    
    def get_all(self) -> Optional[Cluster]:
        data = self.collection.find()
        if not data:
            return None
        return [ self._from_dict(d) for d in data ]

    def update(self, cluster_id: str, updated_data: Cluster):
        return self.collection.update_one({"cluster_id": cluster_id}, {"$set": updated_data.to_dict()})

    def upsert(self, cluster_id: str, updated_data: Cluster):
        return self.collection.update_one({"cluster_id": cluster_id}, {"$set": updated_data.to_dict()}, upsert=True)
    
    def delete(self, cluster_id: str):
        result = self.collection.delete_one({"cluster_id": cluster_id})
        if result.deleted_count == 0:
            return None
        return cluster_id

    def find_network_inconsistencies(self, cluster_id: str):
        # Define the JavaScript function to compute inconsistencies
        js_function = Code("""
            function check(
                networks,
                sources,
                type = 'cidr',
                allowMissingFields = ['cidrs'],
                fieldsToCheck = ['cidrs'],
                allowNullFields = ['cidrs']
            ) {
                function areValuesSame(a, b) {
                    // Check if both are strings
                    if (typeof a === 'string' && typeof b === 'string') {
                        return a === b;
                    }

                    // Check if both are arrays
                    if (Array.isArray(a) && Array.isArray(b)) {
                        // Quick length check
                        if (a.length !== b.length) return false;

                        // Count frequencies of elements in both arrays using plain object
                        const countMap = {};

                        for (const item of a) {
                            countMap[item] = (countMap[item] || 0) + 1;
                        }

                        for (const item of b) {
                            if (!countMap[item] || countMap[item] === 0) {
                                return false;
                            }
                            countMap[item] -= 1;
                        }

                        return true;
                    }

                    // If not string or array, return false
                    return false;
                }

                if (sources.Truth) {
                    throw new Error("Cannot use Truth as a source name.");
                }

                const allSources = { ...sources, Truth: { networks: networks || [] } };
                const inconsistencies = [];

                // Collect all networks by `name-type` into a unified map
                const unifiedMap = {};
                for (const sourceName in allSources) {
                    const source = allSources[sourceName];
                    (source.networks || []).forEach(net => {
                        if (net.type === type) {
                            const key = `${net.name}-${net.type}`;
                            if (!unifiedMap[key]) {
                                unifiedMap[key] = [];
                            }
                            unifiedMap[key].push({ source: sourceName, record: net });
                        }
                    });
                }
                // Given all sources, collect all networks by `name-type` into a unified map
                // the key is `name-type` and the value is an array of objects with source and record
                // name and type are required, other fields are optional
                // examples: 
                // unifiedMap = {
                //   'test-cidr': [
                //     { source: 'Truth', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } },
                //     { source: 'source1', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } }
                //   ]
                // }
                //

                // Check inconsistencies for each key in the unified map
                for (const [key, entries] of Object.entries(unifiedMap)) {
                    const name = entries[0].record.name;
                    const type = entries[0].record.type;
                    // example of  [key, entries]
                    // key: 'test-cidr'
                    // entries:
                    // [
                    //   { source: 'Truth', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } },
                    //   { source: 'source1', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } }
                    // ]
                    const details = [];

                    for (const field of fieldsToCheck) {
                        // examples
                        // const fieldValuesList = [
                        //     { value: "192.168.1.1", sources: ["server1", "server2"] },
                        //     { value: "192.168.1.2", sources: ["server3"] },
                        // ];
                        const fieldValuesList = [];
                        let missingCount = 0;

                        entries.forEach(({ source, record }) => {
                            const value = record[field];

                            if (value !== undefined) {
                                // Check null values only for fields not in allowNullFields
                                if (value !== null || allowNullFields.includes(field)) {
                                    if (value !== null) {

                                        // Find the object with the matching IP address (value)
                                        const target = fieldValuesList.find(item => areValuesSame(item.value, value));
                                        
                                        // If the object is found, insert the source
                                        if (target) {
                                            // Check if the source is already in the sources array to avoid duplicates
                                            if (!target.sources.includes(source)) {
                                                target.sources.push(source);
                                            }
                                        } else {
                                            fieldValuesList.push( ({value: value, sources: [source]}) )
                                        }

                                    }
                                } else {
                                    missingCount++;
                                }
                            } else {
                                // Allow missing fields if specified
                                if (!allowMissingFields.includes(field)) {
                                    missingCount++;
                                }
                            }
                        });

                        const uniqueValuesCount = fieldValuesList.length;
                        const totalSources = entries.length;

                        // Determine if it's a mismatch, missing, or both
                        // if (uniqueValues.length > 1) {
                        if (uniqueValuesCount > 1) {
                            // Mismatch detected
                            details.push({
                                field,
                                type: "mismatch",
                                values: fieldValuesList,
                                // values: Object.entries(fieldValues).map(([value, sources]) => ({ value, sources })),
                                message: `${field.toUpperCase()} mismatch across sources`
                            });
                        }

                        if (missingCount > 0 && !allowMissingFields.includes(field) && missingCount < totalSources) {
                            // Missing values detected
                            details.push({
                                field,
                                type: "missing",
                                missingSources: entries.filter(e => !e.record[field]).map(e => e.source),
                                message: `${field.toUpperCase()} missing in some sources`
                            });
                        }

                        // if (uniqueValuesCount > 1 && missingCount > 0) {
                        // // if (uniqueValues.length > 1 && missingCount > 0) {
                        //     // Both mismatch and missing detected
                        //     details.push({
                        //         field,
                        //         values: fieldValuesList,
                        //         // values: Object.entries(fieldValues).map(([value, sources]) => ({ value, sources })),
                        //         missingSources: entries.filter(e => !e.record[field]).map(e => e.source),
                        //         message: `${field.toUpperCase()} mismatch and missing in some sources`
                        //     });
                        // }
                    }

                    if (details.length > 0) {
                        inconsistencies.push({
                            name,
                            type,
                            key,
                            sources: entries.map(e => e.source),
                            details
                        });
                    }
                }

                return inconsistencies;
            }

        """)
        

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
            },
            {
                "$match": {
                    "inconsistencies.0": {"$exists": True}  # Only include documents with inconsistencies
                }
            }
        ]

        # Run the aggregation pipeline and return results
        results = list(self.collection.aggregate(pipeline))
        result = results[0] if results else {}
        return result

    def find_network_inconsistencies_all(self):
        # Define the JavaScript function to compute inconsistencies
        js_function = Code("""
            function check(
                networks,
                sources,
                type = 'cidr',
                allowMissingFields = ['cidrs'],
                fieldsToCheck = ['cidrs'],
                allowNullFields = ['cidrs']
            ) {
                function areValuesSame(a, b) {
                    // Check if both are strings
                    if (typeof a === 'string' && typeof b === 'string') {
                        return a === b;
                    }

                    // Check if both are arrays
                    if (Array.isArray(a) && Array.isArray(b)) {
                        // Quick length check
                        if (a.length !== b.length) return false;

                        // Count frequencies of elements in both arrays using plain object
                        const countMap = {};

                        for (const item of a) {
                            countMap[item] = (countMap[item] || 0) + 1;
                        }

                        for (const item of b) {
                            if (!countMap[item] || countMap[item] === 0) {
                                return false;
                            }
                            countMap[item] -= 1;
                        }

                        return true;
                    }

                    // If not string or array, return false
                    return false;
                }

                if (sources.Truth) {
                    throw new Error("Cannot use Truth as a source name.");
                }

                const allSources = { ...sources, Truth: { networks: networks || [] } };
                const inconsistencies = [];

                // Collect all networks by `name-type` into a unified map
                const unifiedMap = {};
                for (const sourceName in allSources) {
                    const source = allSources[sourceName];
                    (source.networks || []).forEach(net => {
                        if (net.type === type) {
                            const key = `${net.name}-${net.type}`;
                            if (!unifiedMap[key]) {
                                unifiedMap[key] = [];
                            }
                            unifiedMap[key].push({ source: sourceName, record: net });
                        }
                    });
                }
                // Given all sources, collect all networks by `name-type` into a unified map
                // the key is `name-type` and the value is an array of objects with source and record
                // name and type are required, other fields are optional
                // examples: 
                // unifiedMap = {
                //   'test-cidr': [
                //     { source: 'Truth', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } },
                //     { source: 'source1', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } }
                //   ]
                // }
                //

                // Check inconsistencies for each key in the unified map
                for (const [key, entries] of Object.entries(unifiedMap)) {
                    const name = entries[0].record.name;
                    const type = entries[0].record.type;
                    // example of  [key, entries]
                    // key: 'test-cidr'
                    // entries:
                    // [
                    //   { source: 'Truth', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } },
                    //   { source: 'source1', record: { name: 'test', type: 'cidr', cidrs: ['1.1.1.1/32'] } }
                    // ]
                    const details = [];

                    for (const field of fieldsToCheck) {
                        // examples
                        // const fieldValuesList = [
                        //     { value: "192.168.1.1", sources: ["server1", "server2"] },
                        //     { value: "192.168.1.2", sources: ["server3"] },
                        // ];
                        const fieldValuesList = [];
                        let missingCount = 0;

                        entries.forEach(({ source, record }) => {
                            const value = record[field];

                            if (value !== undefined) {
                                // Check null values only for fields not in allowNullFields
                                if (value !== null || allowNullFields.includes(field)) {
                                    if (value !== null) {

                                        // Find the object with the matching IP address (value)
                                        const target = fieldValuesList.find(item => areValuesSame(item.value, value));
                                        
                                        // If the object is found, insert the source
                                        if (target) {
                                            // Check if the source is already in the sources array to avoid duplicates
                                            if (!target.sources.includes(source)) {
                                                target.sources.push(source);
                                            }
                                        } else {
                                            fieldValuesList.push( ({value: value, sources: [source]}) )
                                        }

                                    }
                                } else {
                                    missingCount++;
                                }
                            } else {
                                // Allow missing fields if specified
                                if (!allowMissingFields.includes(field)) {
                                    missingCount++;
                                }
                            }
                        });

                        const uniqueValuesCount = fieldValuesList.length;
                        const totalSources = entries.length;

                        // Determine if it's a mismatch, missing, or both
                        // if (uniqueValues.length > 1) {
                        if (uniqueValuesCount > 1) {
                            // Mismatch detected
                            details.push({
                                field,
                                type: "mismatch",
                                values: fieldValuesList,
                                // values: Object.entries(fieldValues).map(([value, sources]) => ({ value, sources })),
                                message: `${field.toUpperCase()} mismatch across sources`
                            });
                        }

                        if (missingCount > 0 && !allowMissingFields.includes(field) && missingCount < totalSources) {
                            // Missing values detected
                            details.push({
                                field,
                                type: "missing",
                                missingSources: entries.filter(e => !e.record[field]).map(e => e.source),
                                message: `${field.toUpperCase()} missing in some sources`
                            });
                        }

                        // if (uniqueValuesCount > 1 && missingCount > 0) {
                        // // if (uniqueValues.length > 1 && missingCount > 0) {
                        //     // Both mismatch and missing detected
                        //     details.push({
                        //         field,
                        //         values: fieldValuesList,
                        //         // values: Object.entries(fieldValues).map(([value, sources]) => ({ value, sources })),
                        //         missingSources: entries.filter(e => !e.record[field]).map(e => e.source),
                        //         message: `${field.toUpperCase()} mismatch and missing in some sources`
                        //     });
                        // }
                    }

                    if (details.length > 0) {
                        inconsistencies.push({
                            name,
                            type,
                            key,
                            sources: entries.map(e => e.source),
                            details
                        });
                    }
                }

                return inconsistencies;
            }

        """)
        
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
