import sys
import signal
import urllib.parse
import requests
import urllib3
from KEYS import keys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONSOLE_IP  = keys.get("CONSOLE_IP")
API_KEY     = keys.get("API_KEY")
FRONT_CAM   = keys.get("FRONT_CAMERA")
BACK_CAM    = keys.get("BACK_CAMERA")

headers = {"X-API-KEY": API_KEY}
base = f"https://{CONSOLE_IP}/proxy/protect/integration/v1"

def rtsps_to_rtsp(u: str) -> str:
    """
    Convert UniFi Protect RTSPS SRTP URL to plain RTSP:
    - scheme rtsps -> rtsp
    - port 7441 -> 7447
    - remove ?enableSrtp (and any query)
    """
    parsed = urllib.parse.urlsplit(u)
    scheme = "rtsp"
    netloc = parsed.hostname
    port = parsed.port
    if port is None:
        # default Protect rtsps port is 7441; rtsp is 7447
        port = 7441
    # switch to 7447 for RTSP
    if port == 7441:
        port = 7447
    netloc = f"{netloc}:{port}"
    # drop query entirely
    return urllib.parse.urlunsplit((scheme, netloc, parsed.path, "", ""))

def fetch_stream_url(cam_id: str, quality: str = "high") -> str:
    url = f"{base}/cameras/{cam_id}/rtsps-stream"
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    r.raise_for_status()
    data = r.json()
    # data looks like {'high': 'rtsps://...', 'medium': '...', ...}
    rtsps_url = data.get(quality) or data.get("medium") or data.get("low")
    if not rtsps_url:
        raise RuntimeError("No RTSPS URL returned. Make sure the stream quality is enabled in Protect.")
    return rtsps_url

def demo_fetch():
    # 1) List cameras
    cam_list_url = f"{base}/cameras"
    try:
        resp = requests.get(cam_list_url, headers=headers, verify=False, timeout=10)
        print("GET", cam_list_url, "->", resp.status_code)
        try:
            print(resp.json())
        except Exception as e:
            print("(non-JSON)", e)
    except Exception as e:
        print("Failed to list cameras:", e)

    # 2) Fetch RTSPS, convert to RTSP for the front camera
    try:
        rtsps_url = fetch_stream_url(FRONT_CAM, quality="high")
        print("RTSPS:", rtsps_url)
        rtsp_url = rtsps_to_rtsp(rtsps_url)
        print("RTSP:", rtsp_url)
    except Exception as e:
        print("Failed to fetch/convert stream URL:", e)

if __name__ == "__main__":
    # Allow Ctrl+C to exit cleanly
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    demo_fetch()
