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
print("[*] Browse websites now; only URLs will be shown...")

# --- CAPTURE ONLY URLS ---
seen = set()
try:
    while True:
        sites = zap.core.sites
        for site in sites:
            history_items = zap.core.messages(site)
            for item in history_items:
                msgid = item["id"]
                if msgid not in seen:
                    seen.add(msgid)
                    # extract URL from the request header
                    msg = zap.core.message(msgid)
                    req_header = msg.get("requestHeader", "")
                    # first line of header: e.g. "GET http://example.com/ HTTP/1.1"
                    first_line = req_header.split("\r\n", 1)[0]
                    # URL is between the HTTP verb and protocol
                    parts = first_line.split(" ")
                    if len(parts) >= 2:
                        url = parts[1]
                        print(url)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n[*] Stopping browser and ZAP…")
    try:
        zap.selenium.shutdown_browser(apikey=API_KEY)
    except Exception:
        pass
    try:
        zap.core.shutdown(apikey=API_KEY)
    except Exception:
        pass
    zap_proc.terminate()
    zap_proc.wait()
    print("[*] ZAP shut down cleanly.")
