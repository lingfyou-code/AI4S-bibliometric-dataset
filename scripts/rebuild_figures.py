from pathlib import Path
import csv,json,collections,hashlib,shutil,zipfile,math,sys
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
R=Path(__file__).resolve().parent.parent;O=R;SRC=R;F=O/'figures';F.mkdir(exist_ok=True)
def readcsv(name):
 with (SRC/'figures/source_data'/name).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
manifest=json.loads((SRC/'data/current_manifest.json').read_text(encoding='utf-8'));v=json.loads((SRC/'data/figures_validation.json').read_text(encoding='utf-8'))
annual=readcsv('annual_publications.csv');wc=readcsv('wc_category_counts.csv');wy=readcsv('wc_annual_counts.csv');inst=readcsv('institution_top10.csv');flow=readcsv('screening_flow_counts.csv')
N=manifest['current_records'];assert N==10017==v['sample_records']
years=[int(x['PY']) for x in annual];counts=[int(x['篇数']) for x in annual];assert sum(counts)==N and dict(zip(map(str,years),counts))==manifest['annual_counts']
assert len(wc)==161 and sum(int(x['文献数']) for x in wc)==21703
assert sum(int(x['文献数']) for x in wy)==21703 and len(wy)==161*17
wcmap={x['WC类别']:int(x['文献数']) for x in wc};aggregated=collections.Counter()
for a in wy:aggregated[a['WC类别']]+=int(a['文献数'])
assert dict(aggregated)==wcmap
for a in flow:assert int(a['输入文献数'])-int(a['剔除或转出数'])==int(a['剩余文献数'])
assert [int(a['剩余文献数']) for a in flow]==[11513,10993,10017]
assert [int(a['署名文献数']) for a in inst]==[n for _,n in v['top10_institutions']]
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc');mpl.rcParams.update({'font.family':'Microsoft YaHei','svg.fonttype':'none','pdf.fonttype':42,'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'figure.facecolor':'white','savefig.facecolor':'white'})
def save(fig,name):
 for ext in ['png','svg','pdf']:fig.savefig(F/(name+'.'+ext),dpi=300,bbox_inches='tight')
 plt.close(fig)
blue='#2F6E94';grey='#63758A';gold='#CF8A25'
fig,ax=plt.subplots(figsize=(10.5,6.3));ax.plot(years[:-1],counts[:-1],'-o',color=blue,lw=2,ms=4);ax.plot(years[-2:],counts[-2:],'--',color=gold,lw=2);ax.scatter([2026],[counts[-1]],facecolor='white',edgecolor=gold,s=35,zorder=4);ax.axvspan(2025.75,2026.25,color='#FAF0DE',zorder=-1)
for x,y in zip(years,counts):ax.annotate(f'{y:,}',(x,y),xytext=(0,9),textcoords='offset points',ha='center',fontsize=8,color=gold if x==2026 else blue)
ax.set(title='AI4S年度发文量（10,017篇）',xlabel='出版年（WoS原始PY）',ylabel='文献数');ax.set_xticks(years);ax.tick_params(axis='x',labelsize=8);ax.set_ylim(0,3150);ax.grid(axis='y',alpha=.2);fig.text(.12,.01,'2010—2025年用于完整年度比较；2026年为不完整年度，不计算完整年度同比。',fontsize=9,color=grey);save(fig,'fig02_annual_publications')
top=wc[:20];labels=[a['中文对照']+'\n'+a['WC类别'] for a in top];vals=[int(a['文献数']) for a in top]
fig,ax=plt.subplots(figsize=(12,12));ax.barh(range(20),vals,color=blue,height=.65);ax.set_yticks(range(20),labels,fontsize=9);ax.invert_yaxis();ax.set(title='WoS学科分布：前20个原始WC类别',xlabel='文献数（每篇每类别计1次）');ax.set_xlim(0,max(vals)*1.13)
for i,n in enumerate(vals):ax.text(n+12,i,f'{n:,}',va='center',fontsize=9)
ax.grid(axis='x',alpha=.15);fig.subplots_adjust(left=.44,bottom=.08);fig.text(.05,.015,'核心样本10,017篇；WC有效10,011篇，缺失6篇；161个类别共21,703次归属，类别可重叠。',fontsize=9,color=grey);save(fig,'fig03_wc_top20')
top15=wc[:15];lookup={(int(a['PY']),a['WC类别']):int(a['文献数']) for a in wy};arr=np.array([[lookup[y,a['WC类别']] for y in years] for a in top15])
fig,ax=plt.subplots(figsize=(12.5,8.5));c=ax.imshow(arr,cmap='Blues',aspect='auto',vmin=0);ax.set_xticks(range(17),years,rotation=45,ha='right');ax.set_yticks(range(15),[a['中文对照'] for a in top15]);ax.set(title='主要WoS学科类别年度分布（前15类）',xlabel='出版年PY（2026年为不完整年度）')
for i in range(15):
 for j in range(17):ax.text(j,i,str(arr[i,j]) if arr[i,j] else '·',ha='center',va='center',fontsize=7,color='white' if arr[i,j]>arr.max()*.5 else '#243448')
fig.colorbar(c,ax=ax,label='文献数',shrink=.75);fig.subplots_adjust(left=.28,bottom=.15);fig.text(.07,.02,'类别之间可重叠，类别数量之和不等于当年独立文献数；6篇WC缺失未进入统计。',fontsize=9,color=grey);save(fig,'fig04_wc_year_heatmap')
vals=[int(a['署名文献数']) for a in inst];labels=[(a['显示名称'].split('（',1)[1].rstrip('）')+'\n'+a['WoS机构条目']) if '（' in a['显示名称'] else a['WoS机构条目'] for a in inst]
fig,ax=plt.subplots(figsize=(12,8));ax.barh(range(10),vals,color=blue,height=.6);ax.set_yticks(range(10),labels,fontsize=9);ax.invert_yaxis();ax.set(title='机构署名分布：前10个WoS原始C3条目',xlabel='署名文献数');ax.set_xlim(0,450)
for i,n in enumerate(vals):ax.text(n+5,i,str(n),va='center')
ax.grid(axis='x',alpha=.15);fig.subplots_adjust(left=.49,bottom=.12);fig.text(.04,.025,'C3有效9,759篇、缺失258篇；同篇同一条目计1次。机构体系与下属单位可重叠，未追加别名归并。',fontsize=9,color=grey);save(fig,'fig05_institutions_top10')
print('Four statistical figures regenerated from actual 10017-record CSVs.')
