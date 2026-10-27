"""Build v5 from immutable v4: remove 8 content exclusions and 104 PY2027 records."""
from pathlib import Path
import os,sys,json,zipfile,io,hashlib,re,urllib.request
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=json.loads((ROOT/'data/current_manifest.json').read_text())
EXCLUDED={x['UT'] for x in json.loads((ROOT/'reviews/2026-10-27_early/excluded_8.json').read_text())}
EXPECTED=MANIFEST['source_file_sha256']
TAG='data-v5-20261027'
ASSET='AI4S_9363_WoS_PY_TXT.zip'
SOURCE_TAG='data-v4-20261023'
SOURCE_ASSET='AI4S_9475_WoS_TXT.zip'
def sha(b):return hashlib.sha256(b).hexdigest()
def package(files):
 assert set(files)==set(EXPECTED) and len(files)==19
 records=[];removed=[];outside=[]
 for name in sorted(files,key=lambda n:int(re.search(r'download(\d+)',n)[1])):
  b=files[name];assert sha(b)==EXPECTED[name],name
  blocks=re.findall(r'^PT .*?^ER\s*$',b.decode('utf-8-sig'),re.M|re.S)
  for block in blocks:
   ut=re.search(r'^UT (.+)$',block,re.M)[1].strip();py=int(re.search(r'^PY (\d{4})$',block,re.M)[1])
   if ut in EXCLUDED:removed.append(ut)
   elif not 2010<=py<=2026:outside.append(ut)
   else:records.append((ut,py,block))
 assert len(records)+len(removed)+len(outside)==9475
 assert len(records)==len({x[0] for x in records})==9363
 assert set(removed)==EXCLUDED and len(removed)==8
 assert set(outside)=={x['UT'] for x in json.loads((ROOT/'reviews/2026-10-27_early/out_of_range_PY2027_104.json').read_text())}
 from collections import Counter
 assert dict(sorted(Counter(str(x[1]) for x in records).items()))==MANIFEST['annual_counts']
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for start in range(0,len(records),500):
   part=records[start:start+500];name=f'AI4S_9363_WoS_PY_TXT/download{start+1}-{start+len(part)}.txt'
   text='FN Clarivate Analytics Web of Science\nVR 1.0\n'+''.join(x[2].rstrip()+'\n\n' for x in part)+'EF\n'
   info=zipfile.ZipInfo(name,(2026,10,27,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
   z.writestr(info,text.encode('utf-8-sig'),compresslevel=9)
 result=out.getvalue()
 assert sha(result)==MANIFEST['output_sha256']
 with zipfile.ZipFile(io.BytesIO(result)) as z:
  assert len(z.namelist())==19
  assert sum(len(re.findall(r'^UT ',z.read(n).decode('utf-8-sig'),re.M)) for n in z.namelist())==9363
 return result
if len(sys.argv)>1:
 source=Path(sys.argv[1])
 if source.is_dir():files={p.name:p.read_bytes() for p in source.glob('*.txt')}
 else:
  with zipfile.ZipFile(source) as z:files={Path(n).name:z.read(n) for n in z.namelist() if n.endswith('.txt')}
 data=package(files);dest=ROOT/ASSET;dest.write_bytes(data)
 print(json.dumps({'records':9363,'files':19,'sha256':sha(data),'bytes':len(data)}));sys.exit()
token=os.environ['GH_TOKEN'];repo=os.environ['GITHUB_REPOSITORY']
def request(path,method='GET',data=None,ctype='application/json',host='api.github.com'):
 body=json.dumps(data,ensure_ascii=False).encode() if data is not None and ctype=='application/json' else data
 req=urllib.request.Request('https://'+host+path,data=body,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'AI4S-dataset-publisher'})
 with urllib.request.urlopen(req,timeout=240) as response:
  b=response.read();return json.loads(b) if b else None
source_release=request(f'/repos/{repo}/releases/tags/{SOURCE_TAG}')
source=next(a for a in source_release['assets'] if a['name']==SOURCE_ASSET)
with urllib.request.urlopen(source['browser_download_url'],timeout=180) as response:sourcebytes=response.read()
assert source.get('digest')=='sha256:'+sha(sourcebytes)
with zipfile.ZipFile(io.BytesIO(sourcebytes)) as z:files={Path(n).name:z.read(n) for n in z.namelist() if n.endswith('.txt')}
data=package(files)
releases=request(f'/repos/{repo}/releases?per_page=100')
release=next((r for r in releases if r['tag_name']==TAG),None)
body='当前主分析9,363篇，19个WoS TXT；全样本统一按WoS原始PY统计年度发文量。9,475−8篇内容剔除−104篇PY2027范围外移出＝9,363。原始出版年PY不改写。2026为不完整年度。五幅图及配套CSV已按本版重算，年度统计统一采用PY。详见仓库检索结果.md和reviews/2026-10-27_early/。附件为文献元数据而非论文全文。'
if release is None:
 release=request(f'/repos/{repo}/releases','POST',{'tag_name':TAG,'target_commitish':os.environ.get('GITHUB_SHA','main'),'name':'AI4S v5：9,363篇，统一PY出版年','body':body,'draft':False,'prerelease':False})
request(f'/repos/{repo}/releases/{release["id"]}','PATCH',{'body':body})
existing=next((a for a in release['assets'] if a['name']==ASSET),None)
if existing:
 assert existing['digest']=='sha256:'+sha(data),'Existing v5 differs; preserving it'
 asset=existing
else:asset=request(f'/repos/{repo}/releases/{release["id"]}/assets?name={ASSET}','POST',data,'application/zip','uploads.github.com')
assert asset['size']==len(data) and asset.get('digest')=='sha256:'+sha(data)
print(json.dumps({'records':9363,'files':19,'sha256':sha(data),'url':asset['browser_download_url']}))

