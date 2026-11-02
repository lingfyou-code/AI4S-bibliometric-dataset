from pathlib import Path
import csv,numpy as np,matplotlib as mpl,matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1];S=R/'figures/source_data';F=R/'figures'
def read(n):
 with (S/n).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
cats=read('wc_category_counts.csv')[:15];data=read('wc_annual_counts.csv');years=list(range(2010,2027));lookup={(int(x['PY']),x['WC类别']):int(x['文献数']) for x in data}
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc');mpl.rcParams.update({'font.family':'Microsoft YaHei','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(13,8));bottom=np.zeros(17);colors=['#2F6E94','#C49745','#7B8F50','#B7778E','#D27D42','#78A3BD','#D9B97F','#9FAD7B','#CE9EAE','#E1A57D','#1C4B68','#8D6D31','#526333','#864F65','#96552B']
for k,c in enumerate(cats):
 vals=np.array([lookup[y,c['WC类别']] for y in years]);bars=ax.bar(years,vals,bottom=bottom,label=c['中文对照'],color=colors[k],width=.72);bars[-1].set_hatch('///');bottom+=vals
ax.set_xticks(years);ax.tick_params(axis='x',rotation=45);ax.set(title='主要WoS学科类别年度构成（9,992篇样本；前15类）',xlabel='出版年PY',ylabel='学科归属次数');ax.grid(axis='y',alpha=.15);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),frameon=False,fontsize=9);fig.subplots_adjust(right=.76,bottom=.18)
fig.text(.08,.025,'同篇跨类别可重复计数，柱高不是独立文献总量；未合并其他类别。2026年为不完整年度，以斜线标记。',fontsize=10,color='#63758A')
fig.savefig(F/'wc_annual_stacked.svg',bbox_inches='tight');fig.savefig(F/'wc_annual_stacked.png',bbox_inches='tight',dpi=300);plt.close(fig)
print('Stacked WC chart rebuilt from 9992-record CSVs.')
