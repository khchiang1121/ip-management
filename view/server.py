from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
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

@server_bp.route("/<string:server_id>/edit", methods=["GET"])
def edit_server(server_id):
    """Get all servers."""

    server_service = ServerService()
    
    if request.method == "POST":
        # Process form submission
        data = request.form.to_dict()
        server_service.update(server_id, data)
        flash("Server updated successfully")
        return redirect(url_for('server_bp.server_details', server_id=server_id))
    
    server = server_service.find_network_inconsistencies(server_id)
    if not server:
        server = {}
    # else:
    #     server = server.to_dict()

    return render_template('server-details.html', server=server, edit_mode=True)


