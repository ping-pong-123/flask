import sys
import json

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            scan_data = json.loads(sys.argv[1])
            print(f"✅ Basic scan started for {scan_data['target_url']}")
            #print(f"Scan Type: {scan_data['scan_type']}")
            #print(f"Auth Type: {scan_data['auth_type']}")
            # ... do actual scanning here ...
            print("✅ Basic scan completed.pingpong")
        except Exception as e:
            print(f"[❌] Error in basic scan: {e}")
    else:
        print("❌ No scan data received.")