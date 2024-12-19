import json
import pandas as pd

# read JSON data from file
with open('fake_server_data_list.json') as f:
    data = json.load(f)

# Flatten networks
flattened_data = []
for entry in data:
    base_info = {k: v for k, v in entry.items() if k != "networks"}
    # base_info.pop('sources', None)
    if 'key' in base_info: del base_info['sources']

    flattened_entry = base_info.copy()
    for network in entry["networks"]:
        for net_key, net_value in network.items():
            if net_key in ["ip", "subnet_mask", "mac"]:
                flattened_entry[f"{network['name']}_{net_key}"] = net_value
    flattened_data.append(flattened_entry)

# Convert to DataFrame
df = pd.DataFrame(flattened_data)
df = df.drop('sources', axis=1)

# Write to Excel
df.to_excel("servers_networks.xlsx", index=False)

print("Data successfully written to servers_networks.xlsx")
