import time
from zapv2 import ZAPv2
import subprocess
import requests

ZAP_PATH = r"/usr/bin/zaproxy"  # path to zaproxy binary
API_KEY = "pc0dcb1qlk7ndcdm5e40c308mg"
ZAP_ADDRESS = "127.0.0.1"
ZAP_PORT = "8090"

print("[*] Starting OWASP ZAP...")
zap_proc = subprocess.Popen(
    [ZAP_PATH, "-daemon", "-port", ZAP_PORT, "-host", ZAP_ADDRESS,
     "-config", "api.disablekey=false"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# --- wait until ZAP REST API responds ---
timeout = 60  # seconds
start = time.time()
while True:
    try:
        requests.get(f"http://{ZAP_ADDRESS}:{ZAP_PORT}", timeout=2)
        break
    except Exception:
        if time.time() - start > timeout:
            raise RuntimeError("ZAP did not start within timeout.")
        time.sleep(2)

# --- connect to ZAP ---
zap = ZAPv2(
    apikey=API_KEY,
    proxies={
        "http": f"http://{ZAP_ADDRESS}:{ZAP_PORT}",
        "https": f"http://{ZAP_ADDRESS}:{ZAP_PORT}",
    },
)
print("[*] OWASP ZAP started.")
print(f"[*] Proxy running on {ZAP_ADDRESS}:{ZAP_PORT}")

zap.core.new_session(name="fresh", overwrite=True, apikey=API_KEY)
print("[*] Started a fresh session (no previous logs).")

print("[*] Opening ZAP built-in browser (HUD) ...")
zap.selenium.launch_browser("firefox", apikey=API_KEY)
print("[*] Browse websites now; only URLs will be shown...")

# keep running until Ctrl+C
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[*] Shutting down browser and ZAP...")
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
