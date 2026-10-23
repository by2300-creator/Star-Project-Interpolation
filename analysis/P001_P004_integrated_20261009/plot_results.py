"""Scientific static plots; project Matplotlib supplies missing bundled capability."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/stars_analysis_mpl')
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parent
FAMILIES=['parabola','circle','cubic','quartic','quintic']
NAMES=['Quadratic','Semicircle','Cubic maximum','Quartic maximum','Quintic maximum']
COLORS={'earlier':'#b56426','controlled':'#2378a7'}
POINTS=[0,1,2,3,5,6,7,8];X=np.array(POINTS)-4
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
p=pd.read_csv(OUT/'observer_influence_profiles.csv')
fig,axs=plt.subplots(2,3,figsize=(13.5,8),sharex=True,sharey=True)
for ax,family,title in zip(axs.flat,FAMILIES,NAMES):
    g=p[(p.stimulus_set=='curvature_maxima')&(p.curve_family==family)]
    for cohort,color in COLORS.items():
        c=g[g.cohort==cohort]
        for observer,o in c.groupby('observer'):
            ax.plot(X,o.set_index('point').sensitivity.reindex(POINTS),color=color,alpha=.24,lw=.8)
        ax.plot(X,c.groupby('point').sensitivity.mean().reindex(POINTS),
                'o--' if cohort=='earlier' else 's-',color=color,lw=2.2,ms=4,
                label='Earlier design: 2 observers' if cohort=='earlier' else 'Controlled design: 4 observers')
    ax.axhline(0,color='#999999',lw=.8);ax.axvspan(-.3,.3,color='#eeeeee');ax.set_xticks(X)
    ax.set_title(title);ax.set_ylim(-1.15,1.65)
axs[1,2].axis('off');handles,labels=axs[0,0].get_legend_handles_labels()
axs[1,2].legend(handles,labels,loc='upper left',frameon=False)
axs[1,2].text(0,.53,'Thin lines: individual observers.\nThick lines: mean within each design.\n\nTarget is the missing position 0.\nAll six are different people.\n\nProfiles describe the tested perturbation size;\nthey do not establish a particular spline model.',va='top',linespacing=1.7,transform=axs[1,2].transAxes)
fig.suptitle('Nearby dots dominate in both designs; family contrasts vary',fontsize=15)
fig.supylabel('Influence: response pixels / perturbation pixel')
fig.supxlabel('Ordered dot position relative to target (not physical distance)')
fig.tight_layout(rect=(.02,.03,1,.96));fig.savefig(OUT/'cohort_influence_profiles.png',dpi=170);plt.close(fig)

c=pd.read_csv(OUT/'observer_primary_contrasts.csv')
contrasts=[f+' minus parabola' for f in FAMILIES[1:]]
fig,ax=plt.subplots(figsize=(10.5,6.1))
for i,contrast in enumerate(contrasts):
    g=c[c.comparison==contrast]
    for cohort,offset in [('earlier',-.12),('controlled',.12)]:
        v=g[g.cohort==cohort].nearest_difference.to_numpy()
        jitter=np.linspace(-.05,.05,len(v))
        ax.scatter(v,i+offset+jitter,color=COLORS[cohort],s=45,marker='o' if cohort=='earlier' else 's',alpha=.8,
                   label=('Earlier observers' if cohort=='earlier' else 'Controlled observers') if i==0 else None)
        ax.scatter(v.mean(),i+offset,marker='|',s=330,linewidths=2.5,color=COLORS[cohort])
    ax.scatter(g.nearest_difference.mean(),i,marker='D',s=55,color='#252d33',label='All-six descriptive mean' if i==0 else None,zorder=4)
ax.axvline(0,color='#777777',lw=1);ax.set_yticks(range(4),['Semicircle − quadratic','Cubic maximum − quadratic','Quartic maximum − quadratic','Quintic maximum − quadratic'])
ax.invert_yaxis();ax.set_xlabel('Difference in nearest-dot influence');ax.set_title('A near-zero combined contrast can hide opposite cohort patterns',pad=16)
ax.legend(loc='lower right',frameon=False,fontsize=9);ax.set_xlim(-.4,.55);ax.set_ylim(3.7,-.5)
fig.text(.03,.02,'Each colored point is one person; vertical marks are cohort means. No confidence or equivalence claim is implied.',fontsize=9)
fig.tight_layout(rect=(0,.05,1,1));fig.savefig(OUT/'configuration_contrasts.png',dpi=170);plt.close(fig)

coords=pd.read_csv(OUT/'canonical_coordinates.csv').groupby(['cohort','stimulus_set','curve_family','point'],as_index=False)[['x_px','y_px']].mean()
configs=[('curvature_maxima',f,n) for f,n in zip(FAMILIES,NAMES)]+[('original',f,'Original '+f) for f in ['line','cubic','quartic','quintic']]
fig,axs=plt.subplots(3,3,figsize=(12.5,10.5),sharex=True,sharey=True)
for ax,(stimulus_set,family,name) in zip(axs.flat,configs):
    for cohort in ['earlier','controlled']:
        g=coords[(coords.cohort==cohort)&(coords.stimulus_set==stimulus_set)&(coords.curve_family==family)&(coords.point!=4)]
        ax.scatter(g.x_px,g.y_px,s=45 if cohort=='earlier' else 14,
                   facecolors='none' if cohort=='earlier' else COLORS[cohort],edgecolors=COLORS[cohort],
                   label='Earlier' if cohort=='earlier' else 'Controlled')
    ax.scatter([0],[0],marker='+',color='#222222',s=35,label='Hidden reference')
    ax.set_title(name);ax.set_aspect('equal',adjustable='box');ax.set_xlim(-340,340);ax.set_ylim(-230,280)
handles,labels=axs[0,0].get_legend_handles_labels()
fig.legend(handles,labels,frameon=False,fontsize=9,ncol=3,loc='upper center',bbox_to_anchor=(.5,.947))
fig.suptitle('Recorded baseline geometry: small changes in maxima, larger changes in originals',fontsize=14)
fig.supxlabel('Distance along target tangent (px)',y=.07);fig.supylabel('Distance along target normal (px)')
fig.text(.06,.025,'Target-centered and pose-aligned for comparison; not screenshots. Orange rings and blue centers overlap when sampling is unchanged.',fontsize=9)
fig.subplots_adjust(left=.08,right=.99,bottom=.13,top=.90,hspace=.32,wspace=.12)
fig.savefig(OUT/'geometry_comparison.png',dpi=170);plt.close(fig)
