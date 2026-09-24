import asyncio
import base64
import hmac
import re
import secrets
from contextlib import asynccontextmanager, suppress
from time import monotonic
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from backend.config import MAX_BODY
from backend.imaging import decode_png
from backend.schemas import OCRRequest, OCRResponse
from backend.settings import Settings
from backend.glossary import Glossary, Glossaries
from backend.translation.llm import LLM, LLMError
from backend.translation.service import Translator
from backend.engine import Engine
from backend.exports import export_rows
from backend.rendering import render

class PageRequest(OCRRequest):
    series: str = Field(default="wangan-midnight", pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")
class LearnRequest(BaseModel):
    jp: str = Field(min_length=1,max_length=3000)
    en: str = Field(max_length=3000)
class ExportRow(BaseModel):
    jp: str = Field(max_length=3000)
    reading: str = Field(default="",max_length=3000)
    en: str = Field(max_length=3000)
    notes: str = Field(default="",max_length=3000)
class ExportRequest(BaseModel):
    rows: list[ExportRow] = Field(min_length=1,max_length=500)
    format: str = Field(default="csv",pattern="^(csv|anki)$")

class BodyLimit:
    def __init__(self, app): self.app=app
    async def __call__(self, scope, receive, send):
        if scope['type']!='http': return await self.app(scope,receive,send)
        chunks,size=[],0
        while True:
            message=await receive()
            if message['type']=='http.disconnect': return
            size+=len(message.get('body',b''))
            if size>MAX_BODY:
                return await JSONResponse({'detail':'Request too large.'},413)(scope,receive,send)
            chunks.append(message)
            if not message.get('more_body',False): break
        async def replay():
            return chunks.pop(0) if chunks else await receive()
        await self.app(scope,replay,send)

def create_app(service=None, translator=None, settings=None):
    settings=settings or Settings()
    @asynccontextmanager
    async def lifespan(app):
        settings.validate()
        llm=None
        if service is None:
            from backend.pipeline.detector import ComicDetector
            from backend.pipeline.ocr import MangaReader
            from backend.pipeline.service import OCRService
            ocr=await run_in_threadpool(lambda: OCRService(ComicDetector(),MangaReader()))
        else: ocr=service
        if translator is None:
            llm=LLM(settings)
            selected_translator=Translator(llm)
        else: selected_translator=translator
        app.state.service=ocr
        app.state.engine=Engine(ocr,selected_translator,Glossaries(settings.glossary_dir),settings)
        app.state.busy=asyncio.Lock()
        app.state.jobs={}
        app.state.tasks=set()
        async def cleanup():
            while True:
                await asyncio.sleep(30)
                now=monotonic()
                for key,item in list(app.state.jobs.items()):
                    if item['status']!='running' and now-item['born']>300:
                        app.state.jobs.pop(key,None)
                app.state.engine.cache.prune(); app.state.engine.lessons.prune()
        janitor=asyncio.create_task(cleanup())
        try: yield
        finally:
            janitor.cancel()
            with suppress(asyncio.CancelledError): await janitor
            if app.state.tasks: await asyncio.gather(*app.state.tasks,return_exceptions=True)
            if llm: await llm.close()
            app.state.engine.cache.clear(); app.state.engine.lessons.clear(); app.state.jobs.clear()

    app=FastAPI(title='Manga Translator',version='1.0.0',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.add_middleware(BodyLimit)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=settings.hosts)

    @app.middleware('http')
    async def security(request, call_next):
        origin=request.headers.get('origin','')
        if origin and not re.fullmatch(r'chrome-extension://[a-p]{32}',origin) and origin not in {'http://127.0.0.1:8000','http://localhost:8000'}:
            return JSONResponse({'detail':'Origin is not allowed.'},403)
        if request.url.path!='/health':
            supplied=request.headers.get('authorization','')
            if not settings.token or not hmac.compare_digest(supplied.encode(),('Bearer '+settings.token).encode()):
                return JSONResponse({'detail':'Backend token missing or incorrect.'},401)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store'
        response.headers['X-Content-Type-Options']='nosniff'
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        # Pydantic's default response echoes invalid input, including screenshot data.
        return JSONResponse({'detail':'Invalid request fields; check the API schema.'},422)

    @app.exception_handler(ValueError)
    async def value_error(request,exc):
        return JSONResponse({'detail':str(exc)},400)

    @app.exception_handler(LLMError)
    async def llm_error(request,exc):
        return JSONResponse({'detail':str(exc)},502)

    async def exclusive(work):
        if app.state.busy.locked(): raise HTTPException(429,'Another request is running; try again shortly.')
        async with app.state.busy:
            try: return await work()
            except (ValueError,LLMError,HTTPException): raise
            except Exception:
                raise HTTPException(500,'Processing failed. Check model installation and configuration.') from None

    @app.get('/health')
    def health():
        return {'status':'ready','version':'1.0.0','translation_configured':bool(settings.model),'persistence':'session-only results'}

    @app.post('/ocr',response_model=OCRResponse)
    async def ocr(payload: OCRRequest):
        async def work():
            return await run_in_threadpool(lambda: app.state.service.process(decode_png(payload.image)))
        return await exclusive(work)

    @app.post('/translate')
    async def translate(payload: PageRequest):
        return await exclusive(lambda: app.state.engine.translate(payload.image,payload.series))

    async def enqueue(operation):
        if app.state.busy.locked(): raise HTTPException(429,'Another request is running; try again shortly.')
        # Reserve before yielding; don't create an unbounded screenshot queue.
        await app.state.busy.acquire()
        key=secrets.token_urlsafe(24)
        # At most eight completed results may wait for collection.
        completed=[k for k,v in app.state.jobs.items() if v['status']!='running']
        for old in completed[:-7]: app.state.jobs.pop(old,None)
        app.state.jobs[key]={'status':'running','born':monotonic()}
        async def work():
            try:
                result=await operation()
                app.state.jobs[key]={'status':'done','result':result,'born':monotonic()}
            except (ValueError,LLMError) as exc:
                app.state.jobs[key]={'status':'error','detail':str(exc),'born':monotonic()}
            except Exception:
                app.state.jobs[key]={'status':'error','detail':'Processing failed. Check model installation.','born':monotonic()}
            finally: app.state.busy.release()
        task=asyncio.create_task(work()); app.state.tasks.add(task)
        task.add_done_callback(app.state.tasks.discard)
        return {'job_id':key}

    @app.post('/jobs',status_code=202)
    async def start_job(payload: PageRequest):
        return await enqueue(lambda: app.state.engine.translate(payload.image,payload.series))

    @app.post('/learn/jobs',status_code=202)
    async def start_lesson(payload: LearnRequest):
        return await enqueue(lambda: app.state.engine.learn(payload.jp,payload.en))

    @app.get('/jobs/{key}')
    def job(key: str):
        item=app.state.jobs.get(key)
        if item is None: raise HTTPException(404,'Job expired or already collected.')
        if item['status']!='running': app.state.jobs.pop(key,None)
        return {k:v for k,v in item.items() if k!='born'}

    @app.post('/translate/image')
    async def image_translation(request: Request, series: str='wangan-midnight'):
        if request.headers.get('content-type','').split(';')[0]!='image/png':
            raise HTTPException(415,'Send a PNG body with Content-Type: image/png.')
        raw=await request.body()
        encoded=base64.b64encode(raw).decode('ascii')
        async def work():
            result=await app.state.engine.translate(encoded,series)
            png=await run_in_threadpool(lambda: render(decode_png(encoded),result['regions']))
            return Response(png,media_type='image/png',headers={
                'X-Cache-Hit':str(result['cache_hit']).lower(),
                'Content-Disposition':'inline; filename="translated.png"'})
        return await exclusive(work)

    @app.post('/learn')
    async def learn(payload: LearnRequest):
        return await exclusive(lambda: app.state.engine.learn(payload.jp,payload.en))

    @app.post('/export')
    def export(payload: ExportRequest):
        kind=payload.format
        return Response(export_rows(payload.rows,kind),media_type='text/csv' if kind=='csv' else 'text/plain',
            headers={'Content-Disposition':f'attachment; filename="manga-learning.{"csv" if kind=="csv" else "tsv"}"'})

    @app.get('/glossaries')
    def list_glossaries(): return app.state.engine.glossaries.list()

    @app.get('/glossaries/{series}')
    def glossary(series: str): return app.state.engine.glossaries.read(series)

    @app.put('/glossaries/{series}')
    async def save_glossary(series: str, value: Glossary):
        async def work():
            app.state.engine.glossaries.write(series,value)
            app.state.engine.cache.clear()
            return {'saved':True}
        return await exclusive(work)

    @app.delete('/cache')
    async def clear_cache():
        async def work():
            app.state.engine.cache.clear(); app.state.engine.lessons.clear(); app.state.jobs.clear()
            return {'cleared':True}
        return await exclusive(work)
    return app

app=create_app()
