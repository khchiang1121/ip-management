from flask import Blueprint, render_template, request, jsonify
from services.cluster import ClusterService

cluster_bp = Blueprint('cluster_bp', __name__)

# ok
@cluster_bp.route("/", methods=["GET"])
def show_clusters():
    """Get all clusters."""

    cluster_service = ClusterService()
    clusters = cluster_service.get_all()
    if not clusters:
        clusters = []
    else:
        clusters = [cluster.to_dict() for cluster in clusters]

    return render_template('cluster.html', clusters=clusters)

# ok
@cluster_bp.route("/<string:cluster_id>", methods=["GET"])
def cluster_details(cluster_id):
    """Get all clusters."""

    cluster_service = ClusterService()
    cluster = cluster_service.find_network_inconsistencies(cluster_id)
    if not cluster:
        cluster = {}
    # else:
    #     cluster = cluster.to_dict()

    return render_template('cluster-details.html', cluster=cluster)

@cluster_bp.route("/network-inconsistencies", methods=["GET"])
def show_network_inconsistencies_clusters():
    """Get all clusters."""

    cluster_service = ClusterService()
    clusters =  cluster_service.find_network_inconsistencies_all()
    
    if clusters is None:
        clusters = []
    
    for cluster in clusters:
        if "_id" in cluster:
            cluster["_id"] = str(cluster["_id"])

    return render_template('cluster-inconsistencies.html', clusters=clusters)
