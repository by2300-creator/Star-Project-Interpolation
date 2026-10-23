"""Static scientific figures from saved summaries; no raw-data modifications.

Project Matplotlib is used because the bundled analysis Python lacks it.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/stars_analysis_mpl')
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT=Path(__file__).resolve().parent
FAMILIES=['parabola','circle','cubic','quartic','quintic']
LABELS=['Quadratic','Semicircle','Cubic maximum','Quartic maximum','Quintic maximum']
SHORT=['Quadratic','Semicircle','Cubic','Quartic','Quintic']
PID=[f'P{i:03d}' for i in range(1,11)]
COLORS=dict(zip(PID,['#2474a6','#d47a24','#279175','#9a68ae','#c44758','#71822c','#6d829b','#a84e18','#2b9fad','#594e98']))
POINTS=[0,1,2,3,5,6,7,8];X=np.array(POINTS)-4
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
profile=pd.read_csv(OUT/'participant_influence_profiles.csv')
base=pd.read_csv(OUT/'baseline_summary.csv')
fi=pd.read_csv(OUT/'family_intervals.csv')
ci=pd.read_csv(OUT/'primary_contrast_intervals.csv')
contrasts=pd.read_csv(OUT/'primary_contrasts.csv')

fig,axs=plt.subplots(2,3,figsize=(13.5,8),sharex=True,sharey=True)
matched=profile[profile.stimulus_set=='curvature_maxima']
for ax,family,label in zip(axs.flat,FAMILIES,LABELS):
    g=matched[matched.curve_family==family]
    for pid,color in COLORS.items():
        y=g[g.participant_id==pid].set_index('point').sensitivity.reindex(POINTS)
        ax.plot(X,y,'o-' if pid in PID[:7] else '^-',color=color,lw=1,ms=3,alpha=.45 if pid in PID[:7] else .75,
                label=pid+(' (new)' if pid in PID[7:] else ''))
    ax.plot(X,g.groupby('point').sensitivity.mean().reindex(POINTS),'o-',color='#142330',lw=2.7,ms=4,label='Ten-person mean')
    ax.axhline(0,color='#999999',lw=.8);ax.axvspan(-.3,.3,color='#eeeeee')
    ax.set_title(label);ax.set_xticks(X)
low=min(-.8,matched.sensitivity.min()-.15);high=max(1.5,matched.sensitivity.max()+.15)
axs[0,0].set_ylim(low,high)
axs[1,2].axis('off')
handles,labels=axs[0,0].get_legend_handles_labels()
axs[1,2].legend(handles,labels,loc='upper left',frameon=False,ncol=2,fontsize=9)
axs[1,2].text(0,.37,'Missing target is position 0.\nNearest dots are −1 and +1.\n\nPositive: response follows the perturbation.\nNegative: response shifts oppositely.\n\nEach person averages both starting sides.\nAll ten used the same v9 protocol.\nOctober 5 recordings are excluded.',va='top',fontsize=9,linespacing=1.4,transform=axs[1,2].transAxes)
fig.suptitle('Nearest dots strongly influence interpolation across configurations',fontsize=15)
fig.supylabel('Influence (response pixels / perturbation pixel)')
fig.supxlabel('Ordered dot position relative to target; not physical distance')
fig.tight_layout(rect=(.02,.03,1,.96));fig.savefig(OUT/'influence_profiles.png',dpi=170);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(13.5,6.1))
for ax,value,outcome,title in [
    (axs[0],'mean_abs_px','mean_absolute_error_px','Absolute baseline error'),
    (axs[1],'curvature_aligned_bias_px','curvature_aligned_bias_px','Signed baseline bias')]:
    for pid,color in COLORS.items():
        y=base[base.participant_id==pid].set_index('curve_family')[value].reindex(FAMILIES)
        ax.plot(range(5),y,'o-' if pid in PID[:7] else '^-',color=color,lw=1,ms=4,alpha=.65)
    stats=fi[fi.outcome==outcome].set_index('curve_family').reindex(FAMILIES)
    ax.errorbar(range(5),stats['mean'],yerr=np.array([stats['mean']-stats.lower_95,stats.upper_95-stats['mean']]),
                fmt='D-',lw=2,color='#142330',capsize=4,ms=5,zorder=5)
    ax.axhline(0,color='#999999',lw=.8)
    ax.set_xticks(range(5),SHORT,rotation=15);ax.set_title(title)
axs[0].set_ylabel('Mean absolute error (px)')
axs[1].set_ylabel('Mean bias (px); positive = toward concave side')
fig.suptitle('Individual baseline settings vary more than the group biases',fontsize=15)
legend=[Line2D([0],[0],color=c,marker='o' if pid in PID[:7] else '^',label=pid+(' (new)' if pid in PID[7:] else '')) for pid,c in COLORS.items()]
legend.append(Line2D([0],[0],color='#142330',marker='D',label='Mean + exploratory 95% interval'))
fig.legend(handles=legend,loc='lower center',ncol=4,frameon=False,fontsize=8.5,bbox_to_anchor=(.5,.045))
fig.text(.03,.015,'16 baselines per person per family. Intervals resample whole participants; unadjusted for multiple comparisons.',fontsize=9)
fig.tight_layout(rect=(0,.22,1,.94));fig.savefig(OUT/'baseline_accuracy.png',dpi=170);plt.close(fig)

fig,axs=plt.subplots(1,2,figsize=(13.5,6.4),sharey=True)
names=['Semicircle − quadratic','Cubic max − quadratic','Quartic max − quadratic','Quintic max − quadratic']
for ax,outcome,title,xlabel in [
    (axs[0],'nearest_sensitivity_difference','Nearest-dot influence','Difference in response px / perturbation px'),
    (axs[1],'bias_difference_px','Signed baseline bias','Difference in curvature-aligned bias (px)')]:
    for i,family in enumerate(FAMILIES[1:]):
        g=contrasts[contrasts.comparison==family+' minus parabola'].set_index('participant_id')
        for k,pid in enumerate(PID):
            ax.scatter(g.loc[pid,outcome],i+(k-4.5)*.042,s=32,color=COLORS[pid],
                       marker='o' if pid in PID[:7] else '^',alpha=.8,zorder=4)
        r=ci[(ci.comparison==family+' minus parabola')&(ci.outcome==outcome)].iloc[0]
        ax.errorbar(r['mean'],i+.30,xerr=[[r['mean']-r.lower_95],[r.upper_95-r['mean']]],
                    fmt='D',color='#142330',lw=2,capsize=4,ms=5,zorder=5)
    ax.axvline(0,color='#888888',lw=1);ax.set_title(title);ax.set_xlabel(xlabel)
    ax.set_yticks(range(4),names);ax.set_ylim(3.7,-.5)
fig.suptitle('Primary contrasts: participant differences and ten-person means',fontsize=15)
fig.legend(handles=legend,loc='lower center',ncol=4,frameon=False,fontsize=8.5,bbox_to_anchor=(.5,.04))
fig.text(.03,.012,'Black diamonds: means; bars: exploratory 95% participant-bootstrap intervals. These are not equivalence tests.',fontsize=9)
fig.tight_layout(rect=(0,.22,1,.94));fig.savefig(OUT/'primary_contrasts.png',dpi=170);plt.close(fig)

lr=pd.read_csv(OUT/'participant_left_right_summary.csv')
start=pd.read_csv(OUT/'starting_side_effects.csv').groupby('participant_id').baseline_positive_minus_negative_start_px.mean()
fig,axs=plt.subplots(1,2,figsize=(11.5,6.3))
for ax,values,title,xlabel in [
    (axs[0],lr.set_index('participant_id').point3_minus_point5,'Nearest-dot side asymmetry','Dot 3 influence minus dot 5 influence'),
    (axs[1],start,'Starting-side difference','Positive-start minus negative-start baseline (px)')]:
    for i,pid in enumerate(PID):
        ax.plot([0,values[pid]],[i,i],color=COLORS[pid],lw=1.5)
        ax.scatter(values[pid],i,color=COLORS[pid],s=50,marker='o' if pid in PID[:7] else '^')
    ax.axvline(0,color='#999999',lw=.8);ax.set_yticks(range(10),[p+(' (new)' if p in PID[7:] else '') for p in PID])
    ax.invert_yaxis();ax.set_xlabel(xlabel);ax.set_title(title)
fig.suptitle('Directional effects vary across participants',fontsize=15)
fig.text(.03,.02,'Each value averages the five matched families. Starting-side differences also contain ordinary response variability.',fontsize=9)
fig.tight_layout(rect=(0,.065,1,.94));fig.savefig(OUT/'direction_and_starting_side.png',dpi=170);plt.close(fig)

diagnostic=pd.read_csv(OUT/'P008_contrast_sensitivity.csv')
fig,axs=plt.subplots(1,2,figsize=(12,5.6),sharey=True)
for ax,outcome,title,xlabel in [
    (axs[0],'nearest_sensitivity_difference','Nearest-dot influence','Difference in response px / perturbation px'),
    (axs[1],'bias_difference_px','Signed baseline bias','Difference in curvature-aligned bias (px)')]:
    values=diagnostic[diagnostic.outcome==outcome].set_index('comparison').reindex([f+' minus parabola' for f in FAMILIES[1:]])
    for column,label,color,marker,offset in [
        ('all_ten_mean','All ten: primary analysis','#142330','D',-.14),
        ('without_P008_mean','Without P008: diagnostic only','#2474a6','s',0),
        ('participant_median','Median of ten participant contrasts','#a84e18','o',.14)]:
        ax.scatter(values[column],np.arange(4)+offset,label=label,color=color,marker=marker,s=55)
    ax.axvline(0,color='#999999',lw=.8);ax.set_title(title);ax.set_xlabel(xlabel)
    ax.set_yticks(range(4),names);ax.set_ylim(3.5,-.5)
fig.suptitle('P008 changes effect sizes; semicircle and cubic mean directions persist',fontsize=14)
handles,labels=axs[0].get_legend_handles_labels()
fig.legend(handles,labels,loc='lower center',ncol=1,frameon=False,bbox_to_anchor=(.5,.025))
fig.text(.02,.008,'Post-hoc sensitivity checks; P008 remains in the primary analysis. No equivalence or significance claim.',fontsize=9)
fig.tight_layout(rect=(0,.20,1,.94));fig.savefig(OUT/'participant_sensitivity.png',dpi=170);plt.close(fig)
