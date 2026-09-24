import json
import os
import re
import tempfile
from pathlib import Path
from pydantic import BaseModel, Field, field_validator

class Glossary(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    terms: dict[str, str] = Field(default_factory=dict, max_length=500)
    characters: dict[str, str] = Field(default_factory=dict, max_length=200)
    @field_validator("terms", "characters")
    @classmethod
    def valid_entries(cls, entries):
        if any(not k.strip() or not v.strip() or len(k)>200 or len(v)>300 for k,v in entries.items()):
            raise ValueError("Glossary entries must be nonempty and at most 200/300 characters.")
        return entries

class Glossaries:
    def __init__(self, directory): self.directory = Path(directory)
    def path(self, series):
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", series):
            raise ValueError("Series ID must use lowercase letters, digits, hyphens or underscores.")
        return self.directory / (series + ".json")
    def read(self, series):
        path = self.path(series)
        if not path.is_file(): raise ValueError("Unknown series; create it in extension settings first.")
        return Glossary.model_validate_json(path.read_text(encoding="utf-8")).model_dump()
    def list(self):
        return [{"id": p.stem, "title": self.read(p.stem)["title"]}
                for p in sorted(self.directory.glob("*.json"))]
    def write(self, series, glossary):
        target = self.path(series)
        self.directory.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as out:
                out.write(glossary.model_dump_json(indent=2))
            os.replace(temp, target)
        finally:
            if os.path.exists(temp): os.unlink(temp)
