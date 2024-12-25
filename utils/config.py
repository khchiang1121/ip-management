from configparser import ConfigParser
import os

# =============================================================================
# Load configuration from ini file
# =============================================================================
config = ConfigParser()
config.read('config.ini', encoding='utf-8')

# Database connection details
mongo_uri = os.environ.get("MONGO_URI", config.get('database', 'mongo_uri', fallback = None))
mongo_database = os.environ.get("MONGO_DATABASE", config.get('database', 'mongo_database', fallback = None))
mongo_userame = os.environ.get("MONGO_USERNAME", config.get('database', 'mongo_username', fallback = None))
mongo_password = os.environ.get("MONGO_PASSWORD", config.get('database', 'mongo_password', fallback = None))

mongo_servers_collection = config.get('database', 'servers_collection', fallback="servers")
mongo_clusters_collection = config.get('database', 'clusters_collection', fallback="clusters")
mongo_cilium_collection = config.get('database', 'cilium_collection', fallback="cilium")


_flask_port_str = os.environ.get("FLASK_PORT", config.get('flask', 'port', fallback = None))
flask_port = int(_flask_port_str) if _flask_port_str else None
flask_admin_user = os.environ.get("FLASK_ADMIN_USER", config.get('flask', 'admin_user', fallback = None))
flask_admin_password = os.environ.get("FLASK_ADMIN_PASSWORD", config.get('flask', 'admin_password', fallback = None))
