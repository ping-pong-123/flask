from pprint import pprint
import time
from zapv2 import ZAPv2
import subprocess

# --- CONFIG ---
ZAP_PATH = r"/usr/bin/zaproxy"  # path to zaproxy binary or /usr/share/zaproxy/zap.sh
API_KEY = "pc0dcb1qlk7ndcdm5e40c308mg"  # your API key from ZAP Options->API
ZAP_ADDRESS = "127.0.0.1"
ZAP_PORT = "8090"  # proxy port

# --- START ZAP DAEMON ---
print("[*] Starting OWASP ZAP...")
zap_proc = subprocess.Popen(
    [ZAP_PATH, "-daemon", "-port", ZAP_PORT, "-host", ZAP_ADDRESS, "-config", "api.disablekey=false"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
time.sleep(10)  # wait for ZAP to fully start

# --- CONNECT TO ZAP ---
zap = ZAPv2(
    apikey=API_KEY,
    proxies={
        "http": f"http://{ZAP_ADDRESS}:{ZAP_PORT}",
        "https": f"http://{ZAP_ADDRESS}:{ZAP_PORT}",
    },
)

print("[*] OWASP ZAP started.")
print(f"[*] Proxy running on {ZAP_ADDRESS}:{ZAP_PORT}")

# --- START A FRESH SESSION ---
zap.core.new_session(name="fresh", overwrite=True, apikey=API_KEY)
print("[*] Started a fresh session (no previous logs).")

# --- OPEN BUILT-IN BROWSER ---
print("[*] Opening ZAP built-in browser (HUD) ...")
zap.selenium.launch_browser("firefox", apikey=API_KEY)  # launches built-in browser
print("[*] Browse websites now; traffic will be captured...")

# --- CAPTURE TRAFFIC ---
seen = set()
try:
    while True:
        # Get all the sites ZAP has recorded
        sites = zap.core.sites
        for site in sites:
            # Retrieve history of HTTP messages for each site (list of dicts)
            history_items = zap.core.messages(site)
            for item in history_items:
                msgid = item["id"]  # extract actual ID string
                if msgid not in seen:
                    seen.add(msgid)
                    msg = zap.core.message(msgid)
                    req_header = msg.get("requestHeader", "")
                    req_body = msg.get("requestBody", "")
                    resp_header = msg.get("responseHeader", "")
                    resp_body = msg.get("responseBody", "")

                    print("=" * 60)
                    print("[Request Header]")
                    print(req_header)
                    if req_body:
                        print("[Request Body]")
                        print(req_body)
                    print("[Response Header]")
                    print(resp_header)
                    if resp_body:
                        snippet = resp_body[:200] + "..." if len(resp_body) > 200 else resp_body
                        print("[Response Body]")
                        print(snippet)
                    print("=" * 60)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n[*] Stopping browser and ZAP…")
    # try to close the HUD browser
    try:
        zap.selenium.shutdown_browser(apikey=API_KEY)
    except Exception:
        pass
    # tell ZAP to shut down itself
    try:
        zap.core.shutdown(apikey=API_KEY)
    except Exception:
        pass
    # also terminate the daemon process we launched
    zap_proc.terminate()
    zap_proc.wait()
    print("[*] ZAP shut down cleanly.")
