from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    # Capture the full HTTP request
    print("\n=== HTTP REQUEST ===")
    print(f"{flow.request.method} {flow.request.url}")
    for name, value in flow.request.headers.items():
        print(f"{name}: {value}")
    if flow.request.content:
        try:
            print("Body:", flow.request.content.decode("utf-8", errors="ignore"))
        except Exception:
            print("Body: [binary data]")

def response(flow: http.HTTPFlow) -> None:
    # Capture the full HTTP response
    print("\n=== HTTP RESPONSE ===")
    print(f"Status: {flow.response.status_code}")
    for name, value in flow.response.headers.items():
        print(f"{name}: {value}")
    if flow.response.content:
        try:
            # Limit output to first 500 chars for readability
            body = flow.response.content.decode("utf-8", errors="ignore")
            print("Body:", body[:500])
        except Exception:
            print("Body: [binary data]")
