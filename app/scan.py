# app/scan.py
import time
from threading import Thread
from flask_socketio import emit
from flask import current_app
from . import socketio, db
from .models import Scan
from datetime import datetime
import subprocess
import os
import json

def run_scan(app, scan_id):
    """
    Main function to run the web application scan as a subprocess.
    This function combines the logic from your two definitions.
    """
    with app.app_context():
        scan = Scan.query.get(scan_id)

        if not scan:
            print(f"❌ No scan found with ID {scan_id}")
            return

        # 1. Update the scan status to In Progress
        scan.start_time = datetime.utcnow()
        scan.status = "In Progress"
        # Initialize log_data to an empty string to avoid "None" type issues
        scan.log_data = ""
        db.session.commit()

        # Emit an initial "In Progress" message
        # Use a phase of 0 to indicate the start
        initial_message = "[⏳] Starting scan..."
        socketio.emit(
            f"scan_update_{scan_id}",
            {"phase": 0, "message": initial_message},
            namespace="/scan"
        )
        # Also save the initial message to the database
        scan.log_data += initial_message + "\n"
        db.session.commit()
        time.sleep(1)
        # 2. Build and run the scanner command
        # This is from your second `run_scan` definition.

        # 🔹 START OF CHANGES: Select the correct scanner script based on scan_type
        # Define a mapping from scan_type to script filename
        scanner_scripts = {
            "basic": "basic_scan.py",
            "lite": "lite_scan.py",
            "deep": "deep_scan.py",
        }
        script_name = scanner_scripts.get(scan.scan_type)

        if not script_name:
            # 🔹 Handle an unknown scan type gracefully
            error_message = f"[❌] Scan failed: Unknown scan type '{scan.scan_type}'"
            scan.status = "Failed"
            scan.end_time = datetime.utcnow()
            scan.log_data += error_message + "\n"
            db.session.commit()
            print(f"[ERROR] {error_message}")
            socketio.emit(
                f"scan_update_{scan_id}",
                {"phase": 4, "message": error_message},
                namespace="/scan"
            )
            return
        # 🔹 NEW: Gather all scan parameters into a dictionary
        scan_params = {
            "target_url": scan.target_url,
            "scan_id": scan.id,
            "scan_name": scan.scan_name,
            "scan_type": scan.scan_type,
            "environment": scan.environment,
            "auth_type": scan.auth_type,
            "username": scan.username,
            "password": scan.password,
            "token": scan.token,
            "cookies": scan.cookies,
            "is_paused": scan.is_paused
        }

        # 🔹 NEW: Serialize the dictionary to a JSON string
        json_data = json.dumps(scan_params)
        # 2. Build and run the scanner command with the correct script
        # 🔹 Pass the JSON string as a single argument
        cmd = ["python3", script_name, json_data]
        print(f"Running scan command: {cmd}")
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd="app",
                bufsize=1
            )

            # 3. Read the output from the subprocess line by line
            # This is also from your second definition.
            # We will use this to update the log in real-time.
            print(f"[DEBUG] Subprocess started for scan ID: {scan_id}")
            for line in process.stdout:
                line = line.strip()
                if line:
                    # Emit each log line over the socket.
                    # We can't know the "phase" from the subprocess output,
                    # so we will just emit the message.
                    # The client-side code will just display the log.
                    print(f"[DEBUG] Emitting log line: {line}")
                    socketio.emit(
                        f"scan_update_{scan_id}",
                        {"message": line},
                        namespace="/scan"
                    )
                    # 🔹 Save the log line to the database
                    scan.log_data += line + "\n"
                    db.session.commit()

            # Wait for the subprocess to complete
            process.wait()
            print(f"[DEBUG] Subprocess completed for scan ID: {scan_id}")

            # 4. Update the scan status to Completed
            final_message = "[✔] Scan completed."
            scan.status = "Completed"
            scan.end_time = datetime.utcnow()
            scan.log_data += final_message + "\n"
            db.session.commit()

            # Emit a final "completed" message with phase 4 for the progress bar
            socketio.emit(
                f"scan_update_{scan_id}",
                {"phase": 4, "message": "[✔] Scan completed."},
                namespace="/scan"
            )

        except Exception as e:
            # 5. Handle any errors during the subprocess execution
            error_message = f"[❌] Scan failed: {str(e)}"
            scan.status = "Failed"
            scan.end_time = datetime.utcnow()
            scan.log_data += error_message + "\n"
            db.session.commit()
            print(f"[ERROR] Scan failed for ID {scan_id}: {str(e)}")

            socketio.emit(
                f"scan_update_{scan_id}",
                {"phase": 4, "message": f"[❌] Scan failed: {str(e)}"},
                namespace="/scan"
            )

def start_scan_async(scan_id):
    """
    Starts the scan in a background thread to prevent blocking the Flask app.
    This function remains the same.
    """
    app = current_app._get_current_object()
    thread = Thread(target=run_scan, args=(app, scan_id))
    thread.daemon = True
    thread.start()
