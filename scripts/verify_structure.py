import os, sys
REQUIRED=[
    "config.py","config_schema.py","main.py","requirements.txt",
    "brokers","core","data_cache","datafeeds","logs","managers","ops","scripts","state","tests",
    "core/logger.py","core/http.py",
    "datafeeds/delta_datafeed.py",
    "managers/backtest_manager.py","managers/paper_manager.py","managers/live_manager.py",
]

OPTIONAL=[
    ".env.example",
]

def main():
    missing=[]
    missing_optional=[]
    
    for p in REQUIRED:
        if not (os.path.isdir(p) or os.path.isfile(p)): 
            missing.append(p)
            
    for p in OPTIONAL:
        if not (os.path.isdir(p) or os.path.isfile(p)): 
            missing_optional.append(p)
    
    if missing:
        print("❌ Missing required files:", *[f" - {m}" for m in missing], sep="\n")
        sys.exit(1)
        
    if missing_optional:
        print("⚠️  Missing optional files:", *[f" - {m}" for m in missing_optional], sep="\n")
        
    print(f"✅ Structure looks good. Checked items: {len(REQUIRED)} required, {len(OPTIONAL)} optional")

if __name__ == "__main__":
    main()
