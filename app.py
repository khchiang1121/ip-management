import os
import bcrypt
from flask import Flask, jsonify, render_template, request, url_for, redirect, Blueprint, flash,send_from_directory,send_file
import os
import json
import jinja2
import os
from services.cluster import ClusterService
from services.server import ServerService
from utils.notify import *
from flask_session import Session
from utils.config import flask_port, flask_admin_user, flask_admin_password
from view.auth import login_manager
from dotenv import load_dotenv
load_dotenv()

env = jinja2.Environment()
env.globals.update(zip=zip)

# =============================================================================
# init Flask and inject new variables
# =============================================================================
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(16)
app.jinja_env.filters['zip'] = zip
app.jinja_env.add_extension('jinja2.ext.do')

Session(app)
login_manager.init_app(app)

# =============================================================================
# Flask blueprint
# =============================================================================
# 登入相關
from view.auth import auth_bp
app.register_blueprint(auth_bp)

# 上傳檔案
from view.upload import(upload_bp)
app.register_blueprint(upload_bp, url_prefix="/upload")

# Server API
from view.server_api import(server_api)
app.register_blueprint(server_api, url_prefix="/api/servers")
from view.server import(server_bp)
app.register_blueprint(server_bp, url_prefix="/servers")

# Cluster API
from view.cluster_api import(cluster_api)
app.register_blueprint(cluster_api, url_prefix="/api/clusters")
from view.cluster import(cluster_bp)
app.register_blueprint(cluster_bp, url_prefix="/clusters")
# =============================================================================
# Flask route
# =============================================================================
@app.route("/", methods = ['GET'])
def index():
    # return redirect(url_for('upload.upload'))
    cluster_service = ClusterService()
    server_service = ServerService()
    cluster_count = cluster_service.count()
    server_count = server_service.count()
    server_inconsistencies_count = len(server_service.find_network_inconsistencies_all())
    cluster_inconsistencies_count = len(cluster_service.find_network_inconsistencies_all())
    return render_template('index.html', server_count=server_count, cluster_count = cluster_count, server_inconsistencies_count = server_inconsistencies_count, cluster_inconsistencies_count = cluster_inconsistencies_count),200

# =============================================================================
# Flask handler
# =============================================================================
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api"):
        response = {
            "message":  "The requested resource does not exist.",
            "error": str(error)
        }
        return jsonify(response), 404
    return render_template('404.html'),404, {"Refresh": "1; url=/"}

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith("/api"):
        response = {
            "message": "Something went wrong on the server. Please try again later.",
            "error": str(error)
        }
        return jsonify(response), 500
    return render_template('500.html'),500, {"Refresh": "1; url=/"}

@app.errorhandler(401)
def unauthorized(error):
    if request.path.startswith("/api"):
        response = {
            "message": "Unauthorized access.",
            "error": str(error)
        }
        return jsonify(response), 401
    return render_template('401.html'),401, {"Refresh": "1; url=/"}

def initialize_app():
    # Custom initialization logic
    print("Custom initialization before first request")
    # Define the path to the member file
    file_path = './member.json'
    
    # Check if the file exists, if not create it with a default structure
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        hashed_password = bcrypt.hashpw(flask_admin_password.encode('utf-8'), bcrypt.gensalt())
        default_data = {
            flask_admin_user: {
                "password": hashed_password.decode('utf-8'),
                "role": "Admin"
            }
        }
        with open(file_path, 'w') as file:
            json.dump(default_data, file, indent=4)
    
@app.before_request
def before_request():
    # 檢查路由，初始化的路由不需要重新導向
    if request.path == "/login":
        return
    if request.path.startswith("/static"):
        return
    return None

with app.app_context():
    initialize_app()

if __name__ == "__main__":
    app.run(port = flask_port, host = "0.0.0.0", debug = True)
