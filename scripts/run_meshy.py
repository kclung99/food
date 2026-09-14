#!/usr/bin/env python3
import argparse,base64,json,mimetypes,os,time,io
from datetime import datetime
from pathlib import Path
import requests
try:
    from PIL import Image
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    Image = None

def load_dotenv():
    env=Path('.env')
    if env.exists():
        for line in env.read_text().splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1)
                os.environ.setdefault(k.strip(),v.strip().strip('"\''))
load_dotenv()
p=argparse.ArgumentParser(); p.add_argument('input',type=Path); p.add_argument('--output',type=Path); a=p.parse_args()
key=os.environ.get('MESHY_API_KEY')
if not key: raise SystemExit('Set MESHY_API_KEY first')
files = [a.input] if a.input.is_file() else sorted(x for x in a.input.iterdir() if x.suffix.lower() in {'.jpg','.jpeg','.png','.heic'})
if not 1<=len(files)<=4: raise SystemExit('Meshy Multi-Image accepts 1–4 images')
def uri(x):
    mime=mimetypes.guess_type(x.name)[0] or 'image/jpeg'
    if x.suffix.lower() == '.heic':
        if Image is None: raise SystemExit('HEIC support requires: python3 -m pip install -r requirements.txt')
        image=Image.open(x).convert('RGB'); buffer=io.BytesIO(); image.save(buffer,format='JPEG',quality=92)
        return 'data:image/jpeg;base64,'+base64.b64encode(buffer.getvalue()).decode()
    return f'data:{mime};base64,'+base64.b64encode(x.read_bytes()).decode()
h={'Authorization':f'Bearer {key}','Content-Type':'application/json'}
body={'image_urls':[uri(x) for x in files],'ai_model':'meshy-7','should_texture':True,'target_formats':['glb']}
def request(method, url, **kwargs):
    for attempt in range(4):
        try: response=requests.request(method,url,**kwargs)
        except requests.RequestException:
            if attempt == 3: raise
            time.sleep(2 ** attempt); continue
        if response.status_code not in {429,500,502,503,504} or attempt == 3: return response
        time.sleep(min(30, 2 ** attempt))
r=request('POST','https://api.meshy.ai/openapi/v1/multi-image-to-3d',headers=h,json=body,timeout=120)
if not r.ok:
    raise SystemExit(f'Meshy rejected the request ({r.status_code}): {r.text}')
tid=r.json()['result']
started=time.time(); print(f'Submitted Meshy task {tid}')
while True:
    t=request('GET',f'https://api.meshy.ai/openapi/v1/multi-image-to-3d/{tid}',headers=h,timeout=60).json()
    elapsed=int(time.time()-started); mins,secs=divmod(elapsed,60)
    print(f'\rMeshy: {t.get("status", "UNKNOWN"):>11}  {t.get("progress", 0):>3}%  elapsed {mins:02d}:{secs:02d}',end='',flush=True)
    if t['status']=='SUCCEEDED': break
    if t['status'] in {'FAILED','CANCELED'}: raise SystemExit(str(t.get('task_error')))
    time.sleep(8)
print()
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
out=a.output or Path('runs')/f'{a.input.name}-{stamp}'; out.mkdir(parents=True,exist_ok=True)
g=request('GET',t['model_urls']['glb'],timeout=180); g.raise_for_status(); (out/'model.glb').write_bytes(g.content); (out/'task.json').write_text(json.dumps(t,indent=2)); print(f'Wrote {out}/model.glb')
