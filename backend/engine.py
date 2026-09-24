import hashlib
import json
from time import perf_counter
from fastapi.concurrency import run_in_threadpool
from backend.cache import SessionCache
from backend.imaging import decode_png

class Engine:
    def __init__(self, ocr, translator, glossaries, settings):
        self.ocr, self.translator, self.glossaries, self.settings = ocr, translator, glossaries, settings
        self.cache = SessionCache(settings.cache_size, settings.cache_ttl)
        self.lessons = SessionCache(100, settings.cache_ttl)

    async def translate(self, encoded, series):
        start = perf_counter()
        image = await run_in_threadpool(decode_png, encoded)
        glossary = self.glossaries.read(series)
        signature = json.dumps({"glossary": glossary, "model": self.settings.model,
            "endpoint": self.settings.llm_url, "pipeline": 1}, sort_keys=True, ensure_ascii=False)
        key = hashlib.sha256(image.size.__repr__().encode()+image.tobytes()+signature.encode()).hexdigest()
        cached = self.cache.get(key)
        if cached is not None:
            cached["cache_hit"] = True
            cached["timing_ms"] = {"total": round((perf_counter()-start)*1000,1)}
            return cached
        result = await run_in_threadpool(self.ocr.process, image)
        before = perf_counter()
        regions = await self.translator.translate(result.regions, glossary)
        answer = {**result.model_dump(), "regions": regions, "series": series, "cache_hit": False}
        answer["timing_ms"]["translation"] = round((perf_counter()-before)*1000,1)
        answer["timing_ms"]["total"] = round((perf_counter()-start)*1000,1)
        self.cache.put(key, answer)
        return answer

    async def learn(self, jp, en):
        key=hashlib.sha256((jp+"\0"+en).encode()).hexdigest()
        result=self.lessons.get(key)
        if result is not None: return result
        lesson=(await self.translator.learn(jp,en)).model_dump()
        lesson["aligned"] = "".join(word["surface"] for word in lesson["words"]) == jp
        lesson["warning"] = "AI-generated readings and explanations may be wrong; verify ambiguous names and slang."
        self.lessons.put(key, lesson)
        return lesson
