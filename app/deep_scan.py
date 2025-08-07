# your_scanner.py
import sys
import json
from importlib import import_module
from pathlib import Path
import subprocess
import os

def dispatch_scan(scan_data):
    """
    This is the main function that performs the actual scanning logic.
    It receives the scan parameters as a dictionary.
    """
    target_url = scan_data["target_url"]
    scan_id = scan_data["scan_id"]
    scan_name = scan_data["scan_name"]
    scan_type = scan_data["scan_type"]
    environment = scan_data["environment"]
    auth_type = scan_data["auth_type"]
    username = scan_data["username"]
    password = scan_data["password"]
    token = scan_data["token"]
    cookies = scan_data["cookies"]
    
    # Convert dictionary to JSON string
    scan_json = json.dumps(scan_data)
    #print("ping pong dude")
    # Build command to run the other script
    cmd = [
        "python3",
        os.path.join("scan/deep", "main.py"),
        scan_json
    ]
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        print(stdout)
        if stderr:
            print("[Error from basic_scan.py]:", stderr)

    except Exception as e:
        print(f"[❌] Failed to run basic scan: {e}")

    
if __name__ == "__main__":
    # 🔹 The first argument is the script name, the second is our JSON string.
    if len(sys.argv) > 1:
        json_data = sys.argv[1]
        try:
            # 🔹 Parse the JSON string back into a Python dictionary
            scan_params = json.loads(json_data)
            dispatch_scan(scan_params)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON data: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("No scan data provided.", file=sys.stderr)
        sys.exit(1)


