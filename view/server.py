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

@server_bp.route("/ajax", methods=["GET"])
def show_servers_ajax():
    """Get all servers."""

    server_service = ServerService()
    # servers = server_service.get_all()
    
    # Get pagination parameters from the request
    page = int(request.args.get('page', 1))  # Default to page 1
    limit = int(request.args.get('limit', 10))  # Default to 10 items per page
    search = str(request.args.get('search[value]', None))  # Default to 10 items per page
    
    # Dynamically get the columns from the request
    columns = [request.args.get(f'columns[{i}][data]') for i in range(len(request.args)) if request.args.get(f'columns[{i}][data]')]

    # Convert the search parameters to a dictionary
    search_columns = {col: str(request.args.get(f'columns[{i}][search][value]', None)) for i, col in enumerate(columns)}

    # Fetch the data with pagination
    servers, total_count = server_service.get_paginated(page, limit, search, search_columns)
    if request.args.get('ajax'):  # Check if it's an AJAX request
        server_dicts = [server.to_dict() for server in servers] if servers else []
        return jsonify({
            "data": server_dicts,
            "recordsTotal": total_count,
            "recordsFiltered": total_count,
        })
        
    if not servers:
        servers = []
    else:
        servers = [server.to_dict() for server in servers]

    return render_template('server-ajax.html', servers=servers, total_count=total_count)

# ok
@server_bp.route("/<string:server_id>", methods=["GET", "POST"])
def server_details(server_id):
    """Get all servers."""

    server_service = ServerService()
    if request.method == "POST":
        # Process form submission
        data = request.form.to_dict()
        try:
            server_service.update(server_id, Server.from_dict(data))
            flash("Server update successfully")
            return redirect(url_for('server_bp.server_details', server_id=server_id))
        except Exception as e:
            flash("error: " + str(e))
            return redirect(url_for('server_bp.server_details', server_id=server_id))
        
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


