# BSSID.py
# The below script outputs a list of BSSIDs brodcast by each AP connected to a Cisco WLC (it will need to be adjusted to run on C9800 WLCs). 
# By parsing AP names and Location from "show ap summary" output.
# It then runs the "show ap wlan <802.11a & 802.11b> <AP Name>" for each AP Name and parses each BSSID for each radio, for each SSID interface.
# Finally exporting parsed dats to .csv format. 




import csv
from genie.testbed import load
from unicon.core.errors import ConnectionError
import re

# Load testbed
testbed = load('testbedWLC.yml')
device = testbed.devices['Cisco Controller']

try:
    print("Connecting to WLC...")
    device.connect()
except ConnectionError as e:
    print(f"Connection failed: {e}")
    exit()

# Step 1: Get AP names
print("Fetching AP summary...")
ap_summary = device.execute('show ap summary')

ap_names = []
ap_locations = {}

for line in ap_summary.splitlines():
    match = re.match(
    r'^(?P<ap_name>\S+)\s+\d+\s+\S+\s+\S+\s+(?P<location>\S+)\s+\S+\s+\S+\s+\d+\s+\[.*\]$',
    line.strip()
)
    if match:
        ap_name = match.group('ap_name')
        location = match.group('location').strip()
        ap_names.append(ap_name)
        ap_locations[ap_name] = location

if not ap_names:
    print("No APs found.")
    exit()

# Step 2: Collect data
ap_data = []

def parse_wlan_table(output):
    entries = []
    for line in output.splitlines():
        if re.match(r'^\d+\s+', line):
            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 3:
                interface = parts[1]
                bssid = parts[2]
                entries.append((interface, bssid))
    return entries

for ap in ap_names:
    print(f"\nProcessing AP: {ap}")

    for band in ['802.11a', '802.11b']:
        print(f"  → Checking {band}...")
        cmd = f"show ap wlan {band} {ap}"
        output = device.execute(cmd)

        entries = parse_wlan_table(output)

        for interface, bssid in entries:
            ap_data.append({
                "AP Name": ap,
                "Band": band,
                "Interface Name": interface,
                "BSSID": bssid,
                "Location": ap_locations.get(ap, "")
    })

# Step 3: Export to CSV
csv_file = "bssid.csv"
print(f"\n📁 Writing results to {csv_file}...")

with open(csv_file, mode='w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=["AP Name", "Location", "Band", "Interface Name", "BSSID"])
    writer.writeheader()
    writer.writerows(ap_data)

print("✅ Export complete.")

