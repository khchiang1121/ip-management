import os
import random
import shutil
from faker import Faker
import json
random.seed(9001)
Faker.seed(9001)
# Initialize Faker instance
fake = Faker()
last_updated = "2024-12-19T19:30:00.660+00:00"
# last_updated = fake.date_time_this_year().isoformat()

def delete_and_recreate_folder(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path):
        # Delete the folder and all of its contents
        shutil.rmtree(folder_path)
        print(f"'{folder_path}' and its contents have been deleted.")
    
    # Recreate the folder
    os.makedirs(folder_path)
    print(f"'{folder_path}' has been recreated.")
    
def generate_ip(range_type):
    """Generate a fake IP address based on the given range."""
    if range_type == 'data':
        return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    elif range_type == 'maas':
        return f"192.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
    elif range_type == 'admin':
        return f"11.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_cidrs(num_cidrs=1, ip_range=172, slash=random.randint(1, 31)):
    """Generate a list of fake CIDRs."""
    return [f"{ip_range}.{random.randint(0, 255)}.0.1/{slash}" for i in range(num_cidrs)]

def generate_mac():
    """Generate a fake MAC address."""
    return ':'.join(['{:02X}'.format(random.randint(0, 255)) for _ in range(6)])

def generate_cluster_id():
    envconfig_list = ['envconfig_c1', 'envconfig_c2', 'envconfig_c3']
    envconfig = random.choice(envconfig_list)
    return envconfig

def generate_fake_data():
    """Generate fake data in the given structure."""

    serial_number = fake.uuid4()

    # Generate IPs for the networks
    data_ip = generate_ip("data")
    maas_ip = generate_ip("maas")
    admin_ip = generate_ip("admin")

    data_mac = generate_mac()
    maas_mac = generate_mac()
    admin_mac = generate_mac()

    dc_list = ['DC1', 'DC2', 'DC3']
    room_list = ['R1', 'R2', 'R3']
    rack_list = ['A01', 'A02', 'B01']
    owner_list = ['user1', 'user2', 'user3']

    dc = random.choice(dc_list)
    room = random.choice(room_list)
    rack = random.choice(rack_list)
    unit = random.randint(1, 50)
    cluster_id = generate_cluster_id()
    envconfig = generate_cluster_id()
    owner = random.choice(owner_list)
    as_number = random.randint(64600, 64800)


    # Base structure
    data = {
        "server_id": serial_number,
        "hostname": "TW" + "-" + dc + "-" + room + "-" + rack + "-" + str(unit),
        "serial_number": serial_number,
        "location": "TW",
        "datacenter": dc,
        "room": room,
        "rack": rack,
        "unit": unit,
        "os": "ubuntu 22.04",
        "as_number": as_number,
        "owner": owner,
        "cluster_id": cluster_id,
        "env_config": cluster_id,
        "additional_info" : {
            "description": fake.sentence(),
        },
        "networks": [
            {
                "name": "data",
                "type": "ip",
                "ip": data_ip,
                "subnet_mask": "255.255.255.0",
                "mac": data_mac
            },
            {
                "name": "maas",
                "type": "ip",
                "ip": maas_ip,
                "subnet_mask": "255.255.255.0",
                "mac": maas_mac
            },
            {
                "name": "admin",
                "type": "ip",
                "ip": admin_ip,
                "subnet_mask": "255.255.255.0",
                "mac": admin_mac
            }
        ],
        "sources": {
            "Inventory": {
                "hostname": "TW" + "-" + dc + "-" + room + "-" + rack + "-" + str(unit),
                "serial_number": serial_number,
                "location": "TW",
                "datacenter": dc,
                "room": room,
                "rack": rack,
                "unit": unit,
                "os": "ubuntu 22.04",
                "as_number": as_number,
                "owner": owner,
                "cluster_id": cluster_id,
                "env_config": cluster_id,
                "networks": [
                    {
                        "name": "data",
                        "type": "ip",
                        "ip": data_ip,
                        "subnet_mask": "255.255.255.0",
                        "mac": data_mac
                    },
                    {
                        "name": "maas",
                        "type": "ip",
                        "ip": maas_ip,
                        "subnet_mask": "255.255.255.0",
                        "mac": maas_mac
                    },
                    {
                        "name": "admin",
                        "type": "ip",
                        "ip": admin_ip,
                        "subnet_mask": "255.255.255.0",
                        "mac": admin_mac
                    }
                ],
                "last_updated": last_updated
            },
            "MonitoringTool": {
                "networks": [
                    {
                        "name": "data",
                        "type": "ip",
                        "ip": data_ip,
                        "subnet_mask": "255.255.255.0",
                        "mac": data_mac
                    },
                    {
                        "name": "maas",
                        "type": "ip",
                        "ip": maas_ip,
                        "subnet_mask": "255.255.255.0",
                        "mac": maas_mac
                    },
                    {
                        "name": "admin",
                        "type": "ip",
                        "ip": admin_ip,
                        "subnet_mask": "255.255.255.0",
                        "mac": admin_mac
                    }
                ],
                "last_updated": last_updated
            }
        },
        "last_updated": last_updated
    }

    return data

def update_server_id(fake_data, server_id):
    fake_data['server_id'] = server_id
    fake_data['serial_number'] = server_id
    fake_data['sources']['Inventory']['serial_number'] = server_id
    return fake_data

def update_cluster_id(fake_data, cluster_id):
    fake_data['cluster_id'] = cluster_id
    fake_data['env_config'] = cluster_id
    fake_data['sources']['Inventory']['env_config'] = cluster_id
    return fake_data

fake_data_list = [generate_fake_data() for _ in range(100)]

# ===== Prepare for the output file ====
    
idx = 0
server_id = "test"
update_server_id(fake_data_list[idx], server_id)

idx+=1
server_id = "inventory-only-networks"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory'] = {key: value for key, value in fake_data_list[idx]['sources']['Inventory'].items() if key == 'networks'}

idx+=1
server_id = "rich-inventory"
update_server_id(fake_data_list[idx], server_id)

# ============
# Wrong ip, mac
# ============
# 要抓出來
idx+=1
server_id = "wrong-ip-in-inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['ip'] = "10.0.0.10"

# 要抓出來
idx+=1
server_id = "wrong-mask-in-Inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['subnet_mask'] = "255.1.2.3"

# ============
# missing a source
# ============
idx+=1
server_id = "missing-inventory-block"
update_server_id(fake_data_list[idx], server_id)
del fake_data_list[idx]['sources']['Inventory']

# ============
# missing a ip(name=data_ip) in networks
# ============
idx+=1
server_id = "missing-dataip-block-in-inventory"
update_server_id(fake_data_list[idx], server_id)
del fake_data_list[idx]['sources']['Inventory']['networks'][0]

# ============
# feild(key) is empty
# ============
# 要抓出來
idx+=1
server_id = "ip-empty-in-inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['ip'] = ""

# 要抓出來
idx+=1
server_id = "mac-empty-in-inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['mac'] = ""

# ============
# feild(key) is None
# ============
# 要抓出來
idx+=1
server_id = "ip-None-in-inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['ip'] = None

idx+=1
server_id = "mac-None-in-inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['mac'] = None

# ============
# feild(key) missing
# ============
# 要抓出來
idx+=1
server_id = "missing-ip-feild-in-inventory"
update_server_id(fake_data_list[idx], server_id)
del fake_data_list[idx]['sources']['Inventory']['networks'][0]['ip']

idx+=1
server_id = "missing-mac-feild-in-inventory"
update_server_id(fake_data_list[idx], server_id)
del fake_data_list[idx]['sources']['Inventory']['networks'][0]['mac']

# ============
# networks is None, empty list or missing
# ============
idx+=1
server_id = "networks-is-missing-in-Inventory"
update_server_id(fake_data_list[idx], server_id)
del fake_data_list[idx]['sources']['Inventory']['networks']

idx+=1
server_id = "networks-is-None-in-Inventory"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['networks'] = None

idx+=1
server_id = "networks-is-empty-list-in-truth"
update_server_id(fake_data_list[idx], server_id)
fake_data_list[idx]['networks'] = []



idx+=1
# Write the generated fake data to a JSON file
output_filename = "fake_server_data.json"
with open(output_filename, "w") as json_file:
    json.dump(fake_data_list[idx], json_file, indent=4)

delete_and_recreate_folder("./test_server_data")
# Write the generated fake data to a JSON file
output_filename = "fake_server_data_list.json"
with open(output_filename, "w") as json_file:
    json.dump(fake_data_list, json_file, indent=4)
    
for id, fake_data in enumerate(fake_data_list):
    if id < idx:
        # output to a single file
        output_filename = f"./test_server_data/{id}_{fake_data["server_id"]}.json"
        with open(output_filename, "w") as json_file:
            json.dump(fake_data, json_file, indent=4)
        # output to a list

print(f"{len(fake_data_list)} fake data entries have been written to {output_filename}")




















# Initialize Faker instance
fake = Faker()

def generate_fake_cluster_data():
    """Generate fake data in the given structure."""
    pod_cidrs = generate_cidrs(num_cidrs=2, ip_range=172, slash=16)
    service_cidrs = generate_cidrs(num_cidrs=1, ip_range=173, slash=17)
    native_routing_cidrs = generate_cidrs(num_cidrs=2, ip_range=174, slash=18)
    non_masquerade_private_cidrs = generate_cidrs(num_cidrs=1, ip_range=175, slash=19)
    l4lb_vip = generate_cidrs(num_cidrs=3, ip_range=10, slash=32)
    hostsubnets_cidrs = generate_cidrs(num_cidrs=2, ip_range=10, slash=32)
    
    cluster_list = ['c1', 'c2', 'c3']
    envconfig_list = ['envconfig_c1', 'envconfig_c2', 'envconfig_c3']
    owner_list = ['user1', 'user2', 'user3']

    cluster_id = random.choice(cluster_list)
    envconfig = random.choice(envconfig_list)
    cilium_cluster_id = random.randint(1, 20)

    # Base structure
    data = {
        "cluster_id": cluster_id,
        "env_config": cluster_id,
        "owners": owner_list,
        "cilium_cluster_id": cilium_cluster_id,
        "additional_info" : {
            "description": fake.sentence(),
        },
        "networks": [
            {
                "name": "pod_cidr",
                "type": "cidr",
                "cidrs": pod_cidrs
            },
            {
                "name": "service_cidr",
                "type": "cidr",
                "cidrs": service_cidrs
            },
            {
                "name": "native_routing_cidr",
                "type": "cidr",
                "cidrs": native_routing_cidrs
            },
            {
                "name": "non_masquerade_private_cidr",
                "type": "cidr",
                "cidrs": non_masquerade_private_cidrs
            },
            {
                "name": "l4lb_vip",
                "type": "cidr",
                "cidrs": l4lb_vip
            },
            {
                "name": "TW-DC1-R3-A02-15",
                "type": "hostsubnet",
                "hostname": "TW-DC1-R3-A02-15",
                "egress_cidrs": hostsubnets_cidrs,
                "egress_ips": [hostsubnets_cidrs[0]]
            }
        ],
        "sources": {
            "Inventory": {
                "env_config": cluster_id,
                "owners": owner_list,
                "cilium_cluster_id": cilium_cluster_id,
                "additional_info" : {
                    "description": fake.sentence(),
                },
                "networks": [
                    {
                        "name": "pod_cidr",
                        "type": "cidr",
                        "cidrs": pod_cidrs
                    },
                    {
                        "name": "service_cidr",
                        "type": "cidr",
                        "cidrs": service_cidrs
                    },
                    {
                        "name": "native_routing_cidr",
                        "type": "cidr",
                        "cidrs": native_routing_cidrs
                    },
                    {
                        "name": "non_masquerade_private_cidr",
                        "type": "cidr",
                        "cidrs": non_masquerade_private_cidrs
                    },
                    {
                        "name": "l4lb_vip",
                        "type": "cidr",
                        "cidrs": l4lb_vip
                    },
                    {
                        "name": "TW-DC1-R3-A02-15",
                        "type": "hostsubnet",
                        "hostname": "TW-DC1-R3-A02-15",
                        "egress_cidrs": hostsubnets_cidrs,
                        "egress_ips": [hostsubnets_cidrs[0]]
                    }
                ],
                "last_updated": last_updated
            },
            "MonitoringTool": {
                "networks": [
                    {
                        "name": "pod_cidr",
                        "type": "cidr",
                        "cidrs": pod_cidrs
                    },
                    {
                        "name": "service_cidr",
                        "type": "cidr",
                        "cidrs": service_cidrs
                    },
                    {
                        "name": "native_routing_cidr",
                        "type": "cidr",
                        "cidrs": native_routing_cidrs
                    },
                    {
                        "name": "non_masquerade_private_cidr",
                        "type": "cidr",
                        "cidrs": non_masquerade_private_cidrs
                    },
                    {
                        "name": "l4lb_vip",
                        "type": "cidr",
                        "cidrs": l4lb_vip
                    },
                    {
                        "name": "TW-DC1-R3-A02-15",
                        "type": "hostsubnet",
                        "hostname": "TW-DC1-R3-A02-15",
                        "egress_cidrs": hostsubnets_cidrs,
                        "egress_ips": [hostsubnets_cidrs[0]]
                    }
                ],
                "last_updated": last_updated
            }
        },
        "last_updated": last_updated
    }

    return data

# Generate 100 fake data entries
fake_data_list = [generate_fake_cluster_data() for _ in range(100)]


wrong_cidrs = generate_cidrs(num_cidrs=2, ip_range=99, slash=16)

idx = 0
cluster_id = "test"
update_cluster_id(fake_data_list[idx], cluster_id)

idx+=1
cluster_id = "inventory-only-contain-networks"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory'] = {key: value for key, value in fake_data_list[idx]['sources']['Inventory'].items() if key == 'networks'}

idx+=1
cluster_id = "rich-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)

# ============
# Wrong ip, mac
# ============
# 要抓出來
idx+=1
cluster_id = "wrong-pod-cidr-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['cidrs'] = wrong_cidrs

# 要抓出來
idx+=1
cluster_id = "wrong-hostsubnet-egress_cidrs-in-Inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][-1]['egress_cidrs'] = wrong_cidrs

# 要抓出來
idx+=1
cluster_id = "wrong-hostsubnet-egress_ips-in-Inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][-1]['egress_ips'] = [wrong_cidrs[0]]

# ============
# missing a source
# ============
idx+=1
cluster_id = "missing-inventory-block"
update_cluster_id(fake_data_list[idx], cluster_id)
del fake_data_list[idx]['sources']['Inventory']

# ============
# missing a ip(name=data_ip) in networks
# ============
idx+=1
cluster_id = "missing-some-data-block-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
del fake_data_list[idx]['sources']['Inventory']['networks'][0]
del fake_data_list[idx]['sources']['Inventory']['networks'][3]

# ============
# feild(key) is empty
# ============
# 要抓出來
idx+=1
cluster_id = "pod-cidrs-empty-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['cidrs'] = []

# 要抓出來
idx+=1
cluster_id = "egress-cidrs-empty-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][-1]['egress_cidrs'] = []

# ============
# feild(key) is None
# ============
idx+=1
cluster_id = "pod-cidrs-None-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][0]['cidrs'] = None

idx+=1
cluster_id = "egress_cidrs-None-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['sources']['Inventory']['networks'][-1]['egress_cidrs'] = None

# ============
# feild(key) missing
# ============
idx+=1
cluster_id = "missing-cidrs-feild-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
del fake_data_list[idx]['sources']['Inventory']['networks'][0]['cidrs']

idx+=1
cluster_id = "missing-egress_cidrs-feild-in-inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
del fake_data_list[idx]['sources']['Inventory']['networks'][-1]['egress_cidrs']

# ============
# networks is None, empty list or missing
# ============
idx+=1
cluster_id = "networks-is-missing-in-Inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
del fake_data_list[idx]['sources']['Inventory']['networks']

idx+=1
cluster_id = "networks-is-None-in-Inventory"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['networks'] = None

idx+=1
cluster_id = "networks-is-empty-list-in-truth"
update_cluster_id(fake_data_list[idx], cluster_id)
fake_data_list[idx]['networks'] = []

idx+=1
# Write the generated fake data to a JSON file
output_filename = "fake_cluster_data.json"
with open(output_filename, "w") as json_file:
    json.dump(fake_data_list[idx], json_file, indent=4)

delete_and_recreate_folder("./test_cluster_data")
# Write the generated fake data to a JSON file
output_filename = "fake_cluster_data_list.json"
with open(output_filename, "w") as json_file:
    json.dump(fake_data_list, json_file, indent=4)
    
for id, fake_data in enumerate(fake_data_list):
    if id < idx:
        # output to a single file
        output_filename = f"./test_cluster_data/{id}_{fake_data["cluster_id"]}.json"
        with open(output_filename, "w") as json_file:
            json.dump(fake_data, json_file, indent=4)
        # output to a list

print(f"{len(fake_data_list)} fake data entries have been written to {output_filename}")
