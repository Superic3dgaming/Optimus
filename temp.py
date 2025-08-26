import os, requests
from dotenv import load_dotenv

load_dotenv()

bases = [b.strip().rstrip("/") for b in (os.getenv("OPTIMUS_API_BASES") or "").split(",") if b.strip()]
if not bases:
    bases = [(os.getenv("OPTIMUS_API_BASE") or "https://api.delta.exchange").rstrip("/")]

paths = [os.getenv("OPTIMUS_API_PATH_PRODUCTS") or "/v3/public/products", "/v2/public/products"]

for base in bases:
    for p in paths:
        url = f"{base}{p}"
        try:
            r = requests.get(url, params={"limit": 1}, timeout=(5,5))
            print(url, "->", r.status_code)
            if r.ok:
                print(r.text[:200])
        except Exception as e:
            print(url, "ERROR", e)

