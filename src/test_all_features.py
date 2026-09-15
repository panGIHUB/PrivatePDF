import io, sys, tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader
import fitz

sys.path.insert(0, str(Path(__file__).parent))
from app.main import app


def pdf_bytes(pages=3):
    d=fitz.open()
    for i in range(pages):
        p=d.new_page(width=595,height=842)
        p.insert_text((60,100), f"PrivatePDF Test Page {i+1}", fontsize=20)
        p.insert_text((60,140), "Watermark compression grayscale extraction test", fontsize=12)
    b=d.tobytes(); d.close(); return b

PDF=pdf_bytes()
IMG=io.BytesIO(); Image.new('RGB',(400,300),'white').save(IMG,'PNG'); IMG=IMG.getvalue()


def check_pdf(resp, name):
    assert resp.status_code == 200, f"{name}: HTTP {resp.status_code}: {resp.text[:500]}"
    PdfReader(io.BytesIO(resp.content))
    assert len(resp.content)>100, f"{name}: empty output"

with TestClient(app) as c:
    tests=[]
    def t(name, fn):
        try:
            r=fn();
            if name in ('pdf-to-jpg',):
                assert r.status_code==200 and len(r.content)>100
            elif name=='text':
                assert r.status_code==200 and b'PrivatePDF Test Page' in r.content
            elif name=='markdown':
                assert r.status_code==200 and b'Page 1' in r.content
            elif name in ('office-to-pdf','pdf-to-office'):
                pass
            else: check_pdf(r,name)
            tests.append((name,'PASS',''))
        except Exception as e: tests.append((name,'FAIL',str(e)))

    try:
        r=c.get('/api/health'); assert r.status_code==200 and r.json().get('ok') is True
        tests.append(('health','PASS',''))
    except Exception as e: tests.append(('health','FAIL',str(e)))
    t('merge', lambda: c.post('/api/merge', files=[('files',('a.pdf',PDF,'application/pdf')),('files',('b.pdf',PDF,'application/pdf'))]))
    t('extract', lambda: c.post('/api/pages', data={'action':'extract','pages':'1,3'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('delete', lambda: c.post('/api/pages', data={'action':'delete','pages':'2'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('reorder', lambda: c.post('/api/pages', data={'action':'reorder','pages':'3,1,2'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('rotate', lambda: c.post('/api/rotate', data={'degrees':'90'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('compress', lambda: c.post('/api/compress', data={'dpi':'110','quality':'70'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('resize', lambda: c.post('/api/resize', data={'size':'A4','orientation':'portrait'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('crop', lambda: c.post('/api/crop', data={'margin':'20'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('numbers', lambda: c.post('/api/numbers', data={'start':'10'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('watermark', lambda: c.post('/api/watermark', data={'text':'CONFIDENTIAL','opacity':'0.25','size':'42','angle':'37','color':'#555555','position':'center','tiled':'false','bold':'true','outline':'true'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('protect', lambda: c.post('/api/protect', data={'password':'secret123'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    protected=c.post('/api/protect', data={'password':'secret123'}, files={'file':('a.pdf',PDF,'application/pdf')})
    t('unlock', lambda: c.post('/api/unlock', data={'password':'secret123'}, files={'file':('a.pdf',protected.content,'application/pdf')}))
    t('metadata', lambda: c.post('/api/metadata', data={'mode':'remove'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('grayscale', lambda: c.post('/api/grayscale', files={'file':('a.pdf',PDF,'application/pdf')}))
    t('text', lambda: c.post('/api/text', files={'file':('a.pdf',PDF,'application/pdf')}))
    t('markdown', lambda: c.post('/api/markdown', files={'file':('a.pdf',PDF,'application/pdf')}))
    t('pdf-to-jpg', lambda: c.post('/api/pdf-to-jpg', data={'fmt':'jpg'}, files={'file':('a.pdf',PDF,'application/pdf')}))
    t('images-to-pdf', lambda: c.post('/api/images-to-pdf', files=[('files',('x.png',IMG,'image/png'))]))

    for name, status, err in tests:
        print(f"{status:4} {name}" + (f" :: {err}" if err else ''))
    failed=[x for x in tests if x[1]=='FAIL']
    print(f"\nRESULT: {len(tests)-len(failed)}/{len(tests)} passed")
    if failed: raise SystemExit(1)
