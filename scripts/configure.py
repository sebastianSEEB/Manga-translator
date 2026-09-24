"""Create .env once and add a cryptographically random backend token."""
from pathlib import Path
import re
import secrets
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/".env"
text=path.read_text() if path.exists() else (ROOT/".env.example").read_text()
match=re.search(r"^BACKEND_TOKEN=(.*)$",text,re.M)
if not match or len(match.group(1).strip())<32:
    line="BACKEND_TOKEN="+secrets.token_urlsafe(32)
    text=re.sub(r"^BACKEND_TOKEN=.*$",line,text,flags=re.M) if match else text+"\n"+line+"\n"
    path.write_text(text)
    try: path.chmod(0o600)
    except OSError: pass
print(".env is ready. Copy BACKEND_TOKEN into extension settings; select your LLM model in .env.")
