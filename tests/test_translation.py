import asyncio
import json
import httpx
import pytest
from backend.translation.llm import LLM, LLMError
from backend.translation.service import Translator
from backend.translation.models import TranslationBatch, Translation
from backend.schemas import TextRegion
from backend.settings import Settings
from backend.cache import SessionCache

@pytest.mark.parametrize('ids',[['b000','b000'],['wrong'],[]])
def test_reject_missing_extra_duplicate_ids(ids):
    class Fake:
        async def structured(self,*args):
            return TranslationBatch(translations=[Translation(id=id,en='Test',kind='dialogue') for id in ids])
    with pytest.raises(LLMError):
        asyncio.run(Translator(Fake()).translate([TextRegion(id='b000',bbox=(1,1,2,2),jp='日本',vertical=True)],{}))

def test_single_page_call_sfx_and_order():
    class Fake:
        calls=0
        async def structured(self,prompt,data,schema):
            self.calls+=1
            assert [r['id'] for r in data['regions']]==['b000','b001']
            return TranslationBatch(translations=[Translation(id='b001',en='Vroom',kind='sfx'),Translation(id='b000',en='Go!',kind='dialogue')])
    fake=Fake(); regions=[TextRegion(id=f'b00{i}',bbox=(1,1,2,2),jp='日本',vertical=True) for i in range(2)]
    output=asyncio.run(Translator(fake).translate(regions,{}))
    assert fake.calls==1 and output[1]['en']=='[Vroom]' and output[0]['id']=='b000'

def test_llm_request_and_invalid_output():
    async def work():
        llm=LLM(Settings(token='a'*40,model='test'))
        await llm.client.aclose()
        def respond(request):
            body=json.loads(request.content)
            assert body['store'] is False and body['response_format']['type']=='json_schema'
            assert len(body['messages'])==2
            return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'bad json'}}]})
        llm.client=httpx.AsyncClient(transport=httpx.MockTransport(respond))
        try:
            with pytest.raises(LLMError): await llm.structured('test',{},TranslationBatch)
        finally: await llm.close()
    asyncio.run(work())

def test_cache_eviction_and_expiry(monkeypatch):
    import backend.cache as module
    now=[0.0];monkeypatch.setattr(module,'monotonic',lambda:now[0])
    cache=SessionCache(1,10);cache.put('a',{'text':'one'});cache.put('b',{'text':'two'})
    assert cache.get('a') is None
    copy=cache.get('b');copy['text']='changed';assert cache.get('b')['text']=='two'
    now[0]=11;assert cache.get('b') is None

def test_remote_opt_in():
    with pytest.raises(RuntimeError):Settings(token='a'*40,llm_url='https://example.com/v1',remote=False).validate()
    with pytest.raises(RuntimeError):Settings(token='a'*40,llm_url='http://example.com/v1',remote=True).validate()
