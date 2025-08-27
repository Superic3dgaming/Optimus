import os, sys
REQUIRED=[
    "config.py","config_schema.py","main.py","requirements.txt",".env.example",
    "brokers","core","data_cache","datafeeds","logs","managers","ops","scripts","state","tests",
    "core/logger.py","core/http.py",
    "datafeeds/delta_datafeed.py",
    "managers/backtest_manager.py","managers/paper_manager.py","managers/live_manager.py",
]

def main():
    missing=[]
    for p in REQUIRED:
        if not (os.path.isdir(p) or os.path.isfile(p)): missing.append(p)
    if missing:
        print("❌ Missing:", *[f" - {m}" for m in missing], sep="\n")
        sys.exit(1)
    print(f"✅ Structure looks good. Checked items: {len(REQUIRED)}")

if __name__ == "__main__":
    main()
