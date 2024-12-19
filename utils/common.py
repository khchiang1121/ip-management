from functools import wraps
import json

from flask import abort, jsonify
from flask_login import current_user

def pretty_print_json(data: str):
    print(json.dumps(data, indent=4))

def pretty_print_dict(data: dict):
    print(json.dumps(data, indent=4))

def role_required(required_role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not hasattr(current_user, 'role') or current_user.role != required_role:
                # return jsonify(message="Unauthorized"), 401
                abort(401)
            # if 'user_role' not in session or session['user_role'] != role:
            #     return redirect(url_for('login'))
            return func(*args, **kwargs)
        return wrapper
    return decorator