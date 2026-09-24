import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
from backend.config import ROOT

@dataclass
class Settings:
    token: str = field(default_factory=lambda: os.getenv("BACKEND_TOKEN", ""))
    llm_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/"))
    llm_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", ""))
    remote: bool = field(default_factory=lambda: os.getenv("LLM_ALLOW_REMOTE", "false").lower() == "true")
    strict: bool = field(default_factory=lambda: os.getenv("LLM_STRICT_SCHEMA", "true").lower() == "true")
    cache_size: int = field(default_factory=lambda: int(os.getenv("CACHE_PAGES", "24")))
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "1800")))
    hosts: list[str] = field(default_factory=lambda: ["127.0.0.1", "localhost", "testserver"] + [h.strip() for h in (os.getenv("EXTRA_ALLOWED_HOSTS", "") + "," + os.getenv("RAILWAY_PUBLIC_DOMAIN", "")).split(",") if h.strip()])
    glossary_dir: object = field(default_factory=lambda: Path(os.getenv("GLOSSARY_DIR", str(ROOT / "glossaries"))))

    def validate(self):
        if len(self.token) < 32:
            raise RuntimeError("Run python scripts/configure.py to generate BACKEND_TOKEN in .env.")
        url = urlparse(self.llm_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
            raise RuntimeError("Invalid LLM_BASE_URL.")
        if url.hostname not in {"localhost", "127.0.0.1", "::1"}:
            if not self.remote or url.scheme != "https":
                raise RuntimeError("Remote LLM requires HTTPS and LLM_ALLOW_REMOTE=true.")
        if not 0 <= self.cache_size <= 100 or not 1 <= self.cache_ttl <= 86400:
            raise RuntimeError("Invalid session cache limits.")
