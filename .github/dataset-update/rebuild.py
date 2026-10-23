"""Publish only the 19 original-publication-year WoS text files."""
from pathlib import Path
import os,sys,json,zipfile,io,hashlib,re,urllib.request
HERE=Path(__file__).resolve().parent
ASSET='AI4S_9475_WoS_TXT.zip'
FULL='AI4S_core_9475_v4_20261023.zip'
TAG='data-v4-20261023'
EXPECTED={'download1-500.txt': '20185cee9b9f5f08ac2765f2f24438a2e0fb5b4222acbb9b77c5de861ff664b5', 'download1001-1500.txt': '471967ee0602d0b08de7ebe020c9ef2f9d2f99c1a2f7a3417d3d04210bb845c2', 'download1501-2000.txt': '6d7a44c0bee722362599289781c7d6ee53276b52f295315f73ecd18dd15c3f3f', 'download2001-2500.txt': 'a3f158581a1a516efeacd015880ac8ae48e38ddf026a26c0f44c7573ad0a50a8', 'download2501-3000.txt': 'b138e6596e5d977c86b1d7457fb686085b17340b22c562e5eb69fc8f5e0e9d2b', 'download3001-3500.txt': '123433150cc3268ecf4eea431774cdc79a3f42fdaf644898cef6cbd11d2c711b', 'download3501-4000.txt': 'bfe1748544ac53a649b4b24ea871ddb4542efbd7b9b01d43dcfda06d030c346c', 'download4001-4500.txt': '90f46ab6cfcb81673bea7cd0814da8cfe0b07cd70d71b89b7333e103b6d4735e', 'download4501-5000.txt': 'd6b469bf8517c00435ad7be2aa246f79b12ca6b870750b8350c3bb77f050051b', 'download5001-5500.txt': 'a0c52f0e686c7b73337458c8b3c25d374ec159b945b3f364ea3050d331693f6b', 'download501-1000.txt': 'b7a6231352b49abf1a34996888cd7ebe7486b8d352608e5b513ff592d1aec7d2', 'download5501-6000.txt': '193fe5425d4c537486f2eee2c8db172c8941b23cb5580896ed15581efeb7e00c', 'download6001-6500.txt': '5773dea395b80505cf38eeb568fdb078d8177c7d0030ac675a1cb3e5a38ab661', 'download6501-7000.txt': 'e839c0d7848197612e953cc63907381b9452f1069687239695a2d0f8bad85337', 'download7001-7500.txt': 'cc8c4f8201563c313597664b97464c58f77e96451a1a7e7845ba826762a81855', 'download7501-8000.txt': '631397ef30a2b9108b85694467050d11e03509c1394b84ae8ef0568a20dbfc36', 'download8001-8500.txt': 'd525d65c07c0cfffe4c27cef2beab89f03ef215e7fb569ed2be4625f368f46cc', 'download8501-9000.txt': '04425c1fab155e43e81db6de162332b809fe9a99493f8868ad1bc7614e6338ba', 'download9001-9475.txt': '44dcb4778f78868ddb6fbc66afd81fc61643ea461c647c20838ab2da198595d1'}
def sha(b):return hashlib.sha256(b).hexdigest()
def package(data):
 z=zipfile.ZipFile(io.BytesIO(data));files={}
 for name in z.namelist():
  if name.endswith('.txt') and ('核心样本_来源PY保留WoS_TXT/' in name or name.startswith('AI4S_9475_WoS_TXT/')):files[Path(name).name]=z.read(name)
 assert set(files)==set(EXPECTED) and len(files)==19
 uts=[]
 for name,b in files.items():
  assert sha(b)==EXPECTED[name],name
  t=b.decode('utf-8-sig');uts.extend(re.findall(r'^UT (.+)$',t,re.M))
  assert len(re.findall(r'^PT ',t,re.M))==len(re.findall(r'^ER\s*$',t,re.M))
 assert len(uts)==len(set(uts))==9475
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as target:
  for name,b in sorted(files.items()):
   info=zipfile.ZipInfo('AI4S_9475_WoS_TXT/'+name,date_time=(2026,10,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16;target.writestr(info,b,compresslevel=9)
 return out.getvalue()
if len(sys.argv)>1:
 data=package(Path(sys.argv[1]).read_bytes());(HERE/ASSET).write_bytes(data)
 print(json.dumps({'files':19,'records':9475,'only_txt':True,'bytes':len(data),'sha256':sha(data)}));sys.exit()
token=os.environ['GH_TOKEN'];repo=os.environ['GITHUB_REPOSITORY']
def request(path,method='GET',data=None,ctype='application/json',host='api.github.com'):
 body=json.dumps(data,ensure_ascii=False).encode() if data is not None and ctype=='application/json' else data
 req=urllib.request.Request('https://'+host+path,data=body,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'AI4S-dataset-publisher'})
 with urllib.request.urlopen(req,timeout=240) as r:
  b=r.read();return json.loads(b) if b else None
release=request(f'/repos/{repo}/releases/tags/{TAG}')
existing=next((a for a in release['assets'] if a['name']==ASSET),None)
old=next((a for a in release['assets'] if a['name']==FULL),None)
source=existing or old;assert source,'No source dataset asset available'
with urllib.request.urlopen(source['browser_download_url'],timeout=180) as r:sourcebytes=r.read()
assert source.get('digest')=='sha256:'+sha(sourcebytes),'Source download digest mismatch'
data=package(sourcebytes)
if existing:
 assert existing['digest']=='sha256:'+sha(data),'Existing text asset differs; preserving it'
 asset=existing
else:asset=request(f'/repos/{repo}/releases/{release["id"]}/assets?name={ASSET}','POST',data,'application/zip','uploads.github.com')
assert asset['size']==len(data) and asset.get('digest')=='sha256:'+sha(data)
request(f'/repos/{repo}/releases/{release["id"]}','PATCH',{'name':'AI4S配套数据集：9,475篇文献TXT数据','body':'配套数据集仅包含9,475篇核心样本文献的Web of Science纯文本记录，共19个TXT文件，保留来源出版年PY，可用于文献计量软件导入。全部19个文件已核对校验值和文献编号。\n\n附件不含CSV、复核台账及其他过程材料。筛选流程与统计图请查看仓库中的“检索结果.md”。\n\nTXT文件为文献记录，并非论文全文。'})
if old:request(f'/repos/{repo}/releases/assets/{old["id"]}','DELETE')
final=request(f'/repos/{repo}/releases/{release["id"]}')
assert {a['name'] for a in final['assets']}=={ASSET}
print('Verified: only 19 TXT files, 9475 unique records; full audit package removed from this release.')
print(asset['browser_download_url'])

