"""import sys
import json
import requests
import subprocess
import socket
import ssl
from urllib.parse import urljoin, urlparse
import os

def check_http_headers(url):
    print("\n[+] Checking HTTP headers...")
    try:
        resp = requests.get(url, timeout=5, allow_redirects=True)
        headers = resp.headers
        security_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-XSS-Protection",
            "X-Content-Type-Options"
        ]
        for header in security_headers:
            if header in headers:
                print(f"  ✔ {header}: {headers[header]}")
            else:
                print(f"  ✘ {header} missing")
    except Exception as e:
        print(f"  [Error] Failed to check headers: {e}")

def check_ssl_info(domain):
    print("\n[+] Checking SSL certificate info...")
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            print(f"  ✔ Issuer: {cert['issuer'][-1][-1]}")
            print(f"  ✔ Valid from: {cert['notBefore']}")
            print(f"  ✔ Valid until: {cert['notAfter']}")
    except Exception as e:
        print(f"  [Error] SSL info check failed: {e}")

def run_assetfinder(domain):
    print("\n[+] Running subdomain enumeration with assetfinder...")
    try:
        output = subprocess.check_output(['assetfinder', '--subs-only', domain], text=True)
        subs = output.strip().split('\n')
        for sub in subs:
            print(f"  ➤ {sub}")
    except Exception as e:
        print(f"  [Error] assetfinder failed: {e}")

def run_nmap_scan(domain):
    print("\n[+] Running Nmap port scan (top 1000 ports)...")
    try:
        output = subprocess.check_output(['nmap', '-F', domain], text=True)
        print(output)
    except Exception as e:
        print(f"  [Error] Nmap scan failed: {e}")

def check_robots_sitemap(url):
    print("\n[+] Checking for robots.txt and sitemap.xml...")
    try:
        for path in ['robots.txt', 'sitemap.xml']:
            r = requests.get(urljoin(url, path), timeout=5)
            if r.status_code == 200:
                print(f"  ✔ Found {path}")
            else:
                print(f"  ✘ {path} not found (HTTP {r.status_code})")
    except Exception as e:
        print(f"  [Error] Failed to fetch robots/sitemap: {e}")

def check_default_pages(url):
    print("\n[+] Checking for default login/admin pages...")
    paths = ['admin', 'login', 'administrator', 'wp-admin']
    for path in paths:
        full_url = urljoin(url, path)
        try:
            r = requests.get(full_url, timeout=5)
            if r.status_code == 200:
                print(f"  ✔ Found possible page: {full_url}")
        except:
            continue

def dir_brute_force(url, wordlist='dirlist.txt'):
    print("\n[+] Running basic directory brute-force...")

    # Get the absolute path to dirlist.txt relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wordlist_path = os.path.join(script_dir, wordlist)

    if not os.path.exists(wordlist_path):
        print(f"  [Warning] Wordlist not found: {wordlist_path}")
        return

    with open(wordlist_path, 'r') as f:
        for line in f:
            path = line.strip()
            full_url = urljoin(url, path)
            try:
                r = requests.get(full_url, timeout=3, allow_redirects=True)
                if r.status_code == 200:
                    print(f"  ✔ {full_url} [200 OK]")
            except:
                continue


def main(target_url):
    target_url = target_url.strip()
    if not target_url:
        print("[ERROR] No target URL provided.")
        return

    parsed = urlparse(target_url)
    domain = parsed.netloc or parsed.path

    check_http_headers(target_url)
    check_ssl_info(domain)
    run_assetfinder(domain)
    run_nmap_scan(domain)
    check_robots_sitemap(target_url)
    check_default_pages(target_url)
    dir_brute_force(target_url)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            scan_data = json.loads(sys.argv[1])
            print(f"✅ Basic scan started for {scan_data['target_url']}")
            #print(f"Scan Type: {scan_data['scan_type']}")
            #print(f"Auth Type: {scan_data['auth_type']}")
            main(scan_data['target_url'])
            # ... do actual scanning here ...
            print("✅ Basic scan completed.")
        except Exception as e:
            print(f"[❌] Error in basic scan: {e}")
    else:
        print("❌ No scan data received.")"""

import sys
import json
import requests
import subprocess
import socket
import ssl
from urllib.parse import urljoin, urlparse
import os
import time

# In main.py, replace the existing wait_for_user_approval function with this:
def wait_for_user_approval(scan_id, command_text):
    try:
        # Step 1: Send the command to the server and get a command_id
        res = requests.post("http://localhost:5000/api/command/wait", json={
            "scan_id": scan_id,
            "step": command_text,  # You can pass the step as well
            "command": command_text
        })
        command_id = res.json()["command_id"]

        print(f"[Prompt] Waiting for user decision on: {command_text}")

        # Step 2: Poll the server for the user's decision
        while True:
            time.sleep(1)
            r = requests.get(f"http://localhost:5000/api/command/decision/{command_id}")
            if r.status_code == 200:
                decision = r.json().get("decision")
                if decision:
                    print(f"[Decision] {decision.upper()} for command: {command_text}")
                    return decision
            else:
                print("[!] Error polling user decision")
                return "skip"
    except Exception as e:
        print(f"[Error] Failed to get user approval: {e}")
        return "skip"

def check_http_headers(url):
    print("\n[+] Checking HTTP headers...")
    try:
        resp = requests.get(url, timeout=5, allow_redirects=True)
        headers = resp.headers
        security_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Frame-Options",
            "X-XSS-Protection",
            "X-Content-Type-Options"
        ]
        for header in security_headers:
            if header in headers:
                print(f"  ✔ {header}: {headers[header]}")
            else:
                print(f"  ✘ {header} missing")
    except Exception as e:
        print(f"  [Error] Failed to check headers: {e}")

def check_ssl_info(domain):
    print("\n[+] Checking SSL certificate info...")
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(5)
            s.connect((domain, 443))
            cert = s.getpeercert()
            print(f"  ✔ Issuer: {cert['issuer'][-1][-1]}")
            print(f"  ✔ Valid from: {cert['notBefore']}")
            print(f"  ✔ Valid until: {cert['notAfter']}")
    except Exception as e:
        print(f"  [Error] SSL info check failed: {e}")

def run_assetfinder(domain):
    print("\n[+] Running subdomain enumeration with assetfinder...")
    try:
        output = subprocess.check_output(['assetfinder', '--subs-only', domain], text=True)
        subs = output.strip().split('\n')
        for sub in subs:
            print(f"  ➤ {sub}")
    except Exception as e:
        print(f"  [Error] assetfinder failed: {e}")

def run_nmap_scan(domain):
    print("\n[+] Running Nmap port scan (top 1000 ports)...")
    try:
        output = subprocess.check_output(['nmap', '-F', domain], text=True)
        print(output)
    except Exception as e:
        print(f"  [Error] Nmap scan failed: {e}")

def check_robots_sitemap(url):
    print("\n[+] Checking for robots.txt and sitemap.xml...")
    try:
        for path in ['robots.txt', 'sitemap.xml']:
            r = requests.get(urljoin(url, path), timeout=5)
            if r.status_code == 200:
                print(f"  ✔ Found {path}")
            else:
                print(f"  ✘ {path} not found (HTTP {r.status_code})")
    except Exception as e:
        print(f"  [Error] Failed to fetch robots/sitemap: {e}")

def check_default_pages(url):
    print("\n[+] Checking for default login/admin pages...")
    paths = ['admin', 'login', 'administrator', 'wp-admin']
    for path in paths:
        full_url = urljoin(url, path)
        try:
            r = requests.get(full_url, timeout=5)
            if r.status_code == 200:
                print(f"  ✔ Found possible page: {full_url}")
        except:
            continue

def dir_brute_force(url, wordlist='dirlist.txt'):
    print("\n[+] Running basic directory brute-force...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    wordlist_path = os.path.join(script_dir, wordlist)

    if not os.path.exists(wordlist_path):
        print(f"  [Warning] Wordlist not found: {wordlist_path}")
        return

    with open(wordlist_path, 'r') as f:
        for line in f:
            path = line.strip()
            full_url = urljoin(url, path)
            try:
                r = requests.get(full_url, timeout=3, allow_redirects=True)
                if r.status_code == 200:
                    print(f"  ✔ {full_url} [200 OK]")
            except:
                continue

def main(target_url, scan_id):
    target_url = target_url.strip()
    if not target_url:
        print("[ERROR] No target URL provided.")
        return

    parsed = urlparse(target_url)
    domain = parsed.netloc or parsed.path

    steps = [
        ("Check HTTP Headers", lambda: check_http_headers(target_url)),
        ("Check SSL Info", lambda: check_ssl_info(domain)),
        ("Run Assetfinder", lambda: run_assetfinder(domain)),
        ("Run Nmap Scan", lambda: run_nmap_scan(domain)),
        ("Check Robots/Sitemap", lambda: check_robots_sitemap(target_url)),
        ("Check Default Admin Pages", lambda: check_default_pages(target_url)),
        ("Directory Brute Force", lambda: dir_brute_force(target_url)),
    ]

    for label, func in steps:
        decision = wait_for_user_approval(scan_id, label)
        if decision == "terminate":
            print("[TERMINATED] Scan halted by user.")
            sys.exit(0)
        elif decision == "approve":
            func()
        else:
            print(f"[SKIPPED] {label}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            scan_data = json.loads(sys.argv[1])
            print(f"✅ Basic scan started for {scan_data['target_url']}")
            main(scan_data['target_url'], scan_data['scan_id'])
            print("✅ Basic scan completed.")
        except Exception as e:
            print(f"[❌] Error in basic scan: {e}")
    else:
        print("❌ No scan data received.")
