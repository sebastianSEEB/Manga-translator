import base64
import asyncio
from io import BytesIO
from pathlib import Path
import shutil
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.imaging import clamp_box
from backend.pipeline.service import OCRService
from backend.translation.models import Lesson, Word

TOKEN='test-token-'+'a'*40
class Detector:
    def detect(self, image):
        return [{'bbox':(5,5,20,30),'vertical':True}, {'bbox':(55,7,20,30),'vertical':True}]
class Reader:
    def read(self,image): return '行くぞ'
class Translator:
    def __init__(self): self.calls=0
    async def translate(self,regions,glossary):
        self.calls+=1
        return [{**r.model_dump(),'en':"Let's go!",'kind':'dialogue'} for r in regions]
    async def learn(self,jp,en):
        return Lesson(reading='いくぞ',words=[Word(surface=jp,reading='いくぞ',meaning="Let's go",part_of_speech='phrase')],grammar='Casual declaration.')
def png(fmt='PNG'):
    out=BytesIO(); Image.new('RGB',(100,80),'white').save(out,format=fmt)
    return base64.b64encode(out.getvalue()).decode()
@pytest.fixture
def client(tmp_path):
    target=tmp_path/'glossaries'
    shutil.copytree(Path(__file__).parents[1]/'glossaries',target)
    settings=Settings(token=TOKEN,model='test-model',glossary_dir=target)
    translator=Translator()
    with TestClient(create_app(OCRService(Detector(),Reader()),translator,settings)) as c:
        c.headers['Authorization']='Bearer '+TOKEN
        c.translator=translator
        yield c

def test_contract_order_and_coordinates(client):
    response=client.post('/ocr',json={'image':'data:image/png;base64,'+png()})
    assert response.status_code==200
    data=response.json()
    assert (data['width'],data['height'])==(100,80)
    assert data['regions'][0]['bbox']==[55,7,20,30]
    assert data['regions'][0]['vertical'] is True
    assert response.headers['cache-control']=='no-store'

def test_auth_image_host_validation(client):
    assert client.post('/ocr',json={'image':png()},headers={'Authorization':''}).status_code==401
    assert client.post('/ocr',json={'image':'garbage'}).status_code==400
    assert client.post('/ocr',json={'image':png('JPEG')}).status_code==400
    assert client.post('/ocr',json={'image':png()},headers={'Origin':'https://yanmaga.jp'}).status_code==403
    assert client.get('/health',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/ocr',json={'image':123}).json()=={'detail':'Invalid request fields; check the API schema.'}

def test_clipping():
    assert clamp_box((-5,-9,110,90),100,80)==(0,0,100,80)
    assert clamp_box((50,50,20,30),100,80) is None

def test_cache_glossary_and_clear(client):
    payload={'image':png()}
    first=client.post('/translate',json=payload).json()
    second=client.post('/translate',json={**payload,'image':'data:image/png;base64,'+png()}).json()
    assert not first['cache_hit'] and second['cache_hit']
    assert first['regions'][0]['en']=="Let's go!"
    assert client.translator.calls==1
    glossary=client.get('/glossaries/wangan-midnight').json()
    glossary['characters']['アキオ']='Akio'
    assert client.put('/glossaries/wangan-midnight',json=glossary).status_code==200
    assert not client.post('/translate',json=payload).json()['cache_hit']
    assert client.translator.calls==2
    assert client.delete('/cache').json()['cleared']

def test_image_route_and_learning(client):
    result=client.post('/translate/image',content=base64.b64decode(png()),headers={'Content-Type':'image/png'})
    assert result.status_code==200 and result.headers['content-type']=='image/png'
    image=Image.open(BytesIO(result.content));assert image.width==100 and image.height>=80
    lesson=client.post('/learn',json={'jp':'行くぞ','en':"Let's go!"}).json()
    assert lesson['aligned'] and lesson['words'][0]['reading']=='いくぞ'

def test_jobs(client):
    response=client.post('/jobs',json={'image':png()})
    assert response.status_code==202
    job_id=response.json()['job_id']
    import time
    for _ in range(100):
        answer=client.get('/jobs/'+job_id).json()
        if answer['status']!='running':break
        time.sleep(.01)
    assert answer['status']=='done' and answer['result']['regions']
    assert client.get('/jobs/'+job_id).status_code==404

def test_export_and_glossary_paths(client):
    rows=[{'jp':'=SUM(A1)','en':'<script>','reading':'','notes':'line1\nline2'}]
    csv=client.post('/export',json={'rows':rows,'format':'csv'})
    assert "'=SUM(A1)" in csv.text
    anki=client.post('/export',json={'rows':rows,'format':'anki'})
    assert '&lt;script&gt;' in anki.text and '#html:true' in anki.text
    assert client.put('/glossaries/INVALID',json={'title':'x'}).status_code==400

def test_empty_detection_skips_ocr():
    class Empty:
        def detect(self,image):return []
    class Never:
        def read(self,image):raise AssertionError('No OCR on blank image')
    assert OCRService(Empty(),Never()).process(Image.new('RGB',(20,20))).regions==[]

def test_body_limit(client,monkeypatch):
    import backend.app as module
    monkeypatch.setattr(module,'MAX_BODY',100)
    assert client.post('/ocr',content=b'x'*101).status_code==413
