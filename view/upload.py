import json
from flask import Flask, jsonify, render_template, request, session, url_for, redirect, Blueprint, flash,send_from_directory,send_file
from pymongo import UpdateOne
from flask_login import login_required,LoginManager,login_user, logout_user,UserMixin,current_user
import datetime
import os
import pandas as pd
import xlsxwriter
from io import BytesIO
from utils.database import servers_collection
from flask_session import Session
from models.server import Server, IPNetwork, Source

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = set(['csv','xlsx'])
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@upload_bp.route("/", methods = ['POST','GET'])
def upload():
    if request.method == 'POST':
        display_result=""
        #現在時間
        now = datetime.datetime.now()

        #取得上傳檔案
        file = request.files.get('file', None)#https://stackoverflow.com/questions/53240205/request-files-400-bad-request-in-flask

        if file and allowed_file(file.filename): 
            try:
                df = pd.read_excel(file)                 
                # df = df.replace({np.nan: None})
                if_success = None
            except Exception as e:
                if_success = False
                display_result+=("資料格式不正確，請重新檢查資料。【" + str(type(e).__name__)  + "】\n")
            # ================ 資料新增 ================
            if if_success is not False:
                uploaded_data = {
                    'columns': df.columns.tolist(),
                    'data': df.to_dict(orient='records')
                }
                session['uploaded_data'] = {
                    'columns': df.columns.tolist(),
                    'data': df.to_dict(orient='records')
                }
                return render_template('select_column.html', if_success = if_success, display_result = display_result, columns=uploaded_data['columns'], data=uploaded_data['data'])
        else:
            if_success = False
            display_result+="Invalid file format. Please upload an Excel file.【未上傳檔案或副檔名不正確】\n"

        # display error message
        return render_template('upload.html', if_success=if_success, display_result = display_result)
    return render_template('upload.html')

# ok
@upload_bp.route('/process_mapping', methods=['POST'])
def process_mapping():
    try:
        column_mapping = request.form.get('column_mappings')
        print(json.dumps(column_mapping, indent=4))
        
        if column_mapping:
            if not isinstance(column_mapping, dict):
                column_mapping = json.loads(column_mapping)
        else:
            return jsonify({"error": "No mapping data found. Please re-upload the file."}), 400
        
        uploaded_data = session.get('uploaded_data')
        if uploaded_data:
            if not isinstance(uploaded_data, dict):
                uploaded_data = json.loads(uploaded_data)
        else:
            return jsonify({"error": "No uploaded data found. Please re-upload the file."}), 400

        # Map the columns based on user input and convert to database schema format
        formatted_data = process_uploaded_data_inventory_handbook(uploaded_data, column_mapping, "inventory_handbook")

        # Insert formatted data into MongoDB
        servers = []
        if formatted_data:
            upsert_multiple_servers(formatted_data)
            servers = [ server.to_dict() for server in formatted_data]


        # Clear session data after successful insertion
        session.pop('uploaded_data', None)

        # Return success response
        # return jsonify({"message": "Data successfully inserted into the database.", "inserted_count": len(formatted_data)})
        return render_template('show.html', servers=servers)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Map the columns based on user input and convert to database schema format
def process_uploaded_data_inventory_handbook(uploaded_data, column_mapping, source_name="inventory_handbook"):
    formatted_data = []
    if uploaded_data['data']:
        for row in uploaded_data['data']:
            server = Server(
                server_id=row.get(column_mapping.get("server_id", "")),
                hostname=row.get(column_mapping.get("hostname", None)),
                serial_number=row.get(column_mapping.get("serial_number", None)),
                location=row.get(column_mapping.get("location", None)),
                datacenter=row.get(column_mapping.get("datacenter", None)),
                room=row.get(column_mapping.get("room", None)),
                rack=row.get(column_mapping.get("rack", None)),
                unit=row.get(column_mapping.get("unit", None)),
                os=row.get(column_mapping.get("os", "Unknown")),
                owner=row.get(column_mapping.get("owner", None)),
                cluster_id=row.get(column_mapping.get("cluster_id", None)),
                env_config=row.get(column_mapping.get("env_config", None)),
                networks=[],  # Initialize empty; add networks later
                sources={
                    source_name: Source(
                        networks=[
                            IPNetwork(
                                name="data",
                                type="ip",
                                ip=row.get(column_mapping.get("data_ip", None)),
                                subnet_mask=row.get(column_mapping.get("data_subnet_mask", None)),
                                mac=row.get(column_mapping.get("data_mac", None)),
                            ),
                            IPNetwork(
                                name="maas",
                                type="ip",
                                ip=row.get(column_mapping.get("maas_ip", None)),
                                subnet_mask=row.get(column_mapping.get("maas_subnet_mask", None)),
                                mac=row.get(column_mapping.get("maas_mac", None)),
                            ),
                            IPNetwork(
                                name="admin",
                                type="ip",
                                ip=row.get(column_mapping.get("admin_ip", None)),
                                subnet_mask=row.get(column_mapping.get("admin_subnet_mask", None)),
                                mac=row.get(column_mapping.get("admin_mac", None)),
                            ),
                        ],
                    )
                }
            )
            formatted_data.append(server)
    return formatted_data

def upsert_multiple_servers(server_data_list: list[Server]):

    bulk_operations = []
    if server_data_list:
        for server_data in server_data_list:
            server_id = server_data.server_id

            # Define the update operation
            update_query = {"server_id": server_id}

            update_operations = []
            server_data = server_data.to_dict()
            # Add fields to $set only if they exist in the input data
            set_operations = {"$set": {}}
            for field in server_data.keys():
                if field in server_data and server_data[field] is not None and field not in ["server_id", "sources", "networks"]:
                    set_operations["$set"][field] = server_data[field]

            # Handle sources with $mergeObjects
            if "sources" in server_data and server_data["sources"]:
                set_operations["$set"]["sources"] = {
                    "$mergeObjects": [
                        "$sources",
                        server_data['sources']
                    ]
                }        

            if set_operations["$set"]:
                update_operations.append(set_operations)
            
            # Add the operation to bulk_operations
            bulk_operations.append(
                UpdateOne(filter = update_query, update = update_operations, upsert=True),
            )

    # Perform the bulk write
    if bulk_operations:
        try:
            result = servers_collection.bulk_write(bulk_operations)
            print(f"Bulk operation completed: {result.bulk_api_result}")
        except Exception as e:
            print(f"Error during bulk operation: {e}")
    else:
        print("No operations to perform.")

    processed_data = session.get('processed_data')
    if not processed_data:
        return redirect(url_for('upload.upload'))
    return render_template('result.html', data=processed_data)
