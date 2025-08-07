# your_scanner.py
import sys
import json
from importlib import import_module
from pathlib import Path
import subprocess
import os

def dispatch_scan(scan_data):
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
        os.path.join("scan/basic", "main.py"),
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

"""
# your_scanner.py
import sys
import json
import subprocess
import os
import time
from pathlib import Path # 🔹 NEW: Import Path for robust path handling

# 🔹 FIX: Add the 'app' directory (where this script resides) to sys.path
# This ensures that 'app.models' can be imported correctly.
# Path(__file__).parent gets the directory of the current file (e.g., /path/to/project_root/app)
sys.path.append(str(Path(__file__).parent.resolve()))

# 🔹 Import Flask and SQLAlchemy components to allow this subprocess to connect to DB
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.models import Scan # Import your Scan model

# 🔹 Set up a temporary Flask app and database context for this subprocess
_temp_app = Flask(__name__)
_temp_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db' # IMPORTANT: Ensure this matches your main app's DB URI
_temp_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
_db = SQLAlchemy(_temp_app) # Use a local db instance for the subprocess

def dispatch_scan(scan_data):
    
    #This function now acts as the main scan runner. It launches a sub-scanner
    #(e.g., basic/main.py) and periodically checks for the scan's pause status
    #in the database, pausing execution if required.
    
    scan_id = scan_data["scan_id"] # We need the scan_id to query the database
    scan_type = scan_data["scan_type"] # To determine which sub-scanner to run

    # Convert dictionary to JSON string to pass to the sub-scanner
    scan_json = json.dumps(scan_data)
    
    # Build command to run the other script (e.g., scan/basic/main.py)
    # 🔹 Ensure the path to your sub-scanner is correct relative to where your_scanner.py is executed
    # If your_scanner.py is in 'app/' and scan/basic/main.py is in 'app/scan/basic/'
    # then the path from your_scanner.py to main.py is 'scan/basic/main.py'
    sub_scanner_script = os.path.join("scan", scan_type, "main.py")
    cmd = [
        "python3",
        sub_scanner_script,
        scan_json
    ]
    
    print(f"Launching sub-scanner: {cmd}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1 # Line-buffered output
        )

        with _temp_app.app_context():
            _db.init_app(_temp_app)
            _db.create_all()

            print(f"[DEBUG] Subprocess started for scan ID: {scan_id}")
            
            while True:
                line = process.stdout.readline()
                
                if not line and process.poll() is not None:
                    break
                
                current_scan = Scan.query.get(scan_id)
                if current_scan and current_scan.is_paused:
                    print(f"Scan {scan_id} paused by user. Waiting to resume...", file=sys.stderr)
                    while True:
                        time.sleep(2) # Check every 2 seconds to avoid excessive database hits
                        current_scan = Scan.query.get(scan_id)
                        if current_scan and not current_scan.is_paused:
                            print(f"Scan {scan_id} resumed. Continuing...", file=sys.stderr)
                            break
                        elif not current_scan: # Scan might have been deleted while paused
                            print(f"Scan {scan_id} no longer exists. Exiting.", file=sys.stderr)
                            sys.exit(0)

                if line:
                    sys.stdout.write(line)
                    sys.stdout.flush()

            process.wait()
            print(f"[DEBUG] Subprocess completed for scan ID: {scan_id}")

    except Exception as e:
        print(f"[❌] Failed to run scan: {e}", file=sys.stderr)
        with _temp_app.app_context():
            _db.init_app(_temp_app)
            _db.create_all()
            scan = Scan.query.get(scan_id)
            if scan:
                scan.status = "Failed"
                _db.session.commit()
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        json_data = sys.argv[1]
        try:
            scan_params = json.loads(json_data)
            dispatch_scan(scan_params)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON data: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("No scan data provided.", file=sys.stderr)
        sys.exit(1)"""
