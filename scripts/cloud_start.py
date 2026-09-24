"""Container entrypoint: listen on platform port; persist only explicit glossary data."""
import os
import shutil
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))

def prepare():
    source=root/"glossaries"
    target=Path(os.getenv("GLOSSARY_DIR",str(source)))
    target.mkdir(parents=True,exist_ok=True)
    if target.resolve()!=source.resolve():
        for seed in source.glob("*.json"):
            if not (target/seed.name).exists(): shutil.copyfile(seed,target/seed.name)
    # Railway healthchecks use this platform-owned Host; API requests still need a token.
    hosts=[h for h in os.getenv("EXTRA_ALLOWED_HOSTS","").split(",") if h]
    if os.getenv("RAILWAY_ENVIRONMENT_ID"):
        hosts.append("healthcheck.railway.app")
    os.environ["EXTRA_ALLOWED_HOSTS"]=",".join(hosts)
    return int(os.getenv("PORT","8000"))

if __name__=="__main__":
    import uvicorn
    uvicorn.run("backend.app:app",host="0.0.0.0",port=prepare(),workers=1,access_log=False)
