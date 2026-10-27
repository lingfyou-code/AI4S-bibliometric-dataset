"""Recompute repository SVG figures from the verified 9,363-record WoS ZIP.
Usage: python scripts/rebuild_figures.py PATH_TO_AI4S_9363_WoS_PY_TXT.zip
Standard-library only. Original source fields remain unmodified.
"""
from pathlib import Path
import zipfile,re,json,csv,collections,sys,math,html,hashlib
ROOT=Path(__file__).resolve().parents[1];FIG=ROOT/'figures';DATA=FIG/'source_data'
N=9363;YEARS=list(range(2010,2027));BLUE='#2F6E94';GOLD='#CF8A25';INK='#243448';MUTED='#63758A';GRID='#E6EDF3'
def readcsv(p):
 with open(p,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
trans={d['WC类别']:d['中文对照'] for d in readcsv(DATA/'wc_category_counts.csv')}
instlabels={d['WoS机构条目']:d['显示名称'] for d in readcsv(DATA/'institution_top10.csv')}
records=[]
with zipfile.ZipFile(sys.argv[1]) as z:
 assert len(z.namelist())==19
 for name in z.namelist():
  for block in re.findall(r'^PT .*?^ER\s*$',z.read(name).decode('utf-8-sig'),re.M|re.S):
   d={};key=None
   for line in block.splitlines():
    if re.match(r'^[A-Z0-9]{2} ',line):key=line[:2];d[key]=line[3:]
    elif line.startswith('   ') and key:d[key]+=' '+line.strip()
   records.append(d)
assert len(records)==len({d['UT'] for d in records})==N
assert all(d.get('PY') and 2010<=int(d['PY'])<=2026 for d in records)
def values(d,k):return set(x.strip() for x in d.get(k,'').split(';') if x.strip())
annual=collections.Counter(int(d['PY']) for d in records);wc=collections.Counter();inst=collections.Counter();wy=collections.Counter()
for d in records:
 wc.update(values(d,'WC'));inst.update(values(d,'C3'))
 for c in values(d,'WC'):wy[(int(d['PY']),c)]+=1
rank=sorted(wc,key=lambda k:(-wc[k],k));irank=sorted(inst,key=lambda k:(-inst[k],k))
assert len(wc)==153 and set(rank)<=set(trans)
missing_wc=sum(not d.get('WC') for d in records);missing_c3=sum(not d.get('C3') for d in records)
def writecsv(p,header,rows):
 with open(p,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.writer(f);w.writerow(header);w.writerows(rows)
writecsv(DATA/'annual_publications.csv',['PY','篇数','年度状态'],[(y,annual[y],'不完整年度' if y==2026 else '完整年度') for y in YEARS])
writecsv(DATA/'wc_category_counts.csv',['WC类别','中文对照','文献数','占9363篇核心样本比例'],[(c,trans[c],wc[c],f'{wc[c]/N:.10f}') for c in rank])
writecsv(DATA/'wc_annual_counts.csv',['PY','WC类别','中文对照','文献数'],[(y,c,trans[c],wy[y,c]) for y in YEARS for c in rank])
writecsv(DATA/'institution_top10.csv',['WoS机构条目','显示名称','署名文献数','占核心样本比例'],[(c,instlabels.get(c,c),inst[c],f'{inst[c]/N:.10f}') for c in irank[:10]])
writecsv(DATA/'screening_flow_counts.csv',['阶段','输入文献数','剔除或转出数','剩余文献数'],[('初步筛查与撤稿处理',11637,1322,10315),('模型辅助初审与领域筛选',10315,126,10189),('内容、原创性与出版关系核验',10189,722,9467),('出版年份范围核对',9467,104,9363)])
class SVG:
 def __init__(self,w,h,title,desc):
  self.w=w;self.h=h;self.a=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',f'<title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc>', '<style>text{font-family:"Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif}</style>',f'<rect width="{w}" height="{h}" fill="white"/>']
 def text(self,x,y,s,size=16,color=INK,anchor='start',weight='400'):
  self.a.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(str(s))}</text>')
 def line(self,x1,y1,x2,y2,color=GRID,width=1,dash=None,marker=None):
  self.a.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+(f' marker-end="url(#{marker})"' if marker else '')+'/>')
 def rect(self,x,y,w,h,fill,stroke=None,rx=0,extra=''):
  self.a.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" fill="{fill}" rx="{rx}"'+(f' stroke="{stroke}"' if stroke else '')+f' {extra}/>')
 def circle(self,x,y,r,fill,stroke=BLUE):self.a.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
 def save(self,name):
  self.a.append('</svg>');(FIG/name).write_text('\n'.join(self.a)+'\n')
 def header(self,title,subtitle):self.text(60,49,title,30,weight='700');self.text(60,85,subtitle,17,MUTED)
# 1. Annual PY count, incomplete last year distinguished by line and marker.
s=SVG(1040,580,'AI4S年度发文量','9363篇；2010—2026年；全样本按WoS出版年PY统计，2026为不完整年度。')
s.header('AI4S年度发文量','核心样本 9,363 篇｜2010—2026年｜按WoS出版年PY统计')
x0,x1,y0,y1=92,980,455,135
xf=lambda y:x0+(y-2010)/(2026-2010)*(x1-x0)
yf=lambda v:y0-v/3000*(y0-y1)
s.rect(xf(2026)-22,y1,44,y0-y1,'#FAF0DE')
for v in range(0,3001,500):s.line(x0,yf(v),x1+14,yf(v));s.text(x0-13,yf(v)+5,f'{v:,}',14,MUTED,'end')
s.line(x0,y1,x0,y0,'#B9C4CF');s.line(x0,y0,x1+14,y0,'#B9C4CF')
for y in YEARS:
 s.text(xf(y),y0+28,y,13,MUTED,'middle')
 if y>2010:s.line(xf(y-1),yf(annual[y-1]),xf(y),yf(annual[y]),GOLD if y==2026 else BLUE,3,'8 5' if y==2026 else None)
 s.circle(xf(y),yf(annual[y]),4,'white' if y==2026 else BLUE,GOLD if y==2026 else BLUE)
 s.text(xf(y),yf(annual[y])-16,f'{annual[y]:,}',14,GOLD if y==2026 else BLUE,'middle')
s.text(535,516,'出版年（PY）',17,anchor='middle');s.text(30,122,'篇数',15,MUTED)
s.text(92,554,'注：2026年为不完整年度，以虚线、空心点及浅色背景标记。',15,MUTED)
s.save('annual_publications.svg')
# 2. Full-counting WC top20; labels retained in English and Chinese.
s=SVG(1420,1280,'AI4S文献WoS学科分布（前20类）',f'9363篇核心样本，{N-missing_wc}篇有WC；类别可重叠，共{len(wc)}类。')
s.header('AI4S文献的WoS学科分布',f'原始WC类别（前20类）｜核心样本 9,363 篇；其中{N-missing_wc:,}篇有WC标注')
x0,x1,yt,yb=620,1330,140,1125
for v in range(0,1801,300):
 x=x0+v/1800*(x1-x0);s.line(x,yt,x,yb);s.text(x,yb+28,f'{v:,}',14,MUTED,'middle')
s.line(x0,yb,x1,yb,'#B9C4CF')
for i,c in enumerate(rank[:20]):
 y=yt+27+i*48.5;s.rect(x0,y-11,wc[c]/1800*(x1-x0),24,'#507E99',extra=f'data-count="{wc[c]}" data-category="{html.escape(c,quote=True)}"')
 s.text(x0-14,y-2,c,14,'#3C5367','end');s.text(x0-14,y+19,trans[c],13,MUTED,'end');s.text(x0+wc[c]/1800*(x1-x0)+9,y+6,f'{wc[c]:,}',15,BLUE)
s.text(975,1190,'文献数（篇）',18,anchor='middle');s.text(60,1228,'注：同篇文献在每个所属WC类别中各计1次，类别之间可重叠；比例分母统一为9,363篇。',16,MUTED)
s.text(60,1258,f'{missing_wc}篇缺少WC字段，未进入学科统计；完整153类见配套汇总数据。',16,MUTED)
s.save('wc_distribution_top20.svg')
# 3. Stacked top15 WC categories across all PY years.
colors=['#2F6E94','#C49745','#7B8F50','#B7778E','#D27D42','#78A3BD','#D9B97F','#9FAD7B','#CE9EAE','#E1A57D','#1C4B68','#8D6D31','#526333','#864F65','#96552B']
top=rank[:15];totals={y:sum(wy[y,c] for c in top) for y in YEARS};maximum=math.ceil(max(totals.values())/500)*500
s=SVG(1580,900,'主要WoS学科类别的年度分布','9363篇样本，统一PY；前15类别重叠计数，柱高不是独立文献量；2026年不完整。')
s.header('主要WoS学科类别的年度分布','核心样本 9,363 篇｜前15个WC类别｜按WoS出版年PY统计')
s.a.append('<defs><pattern id="incomplete" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M-2 2 L2 -2 M0 9 L9 0 M7 11 L11 7" stroke="#243448" stroke-width="1" opacity="0.45"/></pattern></defs>')
x0,x1,y0,y1=100,1105,715,155
xf=lambda y:x0+32+(y-2010)*(x1-x0-64)/16
yf=lambda v:y0-v/maximum*(y0-y1)
for v in range(0,maximum+1,500):s.line(x0,yf(v),x1,yf(v));s.text(x0-13,yf(v)+5,f'{v:,}',14,MUTED,'end')
s.line(x0,y1,x0,y0,'#B9C4CF');s.line(x0,y0,x1,y0,'#B9C4CF');s.text(100,131,'学科归属次数',16,MUTED)
for y in YEARS:
 bottom=0
 for i,c in enumerate(top):
  v=wy[y,c];s.rect(xf(y)-21,yf(bottom+v),42,v/maximum*(y0-y1),colors[i],extra=f'data-year="{y}" data-category="{html.escape(c,quote=True)}" data-count="{v}"');bottom+=v
 if y==2026:s.rect(xf(y)-21,yf(bottom),42,bottom/maximum*(y0-y1),'url(#incomplete)')
 s.text(xf(y),y0+28,y,14,MUTED,'middle')
for i,c in enumerate(top):
 y=170+i*34;s.rect(1150,y-12,19,19,colors[i]);s.text(1180,y+3,trans[c],16)
s.text(605,784,'出版年（PY）',18,anchor='middle')
s.text(60,837,'注：只展示累计文献数前15个WC类别，不合并“其他”；同篇跨类别可重复计数，柱高不是独立文献总量。',16,MUTED)
s.text(60,870,'2026年为不完整年度，以斜线标记；完整153类及其各年数据见配套CSV。',16,MUTED)
s.save('wc_annual_stacked.svg')
# 4. Institution full counting from C3, without added alias merging.
s=SVG(1420,940,'AI4S机构署名分布','9363篇样本；前10个C3机构条目；同篇同一机构一次，层级可重叠。')
s.header('AI4S机构署名分布',f'前10个WoS机构条目｜核心样本 9,363 篇；其中{N-missing_c3:,}篇有C3标注')
x0,x1,yt,yb=630,1320,150,760
for v in range(0,451,50):
 x=x0+v/450*(x1-x0);s.line(x,yt,x,yb);s.text(x,yb+28,v,15,MUTED,'middle')
s.line(x0,yb,x1,yb,'#B9C4CF')
for i,c in enumerate(irank[:10]):
 y=yt+31+i*59;s.rect(x0,y-13,inst[c]/450*(x1-x0),28,BLUE,extra=f'data-count="{inst[c]}"')
 label=instlabels.get(c,c);ch=label.split('（',1)[1].rstrip('）') if '（' in label else ''
 s.text(x0-17,y-2,c,16,'#3C5367','end');s.text(x0-17,y+20,'（'+ch+'）' if ch else '',15,MUTED,'end');s.text(x0+inst[c]/450*(x1-x0)+11,y+7,inst[c],18,BLUE)
s.text(980,826,'署名文献数（篇）',19,anchor='middle')
s.text(60,874,'注：同篇同一机构条目计1次；机构体系与下属单位可能重叠，其数量不相加。',16,MUTED)
s.text(60,907,f'英文沿用WoS原C3条目，中文仅作对照，未追加机构别名归并；{missing_c3}篇缺少C3字段。',16,MUTED)
s.save('institution_distribution.svg')
# 5. Monotone screening flow; right-facing arrows always indicate removals.
s=SVG(1320,1440,'WoS文献检索与筛选流程','11637→10315→10189→9467→9363；依次移出1322、126、722、104；右侧为剔除或转出。')
s.header('WoS文献检索与筛选流程','逐轮筛选｜早期复核并入内容核验｜最终按出版年PY限定2010—2026年')
s.a.append('<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#6B7E90"/></marker></defs>')
s.text(365,128,'保留文献',19,BLUE,'middle','700');s.text(1000,128,'剔除 / 转出主分析样本',19,'#A56B2A','middle','700')
node_labels=[('原始WoS候选记录',11637),('初步筛查后保留',10315),('领域筛选后保留',10189),('内容核验后保留',9467),('最终核心分析样本',9363)]
ypositions=[155,405,655,905,1155]
for i,((label,n),y) in enumerate(zip(node_labels,ypositions)):
 s.rect(90,y,550,106,'#E9F2F7' if i==4 else '#F4F8FB',BLUE if i==4 else '#BBCBD8',8)
 s.text(365,y+35,label,21,anchor='middle',weight='700');s.text(365,y+80,f'{n:,}篇',33,BLUE,'middle','700')
 if i<4:
  s.line(365,y+106,365,ypositions[i+1]-10,'#6B7E90',2.3,marker='arrow');s.line(365,y+177,727,y+177,'#6B7E90',2.3,marker='arrow')
labels=[('第一轮：初步筛查与撤稿处理',['非目标、纯综述等：1,318篇','明确撤稿记录：4篇'],'本轮剔除：1,322篇'),('第二轮：模型辅助初审与领域筛选',['交通、金融、临床诊疗等','不符合研究范围的文献'],'本轮剔除：126篇'),('第三轮：内容、原创性与出版关系核验',['内容排除、转拓展及资格证据不足','重复 / 撤稿旧版；含早期复核8篇'],'本轮剔除或转出：722篇'),('第四轮：出版年份范围核对',['全样本统一采用出版年PY','移出PY为2027的范围外记录'],'本轮移出：104篇')]
for i,(label,lines,total) in enumerate(labels):
 y=ypositions[i]+119;s.rect(745,y,505,142,'#FCF7EF','#D7BC94',7)
 s.text(766,y+29,label,19,weight='700')
 for j,line in enumerate(lines):s.text(766,y+59+j*27,line,17,'#68594A')
 s.text(766,y+121,total,19,'#A56B2A',weight='700')
s.text(60,1328,'数量核对：11,637－1,322－126－722－104＝9,363篇。',20,BLUE,weight='700')
s.text(60,1367,'注：按最终处置汇总筛选步骤；疑点文献在候选池内核验，符合标准者保留在主线。',17,MUTED)
s.text(60,1401,'第三轮包括早期复核；转拓展参考不计主分析，资格证据不足与内容不相关分别记录。',17,MUTED)
s.save('screening_flow.svg')
# Evidence ledger and data checks for all plotted values.
assert sum(annual.values())==N
assert sum(wc.values())==sum(wy.values())
assert sum(wc.values())==sum(len(values(d,'WC')) for d in records)
assert sum(inst.values())==sum(len(values(d,'C3')) for d in records)
validation={'sample_records':N,'unique_ut':N,'year_field':'PY','years':YEARS,'annual_counts':dict(sorted(annual.items())),'wc_categories':len(wc),'wc_missing':missing_wc,'wc_valid':N-missing_wc,'wc_memberships':sum(wc.values()),'C3_missing':missing_c3,'C3_valid':N-missing_c3,'top10_institutions':[(c,inst[c]) for c in irank[:10]],'screening_counts':[11637,10315,10189,9467,9363],'screening_removals':[1322,126,722,104],'source_zip_sha256':hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest(),'files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(FIG.rglob('*')) if p.is_file()}}
(ROOT/'data').mkdir(exist_ok=True);(ROOT/'data/figures_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in validation.items() if k!='files_sha256'},ensure_ascii=False,indent=2))
