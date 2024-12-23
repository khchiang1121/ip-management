from flask import Blueprint, render_template, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime, timezone
from flask_deprecate import deprecate_route
from models.server import Server, Source
from services import AlreadyExistError
from utils.database import servers_collection
from services.server import ServerService

server_bp = Blueprint('server_bp', __name__)

# ok
@server_bp.route("/", methods=["GET"])
def show_servers():
    """Get all servers."""

    server_service = ServerService()
    servers = server_service.get_all()
    if not servers:
        servers = []
    else:
        servers = [server.to_dict() for server in servers]

    return render_template('server.html', servers=servers)

# ok
@server_bp.route("/<string:server_id>", methods=["GET"])
def server_details(server_id):
    """Get all servers."""

    server_service = ServerService()
    server = server_service.find_network_inconsistencies(server_id)
    if not server:
        server = {}
    # else:
    #     server = server.to_dict()

    return render_template('server-details.html', server=server)

@server_bp.route("/network-inconsistencies", methods=["GET"])
def show_network_inconsistencies_servers():
    """Get all servers."""

    server_service = ServerService()
    servers =  server_service.find_network_inconsistencies_all()
    
    if servers is None:
        servers = []
    
    for server in servers:
        if "_id" in server:
            server["_id"] = str(server["_id"])

    return render_template('server-inconsistencies.html', servers=servers)
