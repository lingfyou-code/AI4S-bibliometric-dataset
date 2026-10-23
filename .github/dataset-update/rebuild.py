"""Reconstruct the frozen dataset from the verified public baseline and a small delta.
Every output file must match the locally verified SHA256 before release publication.
"""
from pathlib import Path
import csv,io,json,re,base64,zlib,hashlib,zipfile,urllib.request,os,sys
HERE=Path(__file__).resolve().parent
BASE_URL='https://github.com/lingfyou-code/AI4S-database/releases/download/data-v3-20261022/AI4S_51._v3_20261022.zip'
BASE_HASH='56a3b87c3f4ca49777af1d642b604ac2c1ac767211bedab83eec99b9e7831b76'
def sha(b):return hashlib.sha256(b).hexdigest()
if len(sys.argv)>1:baseline=Path(sys.argv[1]).read_bytes()
else:
 with urllib.request.urlopen(BASE_URL,timeout=180) as r:baseline=r.read()
assert sha(baseline)==BASE_HASH,'Baseline package hash mismatch'
payload=json.loads(zlib.decompress(base64.b64decode((HERE/'payload.b64').read_text())))
z=zipfile.ZipFile(io.BytesIO(baseline))
oldname=next(n for n in z.namelist() if n.endswith('01_全部10189条_v3筛查审计.csv'))
old=list(csv.DictReader(io.StringIO(z.read(oldname).decode('utf-8-sig'),newline='')))
audit=[]
for r in old:
 x=dict(r)
 if r['当前序号'] in payload['patch']:x.update(payload['patch'][r['当前序号']])
 else:
  x.update({'v4最终分类':r['v3最终分类'],'v4处置来源':'沿用v3','v4复核理由':r['v3复核理由'],'v4核验来源':r['v3核验来源'],'v4证据位置':r['v3证据位置'],'v4证据层级':r['v3证据层级'],'v4仍缺证据':r['v3仍缺证据']})
 audit.append(x)
def csvbytes(rr,fields):
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rr);return s.getvalue().encode('utf-8-sig')
files={n:base64.b64decode(b) for n,b in payload['files'].items()}
files['01_全部10189条_v4筛查审计.csv']=csvbytes(audit,list(audit[0]))
byut={r['WoS编号']:r for r in audit}
for name,spec in payload['csv_refs'].items():files[name]=csvbytes([byut[u] for u in spec['uts']],spec['fields'])
records={}
for n in z.namelist():
 if '核心样本_来源PY保留WoS_TXT/' in n and n.endswith('.txt'):
  text=z.read(n).decode('utf-8-sig').replace('\r\n','\n')
  for b in re.findall(r'^PT .+?^ER[ \t]*$',text,re.M|re.S):records[re.search(r'^UT (.+)$',b,re.M).group(1).strip()]=b
assert len(records)==9470
records.update(payload['new_txt'])
core=[r for r in audit if r['v4最终分类']=='核心样本'];assert len(core)==len(records)==9475
for folder,analysis in [('核心样本_分析归年WoS_TXT',True),('核心样本_来源PY保留WoS_TXT',False)]:
 for start in range(0,len(core),500):
  batch=core[start:start+500];blocks=[]
  for r in batch:
   b=records[r['WoS编号']]
   if analysis:b=re.sub(r'^PY .+$','PY '+r['分析归年'],b,flags=re.M) if re.search(r'^PY .+$',b,re.M) else b.replace('\nER','\nPY '+r['分析归年']+'\nER')
   blocks.append(b)
  files[f'{folder}/download{start+1}-{start+len(batch)}.txt']=('FN Clarivate Analytics Web of Science\nVR 1.0\n'+'\n\n'.join(blocks)+'\n\nEF\n').encode('utf-8-sig')
assert set(files)==set(payload['hashes'])
for name,b in files.items():assert sha(b)==payload['hashes'][name],f'Output hash mismatch: {name}'
target=HERE/'AI4S_core_9475_v4_20261023.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
 for name,b in sorted(files.items()):out.writestr('AI4S_20篇续核及合并_v4_20261023/'+name,b)
print(f'All {len(files)} files verified against the frozen local dataset. Core: 9475; evidence-insufficient: 12.')
if os.environ.get('PUBLISH_DATASET')=='1':
 token=os.environ['GH_TOKEN'];repo=os.environ['GITHUB_REPOSITORY'];tag='data-v4-20261023'
 def api(path,method='GET',data=None,ctype='application/json',host='api.github.com'):
  body=json.dumps(data,ensure_ascii=False).encode() if data is not None and ctype=='application/json' else data
  req=urllib.request.Request('https://'+host+path,data=body,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':ctype,'User-Agent':'AI4S-dataset-publisher'})
  with urllib.request.urlopen(req,timeout=240) as r:return json.load(r)
 import urllib.error
 try:release=api(f'/repos/{repo}/releases/tags/{tag}')
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
  release=api(f'/repos/{repo}/releases','POST',{'tag_name':tag,'target_commitish':os.environ['GITHUB_SHA'],'name':'AI4S配套数据集：9,475篇核心样本','body':'核心分析样本9,475篇；12篇单列为“证据不足未纳入”。附件包含核心CSV、两套WoS TXT、全量筛查审计、逐篇复核记录及筛选流程图。两套TXT择一导入。\n\n全部65个文件已逐一通过与本地冻结数据的SHA256比对。','draft':False,'prerelease':False})
 digest=sha(target.read_bytes());existing=next((a for a in release['assets'] if a['name']==target.name),None)
 if existing:
  assert existing.get('digest')=='sha256:'+digest,'Existing asset differs; not overwritten'
  asset=existing
 else:asset=api(f'/repos/{repo}/releases/{release["id"]}/assets?name={target.name}','POST',target.read_bytes(),'application/zip','uploads.github.com')
 assert asset['size']==target.stat().st_size and asset.get('digest')=='sha256:'+digest
 print('Verified release asset:',asset['browser_download_url'])
