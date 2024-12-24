from flask import Blueprint, request, jsonify
from flask_deprecate import deprecate_route
from models.cluster import Cluster
from services import AlreadyExistError
from services.cluster import ClusterService

cluster_api = Blueprint('cluster_api', __name__)

# okk
@cluster_api.route("/", methods=["GET"])
def get_clusters():
    """Get all cluster."""
    cluster_service = ClusterService()
    clusters = cluster_service.get_all()
    if not clusters:
        return jsonify({"error": "No cluster found"}), 404
    return jsonify([cluster.to_dict() for cluster in clusters]), 200

# okk
@cluster_api.route("/<string:cluster_id>", methods=["GET"])
def get_cluster(cluster_id):
    """Get a single cluster by ID."""
    cluster_service = ClusterService()
    cluster = cluster_service.get(cluster_id)
    if not cluster:
        return jsonify({"error": "Cluster not found"}), 404
    return jsonify(cluster.to_dict()), 200

# okk
@cluster_api.route("/", methods=["POST"])
def create_cluster():
    """Create a new cluster."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        cluster = Cluster.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400

    try:
        cluster_service = ClusterService()    
        created_id = cluster_service.create(cluster)
    except AlreadyExistError as e:
        return jsonify({"error": f"Failed to create cluster: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to create cluster: {str(e)}"}), 500

    return jsonify({"message": "Cluster created", "id": str(created_id)}), 201

# okk
@cluster_api.route("/<string:cluster_id>", methods=["PUT"])
def upsert_cluster(cluster_id):
    """Update a cluster by ID."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        cluster = Cluster.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400
    
    try:
        cluster_service = ClusterService()    
        existing_cluster = cluster_service.get(cluster_id)
        create = existing_cluster is None
        result_id, _ = cluster_service.upsert(cluster_id, cluster)
    except Exception as e:
        return jsonify({"error": f"Failed to update cluster: {str(e)}"}), 500

    if create:
        return jsonify({"id": result_id, "message": "Cluster created"}), 201
    else:
        return jsonify({"id": result_id, "message": "Cluster updated"}), 200

# okk
@cluster_api.route("/<string:cluster_id>", methods=["PATCH"])
def patch_cluster(cluster_id):
    """Update a cluster by ID."""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        cluster = Cluster.from_dict(data)
    except Exception as e:
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400
    
    try:
        cluster_service = ClusterService()    
        existing_cluster = cluster_service.get(cluster_id)
        create = existing_cluster is None
        result_id = cluster_service.patch(cluster_id, cluster)
    except Exception as e:
        return jsonify({"error": f"Failed to update cluster: {str(e)}"}), 500

    if create:
        return jsonify({"id": result_id, "message": "Cluster created"}), 201
    else:
        return jsonify({"id": result_id, "message": "Cluster updated"}), 200

# okk
@cluster_api.route("/<string:cluster_id>", methods=["DELETE"])
def delete_cluster(cluster_id):
    """Delete a cluster by ID."""
    cluster_service = ClusterService()
    result = cluster_service.delete(cluster_id)
    if not result:
        return jsonify({"error": "Cluster not found"}), 404
    return jsonify({"message": "Cluster deleted"}), 200

# okk
@cluster_api.route("/network-inconsistencies", methods = ['GET'])
def get_ip_inconsistencies():
    cluster_service = ClusterService()
    inconsistencies =  cluster_service.find_network_inconsistencies_all()
    
    if inconsistencies is None:
        return jsonify([]), 200
    
    for instance in inconsistencies:
        if "_id" in instance:
            instance["_id"] = str(instance["_id"])

    return jsonify(inconsistencies), 200

# okk
@cluster_api.route("<string:cluster_id>/network-inconsistencies", methods = ['GET'])
def get_cluster_ip_inconsistencies(cluster_id):
    cluster_service = ClusterService()
    inconsistency =  cluster_service.find_network_inconsistencies(cluster_id)
    
    if inconsistency is None:
        return jsonify({}), 200
    
    if "_id" in inconsistency:
        inconsistency["_id"] = str(inconsistency["_id"])

    return jsonify(inconsistency), 200

# ------------------------------
# Deprecated API
# ------------------------------
@cluster_api.route("/<string:cluster_id>/sources/<string:source_name>", methods=["PUT"])
@deprecate_route
def update_source2(cluster_id, source_name):
    """Create or update data for a single source."""
    cluster_service = ClusterService()
    data = request.json
    existing_cluster = cluster_service.get_cluster(cluster_id)
    if not existing_cluster:
        return jsonify({"error": "Cluster not found"}), 404

    # Check if the source exists in the dictionary
    sources = existing_cluster.get("sources", {})
    if source_name not in sources:
        existing_cluster.add_source(source_name, data)
    else:
        existing_cluster.add_source(source_name, data)

    cluster_service.update_cluster(existing_cluster)
    return jsonify({"message": "Source created or updated"}), 200
