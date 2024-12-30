from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime, timezone
from flask_deprecate import deprecate_route
from models.server import Server, Source
from services import AlreadyExistError
from utils.database import servers_collection
from services.server import ServerService

server_api = Blueprint('server_api', __name__)

# okk
@server_api.route("/", methods=["GET"])
def get_servers():
    """Get all servers."""
    server_service = ServerService()
    servers = server_service.get_all()
    if not servers:
        return jsonify({"error": "No server found"}), 404
    return jsonify([server.to_dict() for server in servers]), 200

# okk
@server_api.route("/<string:server_id>", methods=["GET"])
def get_server(server_id):
    """Get a single server by ID."""
    server_service = ServerService()
    server = server_service.get(server_id)
    if not server:
        return jsonify({"error": "Server not found"}), 404
    return jsonify(server.to_dict()), 200

# okk
@server_api.route("/", methods=["POST"])
def create_server():
    """Create a new server."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        server = Server.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400

    try:
        server_service = ServerService()    
        created_server_id = server_service.create(server)
    except AlreadyExistError as e:
        return jsonify({"error": f"Failed to create server: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create server: {str(e)}"}), 500

    return jsonify({"message": "Server created", "id": str(created_server_id)}), 201

# okk
@server_api.route("/<string:server_id>", methods=["PUT"])
def upsert_server(server_id):
    """Update a server by ID."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        server = Server.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400
    
    try:
        server_service = ServerService()    
        existing_server = server_service.get(server_id)
        create = existing_server is None
        result_server_id, _ = server_service.upsert(server_id = server_id, server = server)
    except Exception as e:
        return jsonify({"error": f"Failed to update server: {str(e)}"}), 500

    if create:
        return jsonify({"id": result_server_id, "message": "Server created"}), 201
    else:
        return jsonify({"id": result_server_id, "message": "Server updated"}), 200

# okk
@server_api.route("/<string:server_id>", methods=["PATCH"])
def patch_server(server_id):
    """Update a server by ID."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        server = Server.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400
    
    try:
        server_service = ServerService()    
        existing_server = server_service.get(server_id)
        create = existing_server is None
        result_server_id = server_service.patch(server_id, server)
    except Exception as e:
        return jsonify({"error": f"Failed to update server: {str(e)}"}), 500

    if create:
        return jsonify({"id": result_server_id, "message": "Server created"}), 201
    else:
        return jsonify({"id": result_server_id, "message": "Server updated"}), 200

# okk
@server_api.route("/<string:server_id>", methods=["DELETE"])
def delete_server(server_id):
    """Delete a server by ID."""
    server_service = ServerService()
    result = server_service.delete(server_id)
    if not result:
        return jsonify({"error": "Server not found"}), 404
    return jsonify({"message": "Server deleted"}), 200

# okk
@server_api.route("/network-inconsistencies", methods = ['GET'])
def get_ip_inconsistencies():
    server_service = ServerService()
    inconsistencies =  server_service.find_network_inconsistencies_all()
    
    if inconsistencies is None:
        return jsonify([]), 200
    
    for instance in inconsistencies:
        if "_id" in instance:
            instance["_id"] = str(instance["_id"])

    return jsonify(inconsistencies), 200

# okk
@server_api.route("<string:server_id>/network-inconsistencies", methods = ['GET'])
def get_server_ip_inconsistencies(server_id):
    server_service = ServerService()
    inconsistency =  server_service.find_network_inconsistencies(server_id)
    
    if inconsistency is None:
        return jsonify({}), 200
    
    if "_id" in inconsistency:
        inconsistency["_id"] = str(inconsistency["_id"])

    return jsonify(inconsistency), 200

# ------------------------------
# Deprecated API
# ------------------------------
@server_api.route("/batch", methods=["PUT"])
def batch_update_servers():
    """Batch update servers."""
    data = request.json  # Expects a list of server updates
    for update in data:
        server_id = update.pop("_id", None)
        if server_id:
            servers_collection.update_one({"_id": ObjectId(server_id)}, {"$set": update})
    return jsonify({"message": "Batch update completed"}), 200

@server_api.route("/<string:server_id>/sources/<string:source_name>", methods=["PUT"])
def update_source(server_id, source_name):
    """Create or update data for a single source."""
    server_service = ServerService()
    data = request.json
    server = server_service.get(server_id)
    if not server:
        return jsonify({"error": "Server not found"}), 404

    source = Source.from_dict(data)
    server_service.create_or_update_source(server_id, source_name, source)

    return jsonify({"message": "Source created or updated"}), 200

@server_api.route("/batch/<string:source_name>", methods=["PUT"])
def batch_update_source(source_name):
    """Batch update data of a source."""
    server_service = ServerService()
    data = request.json  # Expects a list of updates for a specific source
    for update in data:
        server_id = update.pop("server_id", None)
        if not server_id:
            continue

        server = server_service.get(server_id)
        if not server:
            continue

        # Check if the source exists in the dictionary
        sources = server.get("sources", {})
        if source_name in sources:
            sources[source_name]["networks"] = update.get("networks", sources[source_name]["networks"])
            sources[source_name]["last_updated"] = datetime.now(timezone.utc).isoformat()
            servers_collection.update_one({"_id": ObjectId(server_id)}, {"$set": {"sources": sources}})

    return jsonify({"message": "Batch source update completed"}), 200
