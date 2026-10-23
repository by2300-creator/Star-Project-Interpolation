"""Read-only descriptive audit of the supplied pilot; no rows are excluded."""
from pathlib import Path
import json, sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from run_exp import build_trials, parse_args, materialize_trial
OUT=Path(__file__).resolve().parent
stem=ROOT/'data/pilot_identification_s1_20260925_163247_752794'
t=pd.read_csv(str(stem)+'_trials.csv'); p=pd.read_csv(str(stem)+'_presses.csv')
assert t.trial_uid.equals(p.trial_uid) and t.trial.equals(p.trial)
assert not t.trial_uid.duplicated().any()
assert t.trial.tolist()==list(range(1,253))
assert np.isfinite(t[['response_normal_px','reaction_time_ms','total_moves']]).all().all()
expected=build_trials(parse_args([]))
assert [s['trial_uid'] for s in expected]==t.trial_uid.tolist()
maxcoord=0
for s,(_,row) in zip(expected,t.iterrows()):
    points,meta=materialize_trial(s,63)
    for i in range(9):
        maxcoord=max(maxcoord,abs(row[f'x{i}_math']-points.loc[i,'x']),abs(row[f'y{i}_math']-points.loc[i,'y']))
print('max difference from regenerated coordinates',maxcoord)
cols=sorted([c for c in p if c.startswith('press_')],key=lambda c:int(c.split('_')[1]))
checks=[]
for (_,r),(_,b) in zip(t.iterrows(),p.iterrows()):
    pos=np.array([r.initial_movable_x_px,r.initial_movable_y_px],float)
    last=None; game=0; cumulative=0; base=0; steps=[]; manual=0
    for c in cols:
        if pd.isna(b[c]):continue
        action,num=b[c].rsplit('_',1)
        if action.startswith('step_'):
            base={'step_small':2,'step_medium':1,'step_big':0}[action]
            game=0;last=None;manual+=1
        else:
            assert action in ('up','down')
            if last is not None and action!=last:game+=1;cumulative+=1
            step=[10,5,1][min(2,base+min(game,2))];steps.append(step)
            target=np.array([r[f'ref_{action}_x_px'],r[f'ref_{action}_y_px']])
            d=target-pos;dist=np.linalg.norm(d)
            pos=target if dist<=step else pos+d*step/dist
            last=action
        assert int(num)==cumulative
    checks.append(dict(trial=r.trial,manual=manual,reversals=cumulative,one_px=sum(s==1 for s in steps),five_px=sum(s==5 for s in steps),ten_px=sum(s==10 for s in steps),replay_error=float(np.linalg.norm(pos-[r.final_x_px,r.final_y_px])),moves_match=len(steps)==r.total_moves))
q=pd.DataFrame(checks);t=t.merge(q,on='trial',validate='one_to_one')
print('KEYS',q.sum(numeric_only=True).to_dict(),'max replay',q.replay_error.max())
print('BEHAVIOR',{'no_reversal':int((q.reversals==0).sum()),'any_1px':int((q.one_px>0).sum()),'any_manual':int((q.manual>0).sum()),'on10px':int(np.isclose(t.response_normal_px/10,np.round(t.response_normal_px/10),atol=1e-8).sum()),'zero':int(np.isclose(t.response_normal_px,0,atol=1e-8).sum()),'no_moves':int((t.total_moves==0).sum()),'total_minutes':t.reaction_time_ms.sum()/60000})
g=t.groupby(['curve_family','target_index']).agg(n=('trial','size'),mean_signed_px=('response_normal_px','mean'),median_signed_px=('response_normal_px','median'),mean_abs_px=('response_abs_px','mean'),median_abs_px=('response_abs_px','median'),sd_signed_px=('response_normal_px','std'),median_rt_ms=('reaction_time_ms','median'),one_px_trials=('one_px',lambda x:(x>0).sum()))
print('BY TARGET\n',g.round(3).to_string());g.to_csv(OUT/'family_target_summary.csv')
print('START',t.groupby('initial_side').response_normal_px.agg(['mean','median']).to_string())
print('QUARTERS',t.groupby((t.trial-1)//63).agg(rt=('reaction_time_ms','median'),abs=('response_abs_px','mean'),fine=('one_px',lambda x:(x>0).sum())).to_string())
s=t[t.condition_type=='single']; pairs=[]
for (stim,i),group in s.groupby(['stimulus_id','perturb_index']):
    a=group[group.perturb_sign==1].iloc[0];b=group[group.perturb_sign==-1].iloc[0]
    assert a.initial_side==b.initial_side
    pairs.append(dict(stimulus_id=stim,curve_family=a.curve_family,target_index=int(a.target_index),point=int(i),distance=abs(int(i)-int(a.target_index)),J=(a.response_normal_units-b.response_normal_units)/(a.perturb_units-b.perturb_units),response_difference_px=a.response_normal_px-b.response_normal_px,delta_px=abs(a.perturb_pixels),plus_trial=a.trial,minus_trial=b.trial,no_move=(a.total_moves==0 or b.total_moves==0)))
j=pd.DataFrame(pairs);j.to_csv(OUT/'matched_influences.csv',index=False)
print('SHIFTS',j.delta_px.describe().to_string()); print('J SUMMARY',j.J.describe().to_string())
print('J nearfar',j.assign(neighbor=j.distance==1).groupby('neighbor').J.agg(['size','mean','median']).to_string())
print('J by family',j.groupby('curve_family').J.agg(['mean','median','min','max']).round(3).to_string())
print('J count',{'positive':int((j.J>1e-8).sum()),'zero':int((j.J.abs()<1e-8).sum()),'negative':int((j.J< -1e-8).sum()),'no_move_affected':j[j.no_move].to_dict('records')})
base=t[t.condition_type=='baseline'].set_index('stimulus_id'); paired=[]
for _,r in t[t.condition_type=='paired'].iterrows():
    indices=json.loads(r.perturb_indices); signs=json.loads(r.perturb_signs)
    singles=[s[(s.stimulus_id==r.stimulus_id)&(s.perturb_index==i)&(s.perturb_sign==sign)].iloc[0] for i,sign in zip(indices,signs)]
    b=base.loc[r.stimulus_id]
    pred=sum(x.response_normal_px for x in singles)-b.response_normal_px
    paired.append(dict(trial=r.trial,curve_family=r.curve_family,target_index=r.target_index,observed_px=r.response_normal_px,predicted_px=pred,residual_px=r.response_normal_px-pred,all_start_matched=all(x.initial_side==r.initial_side for x in singles) and b.initial_side==r.initial_side))
f=pd.DataFrame(paired);f.to_csv(OUT/'paired_comparisons.csv',index=False)
print('SUPERPOSITION',f.residual_px.describe().to_string(),'mae',f.residual_px.abs().mean(),'allstartmatched',f.all_start_matched.sum())
print('BASELINE OFFSET corrected',t.assign(centered=t.response_normal_px-t.stimulus_id.map(base.response_normal_px)).groupby('curve_family').centered.agg(['mean','std']).round(3).to_string())
print('BASE GEOMETRY',t.drop_duplicates('stimulus_id')[['curve_family','target_index','target_analytic_curvature_baseline','target_curvature_baseline','local_dkappa_ds_rms_baseline','rotation_deg','reversed','display_scale_px_per_unit']].sort_values(['curve_family','target_index']).to_string(index=False))
# Descriptive plots: no inferential confidence intervals from one setting per condition.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
order=['line','parabola','cubic','quartic','quintic','circle']
fig,axes=plt.subplots(1,2,figsize=(12,4.8),layout='constrained')
for target,color,offset in [(3,'#26788e',-.17),(4,'#bf5b32',.17)]:
    vals=[g.loc[(fam,target),'mean_abs_px'] for fam in order]
    axes[0].bar(np.arange(6)+offset,vals,.32,label=f'Target {target}',color=color)
axes[0].set(xticks=range(6),xticklabels=order,ylabel='Mean absolute distance from hidden reference (pixels)',title='Quartic midpoint produces the largest offsets')
axes[0].legend(); axes[0].tick_params(axis='x',rotation=25)
axes[1].hist(t.response_normal_px,bins=np.arange(-22.5,77.5,5),color='#26788e',edgecolor='white')
axes[1].set(xlabel='Signed response (pixels; positive toward Z)',ylabel='Trials',title='Responses cluster at coarse adjustment positions')
fig.suptitle('One completed pilot session • 252 trials • descriptive results',fontsize=13)
fig.savefig(OUT/'pilot_summary.png',dpi=170);plt.close(fig)
fig,axes=plt.subplots(2,3,figsize=(12,7),layout='constrained',sharey=True)
for ax,fam in zip(axes.flat,order):
    for target,color in [(3,'#26788e'),(4,'#bf5b32')]:
        z=j[(j.curve_family==fam)&(j.target_index==target)].sort_values('point')
        ax.plot(z.point-z.target_index,z.J,'o-',color=color,label=f'Target {target}')
    ax.axhline(0,color='gray',lw=.8);ax.set_title(fam);ax.set_xlabel('Point index minus target index');ax.set_ylabel('Single-pair influence estimate')
axes[0,0].legend();fig.suptitle('Exploratory influence estimates: one +/− response pair per point',fontsize=13)
fig.savefig(OUT/'influence_estimates.png',dpi=170);plt.close(fig)
