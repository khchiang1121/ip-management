import json
import os
from pathlib import Path
import requests

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def read_all_json_files(folder_path):
    data = {}  # A list to store the parsed contents of all JSON files
    folder = Path(folder_path)  # Create a Path object for the folder path

    if folder.exists() and folder.is_dir():
        # Use pathlib to iterate over all JSON files in the folder
        for json_file in folder.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as file:
                    # Load and parse each JSON file
                    json_data = json.load(file)
                    data[json_file]=json_data
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
    else:
        print(f"The folder '{folder_path}' does not exist or is not a directory.")
    
    return data

def send_request(url, data):
    response = requests.get(url, json=data)
    return response.json()

def store_response(response, file_path):
    with open(file_path, 'w') as file:
        json.dump(response, file, indent=4)
        
def main():
    # Read the JSON file
    file_path = './test_data'
    datas = read_all_json_files(file_path)
    for file, data in datas.items():
        # Send the POST request for each entry in the JSON file
        url = f'http://127.0.0.1:8100/api/servers/{data['server_id']}/ip-inconsistencies'
        response = send_request(url, data)
        store_response(response, f'test_response_data/{os.path.basename(file)}.json')
            
if __name__ == "__main__":
        main()