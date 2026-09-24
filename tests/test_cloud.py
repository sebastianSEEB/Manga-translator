from pathlib import Path
from backend.settings import Settings
from scripts import cloud_start

def test_railway_domain_and_glossary_settings(monkeypatch,tmp_path):
    monkeypatch.setenv('RAILWAY_PUBLIC_DOMAIN','manga.up.railway.app')
    monkeypatch.setenv('GLOSSARY_DIR',str(tmp_path))
    settings=Settings()
    assert 'manga.up.railway.app' in settings.hosts
    assert settings.glossary_dir==tmp_path
    assert '*' not in settings.hosts

def test_seed_and_port_preserve_edits(monkeypatch,tmp_path):
    source=tmp_path/'app'/'glossaries';source.mkdir(parents=True)
    (source/'sample.json').write_text('{"title":"seed"}')
    target=tmp_path/'data'
    monkeypatch.setattr(cloud_start,'root',source.parent)
    monkeypatch.setenv('GLOSSARY_DIR',str(target))
    monkeypatch.setenv('PORT','9876')
    monkeypatch.setenv('RAILWAY_ENVIRONMENT_ID','test')
    monkeypatch.setenv('EXTRA_ALLOWED_HOSTS','custom.example')
    assert cloud_start.prepare()==9876
    assert (target/'sample.json').exists()
    (target/'sample.json').write_text('{"title":"edited"}')
    cloud_start.prepare()
    assert 'edited' in (target/'sample.json').read_text()
    import os
    assert 'healthcheck.railway.app' in os.environ['EXTRA_ALLOWED_HOSTS']
