"""Render scientific figures from analysis summaries; no source-data writes.

Uses the project's Matplotlib because the bundled Python lacks plotting support.
"""
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
LABELS=['Quadratic','Semicircle','Cubic maximum','Quartic maximum','Quintic maximum']
COLORS={'P001':'#2176ae','P002':'#d97925','P003':'#208b76','P004':'#9564b5'}
POINTS=[0,1,2,3,5,6,7,8]
X=np.array(POINTS)-4
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
profile=pd.read_csv(OUT/'participant_influence_profiles.csv')
paired=pd.read_csv(OUT/'paired_influences.csv')
base=pd.read_csv(OUT/'baseline_summary.csv')
start=pd.read_csv(OUT/'starting_side_effects.csv')

fig,axs=plt.subplots(2,3,figsize=(13,7.6),sharex=True,sharey=True)
for ax,family,label in zip(axs.flat,FAMILIES,LABELS):
    p=profile[(profile.stimulus_set=='curvature_maxima')&(profile.curve_family==family)]
    for pid,color in COLORS.items():
        values=p[p.participant_id==pid].set_index('point').sensitivity.reindex(POINTS)
        ax.plot(X,values,'o-',color=color,lw=1,ms=3,alpha=.6,label=pid)
    ax.plot(X,p.groupby('point').sensitivity.mean().reindex(POINTS),'o-',color='#17212a',lw=2.5,ms=4,label='Participant mean')
    ax.axhline(0,color='#999999',lw=.8);ax.axvspan(-.35,.35,color='#eeeeee')
    ax.set_title(label);ax.set_xticks(X);ax.set_ylim(-1.1,1.7)
axs[1,2].axis('off')
handles,labels=axs[0,0].get_legend_handles_labels()
axs[1,2].legend(handles,labels,loc='upper left',frameon=False)
axs[1,2].text(0,.47,'Missing target is position 0.\nNearest dots are −1 and +1.\n\nEach participant line averages both starts.\nPositive: response follows the perturbation.\nNegative: response shifts oppositely.\n\nN = 4 participants; descriptive results.',va='top',transform=axs[1,2].transAxes,linespacing=1.6)
fig.supylabel('Influence (response pixels / perturbation pixel)')
fig.supxlabel('Ordered dot position relative to target; not physical distance')
fig.suptitle('Matched configurations share a nearest-dot-dominated influence pattern',fontsize=15)
fig.tight_layout(rect=(.02,.03,1,.96));fig.savefig(OUT/'influence_profiles.png',dpi=170);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(13,5.5))
for ax,frame,value,title in [
    (axs[0],base,'curvature_aligned_bias_px','Unperturbed interpolation bias'),
    (axs[1],start,'baseline_positive_minus_negative_start_px','Effect of opposite starting sides')]:
    for pid,color in COLORS.items():
        vals=frame[frame.participant_id==pid].set_index('curve_family')[value].reindex(FAMILIES)
        ax.plot(range(5),vals,'o-',color=color,alpha=.7,label=pid)
    ax.plot(range(5),frame.groupby('curve_family')[value].mean().reindex(FAMILIES),'D-',color='#17212a',lw=2,label='Participant mean')
    ax.set_xticks(range(5),['Quadratic','Semicircle','Cubic','Quartic','Quintic'],rotation=18)
    ax.axhline(0,color='#999999',lw=.8);ax.set_title(title)
axs[0].set_ylabel('Mean bias (px); + toward concave side, − away')
axs[1].set_ylabel('Positive-start minus negative-start response (px)')
axs[1].legend(frameon=False,ncol=2,fontsize=9)
fig.suptitle('Small group biases mask larger individual differences',fontsize=15)
fig.text(.02,.01,'16 baselines per participant per family. Start differences pair the same context; they also contain setting variability.',fontsize=10)
fig.tight_layout(rect=(0,.05,1,.95));fig.savefig(OUT/'baseline_and_starting_side.png',dpi=170);plt.close(fig)

fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True,sharey=True)
for ax,family in zip(axs.flat,['line','cubic','quartic','quintic']):
    p=profile[(profile.stimulus_set=='original')&(profile.curve_family==family)]
    for pid,color in COLORS.items():
        ax.plot(X,p[p.participant_id==pid].set_index('point').sensitivity.reindex(POINTS),'o-',color=color,lw=1,ms=3,alpha=.5,label=pid)
    ax.plot(X,p.groupby('point').sensitivity.mean().reindex(POINTS),'o-',color='#17212a',lw=2.3,label='Original mean')
    if family!='line':
        match=paired[(paired.stimulus_set=='curvature_maxima')&(paired.curve_family==family)&(paired.repetition==1)].groupby('point').sensitivity.mean()
        ax.plot(X,match.reindex(POINTS),'--',color='#b04f42',lw=2,label='Maximum mean (same start)')
    ax.axhline(0,color='#999999',lw=.8);ax.axvspan(-.35,.35,color='#eeeeee');ax.set_title('Original '+family)
    ax.set_xticks(X);ax.set_ylim(-1.25,1.7)
axs[1,1].legend(frameon=False,fontsize=8,ncol=2)
fig.suptitle('Original controls: secondary descriptive comparisons',fontsize=15)
fig.supylabel('Influence (response pixels / perturbation pixel)');fig.supxlabel('Ordered dot position relative to target')
fig.tight_layout(rect=(.02,.03,1,.95));fig.savefig(OUT/'original_profiles.png',dpi=170);plt.close(fig)
