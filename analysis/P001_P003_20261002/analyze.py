"""Reproducible descriptive pilot analysis; reads the active, merged CSVs only."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/stars_analysis_mpl')
from pathlib import Path
import json
import itertools
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FAMILIES = ['parabola', 'cubic', 'quartic', 'quintic']
POINTS = [0, 1, 2, 3, 5, 6, 7, 8]
COLORS = {'P001':'#2274a5', 'P002':'#db7727', 'P003':'#238566'}
frames, audits, sources = [], [], []

for participant in COLORS:
    files = list((ROOT/'data').glob(f'{participant}_*_trials.csv'))
    assert len(files) == 1, files
    path = files[0]
    t = pd.read_csv(path).copy()
    p = pd.read_csv(str(path).replace('_trials.csv', '_presses.csv'))
    assert len(t) == len(p) == 277
    assert t.trial.tolist() == p.trial.tolist() == list(range(1, 278))
    assert t.trial_uid.is_unique and t.trial_uid.tolist() == p.trial_uid.tolist()
    assert set(t.participant_id) == {participant} and set(t.target_index) == {4}
    assert np.isfinite(t[['response_normal_px','reaction_time_ms']]).all().all()
    assert (t.submission_step_px == 1).all() and (t.fine_moves >= 1).all()
    sources.append(dict(participant=participant,trials_file=path.name,
                        presses_file=path.name.replace('_trials.csv','_presses.csv')))
    press_cols = sorted([c for c in p if c.startswith('press_')], key=lambda x:int(x.split('_')[1]))
    for r, (_, row) in zip(t.itertuples(), p.iterrows()):
        # P003's 30/10/1 scheme is checked against every recorded endpoint.
        steps = [10,5,1] if r.initial_step_px == 10 else [30,10,1]
        assert r.initial_step_px in (10,30)
        pos = np.array([r.initial_movable_x_px,r.initial_movable_y_px])
        base = reversals = cumulative = moves = fine = manual = 0
        last = None
        for c in press_cols:
            if pd.isna(row[c]):
                continue
            action, count = row[c].rsplit('_',1)
            if action.startswith('step_'):
                base = {'step_small':2,'step_medium':1,'step_big':0}[action]
                reversals = 0
                last = None
                manual += 1
            else:
                assert action in ('up','down'), action
                if last is not None and last != action:
                    reversals += 1
                    cumulative += 1
                step = steps[min(2,base+min(reversals,2))]
                target = np.array([getattr(r,f'ref_{action}_x_px'),getattr(r,f'ref_{action}_y_px')])
                delta = target-pos
                distance = np.linalg.norm(delta)
                old = pos.copy()
                pos = target if distance <= step else pos + delta*step/distance
                fine += int(step == 1 and np.linalg.norm(pos-old)>1e-8)
                moves += 1
                last = action
            assert int(count) == cumulative
        replay_error = float(np.linalg.norm(pos-[r.final_x_px,r.final_y_px]))
        assert replay_error < 1e-7, (participant,r.trial,replay_error)
        assert moves == r.total_moves and fine == r.fine_moves
        assert steps[min(2,base+min(reversals,2))] == r.submission_step_px
        normal = np.array([r.ref_up_x_px-r.ref_down_x_px,r.ref_up_y_px-r.ref_down_y_px])
        normal /= np.linalg.norm(normal)
        projected = np.dot(pos-[r.correct_x_px,r.correct_y_px],normal)
        assert abs(projected-r.response_normal_px)<1e-7
        audits.append(dict(participant_id=participant,trial=r.trial,trial_uid=r.trial_uid,
                           replay_error_px=replay_error,manual_step_changes=manual,
                           fine_moves=fine,reversals=cumulative,step_scheme='/'.join(map(str,steps))))
    t['curvature_sign'] = np.sign(t.target_analytic_curvature_baseline)
    t['curvature_aligned_response_px'] = t.response_normal_px*t.curvature_sign
    frames.append(t)

t = pd.concat(frames,ignore_index=True)
audit = pd.DataFrame(audits)
audit.to_csv(OUT/'recording_audit.csv',index=False)
m = t[t.stimulus_set=='curvature_maxima'].copy()
b = m[m.condition_type=='baseline'].copy()
assert len(m)==576 and len(b)==192
assert np.allclose(abs(m.target_analytic_curvature_px),.005)
pairs=[]
for key,g in m.groupby(['participant_id','curve_family','matched_pose_id','repetition']):
    assert len(g)==3 and sorted(g.condition_type)==['baseline','single','single']
    for field in ['rotation_deg','reversed','initial_offset_px','display_scale_px_per_unit',
                  'target_shift_x_units','target_shift_y_units','pose_combination']:
        assert g[field].nunique()==1,(key,field)
    zero=g[g.condition_type=='baseline'].iloc[0]
    plus=g[g.perturb_sign==1].iloc[0]
    minus=g[g.perturb_sign==-1].iloc[0]
    assert plus.perturb_index==minus.perturb_index
    dp=abs(json.loads(plus.perturb_actual_px)[0]);dm=abs(json.loads(minus.perturb_actual_px)[0])
    assert abs(dp-dm)<1e-8
    pairs.append(dict(participant_id=key[0],curve_family=key[1],matched_pose_id=key[2],repetition=key[3],
                      point=int(plus.perturb_index),initial_side=plus.initial_side,
                      curvature_sign=plus.curvature_sign,pose_combination=plus.pose_combination,
                      baseline_trial=int(zero.trial),minus_trial=int(minus.trial),plus_trial=int(plus.trial),
                      baseline_px=zero.response_normal_px,minus_px=minus.response_normal_px,plus_px=plus.response_normal_px,
                      delta_px=dp,minus_shift_px=minus.response_normal_px-zero.response_normal_px,
                      plus_shift_px=plus.response_normal_px-zero.response_normal_px,
                      sensitivity=(plus.response_normal_px-minus.response_normal_px)/(dp+dm),
                      asymmetry_px=(plus.response_normal_px+minus.response_normal_px)/2-zero.response_normal_px))
j=pd.DataFrame(pairs)
assert len(j)==192
j['distance']=abs(j.point-4)
j.to_csv(OUT/'matched_triplets.csv',index=False)
profile=j.groupby(['participant_id','curve_family','point'],as_index=False).sensitivity.mean()
profile.to_csv(OUT/'participant_influence_profiles.csv',index=False)
baseline=b.groupby(['participant_id','curve_family'],as_index=False).agg(
    n=('trial','size'),signed_bias_px=('response_normal_px','mean'),
    curvature_aligned_bias_px=('curvature_aligned_response_px','mean'),
    mean_abs_px=('response_abs_px','mean'),median_abs_px=('response_abs_px','median'),
    sd_signed_px=('response_normal_px','std'))
baseline.to_csv(OUT/'baseline_summary.csv',index=False)
start=[]
for (pid,family),g in b.groupby(['participant_id','curve_family']):
    pvt=g.pivot(index='matched_pose_id',columns='initial_side',values='response_normal_px')
    differences=pvt[1]-pvt[-1]
    start.append(dict(participant_id=pid,curve_family=family,
                      positive_minus_negative_start_px=differences.mean(),contexts=len(differences)))
start=pd.DataFrame(start);start.to_csv(OUT/'starting_side_effects.csv',index=False)
contrasts=[]
for pid in COLORS:
    subset=b[b.participant_id==pid]
    values=subset.pivot(index=['matched_pose_id','repetition'],columns='curve_family',values='curvature_aligned_response_px')
    for a,c in itertools.combinations(FAMILIES,2):
        difference=values[c]-values[a]
        profiles=profile[profile.participant_id==pid].pivot(index='point',columns='curve_family',values='sensitivity')
        contrasts.append(dict(participant_id=pid,comparison=f'{c} minus {a}',
                              curvature_aligned_bias_difference_px=difference.mean(),
                              mean_absolute_setting_difference_px=difference.abs().mean(),
                              sensitivity_profile_rms_difference=float(np.sqrt(np.mean((profiles[c]-profiles[a])**2)))))
contrasts=pd.DataFrame(contrasts);contrasts.to_csv(OUT/'family_contrasts.csv',index=False)
original=[]
o=t[t.stimulus_set=='original']
for (pid,family),g in o.groupby(['participant_id','curve_family']):
    z=g[g.condition_type=='baseline'].iloc[0]
    for point in POINTS:
        plus=g[(g.perturb_sign==1)&(g.perturb_index==point)].iloc[0]
        minus=g[(g.perturb_sign==-1)&(g.perturb_index==point)].iloc[0]
        delta=abs(json.loads(plus.perturb_actual_px)[0])
        original.append(dict(participant_id=pid,curve_family=family,point=point,
                             baseline_px=z.response_normal_px,delta_px=delta,
                             sensitivity=(plus.response_normal_px-minus.response_normal_px)/(2*delta)))
original=pd.DataFrame(original);original.to_csv(OUT/'original_influence_profiles.csv',index=False)
quality=t.groupby('participant_id',as_index=False).agg(
    trials=('trial','size'),group=('counterbalance_group','first'),initial_step_px=('initial_step_px','first'),
    median_rt_ms=('reaction_time_ms','median'),active_ms=('reaction_time_ms','sum'),
    total_moves=('total_moves','sum'),median_moves=('total_moves','median'),
    fine_moves=('fine_moves','sum'),blocked_attempts=('blocked_submissions','sum'),
    median_abs_all_px=('response_abs_px','median'),max_abs_px=('response_abs_px','max'))
quality['active_minutes']=quality.active_ms/60000
quality.to_csv(OUT/'participant_quality.csv',index=False)
outliers=t.nlargest(12,'response_abs_px')[['participant_id','trial','trial_uid','stimulus_set','curve_family',
    'condition_type','response_normal_px','response_abs_px','reaction_time_ms','initial_offset_px','fine_moves']]
outliers.to_csv(OUT/'largest_deviations.csv',index=False)
# Diagnostics only: no exclusions are applied to the primary summaries.
nearfar=j.assign(region=np.where(j.distance==1,'nearest','other')).groupby(
    ['participant_id','region'],as_index=False).sensitivity.mean()
nearfar.to_csv(OUT/'near_far_summary.csv',index=False)
absolute_profile = profile.assign(region=np.where(abs(profile.point-4)==1,'nearest','other'),
                                  absolute_sensitivity=profile.sensitivity.abs())
absolute_profile.groupby(['participant_id','region'],as_index=False).absolute_sensitivity.mean().to_csv(
    OUT/'absolute_influence_summary.csv',index=False)
# Explicit, post-hoc influence diagnostic, never an exclusion from main results.
flag=(j.participant_id=='P002') & ((j.minus_trial==10)|(j.plus_trial==10)|(j.baseline_trial==10))
diagnostics=[]
for label,frame in [('all retained trials',j),('omit P002 trial-10 triplet for diagnostic only',j[~flag])]:
    v=frame.assign(region=np.where(frame.distance==1,'nearest','other')).groupby(
        ['participant_id','region'],as_index=False).sensitivity.mean()
    v['scenario']=label
    diagnostics.append(v)
pd.concat(diagnostics,ignore_index=True).to_csv(OUT/'outlier_sensitivity_check.csv',index=False)
profile[profile.participant_id!='P003'].groupby(['curve_family','point'],as_index=False).sensitivity.mean().to_csv(
    OUT/'P001_P002_only_profiles.csv',index=False)
quarters=t.copy().assign(quarter=np.minimum(4,((t.trial-1)*4//277)+1)).groupby(
    ['participant_id','quarter'],as_index=False).agg(median_rt_ms=('reaction_time_ms','median'),median_abs_px=('response_abs_px','median'))
quarters.to_csv(OUT/'time_course.csv',index=False)

plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True,sharey=True,layout='constrained')
for ax,family in zip(axs.flat,FAMILIES):
    g=profile[profile.curve_family==family]
    for pid,color in COLORS.items():
        q=g[g.participant_id==pid].sort_values('point')
        ax.plot(q.point,q.sensitivity,'o-',color=color,alpha=.8,label=pid)
    avg=g.groupby('point').sensitivity.mean()
    ax.plot(avg.index,avg.values,'k--',lw=2,label='Mean of 3 participants')
    ax.axhline(0,color='#999999',lw=.8)
    ax.axvspan(3.6,4.4,color='#dddddd',alpha=.6)
    ax.set_title(family.capitalize());ax.set_xticks(range(9));ax.set_xlabel('Dot index (4 is the hidden target)')
    ax.set_ylabel('Response shift / perturbation shift')
axs[0,0].legend(fontsize=8)
fig.suptitle('Matched-curvature perturbation sensitivity\nEach participant line averages the two starting sides; no trials excluded',fontsize=14)
fig.savefig(OUT/'influence_profiles.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(14,4.6),layout='constrained')
for pid,color in COLORS.items():
    g=baseline[baseline.participant_id==pid].set_index('curve_family').loc[FAMILIES]
    axs[0].plot(range(4),g.mean_abs_px,'o-',color=color,label=pid)
    axs[1].plot(range(4),g.curvature_aligned_bias_px,'o-',color=color,label=pid)
    h=start[start.participant_id==pid].set_index('curve_family').loc[FAMILIES]
    axs[2].plot(range(4),h.positive_minus_negative_start_px,'o-',color=color,label=pid)
for ax,title,ylabel in zip(axs,['Unperturbed placement deviation','Bias relative to bending direction','Starting-side dependence'],
                         ['Mean absolute deviation (px)','Mean signed deviation (px)','Positive-start minus negative-start setting (px)']):
    ax.set_title(title);ax.set_xticks(range(4),['x²','x³','x⁴','x⁵']);ax.set_ylabel(ylabel);ax.axhline(0,color='#aaaaaa',lw=.7)
axs[0].legend();fig.suptitle('Matched baselines: 16 observations per family per participant',fontsize=14)
fig.savefig(OUT/'baseline_and_starting_side.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for pid,color in COLORS.items():
    g=nearfar[nearfar.participant_id==pid].set_index('region').loc[['nearest','other']]
    axs[0].plot([0,1],g.sensitivity,'o-',color=color,label=pid)
    g=quarters[quarters.participant_id==pid]
    axs[1].plot(g.quarter,g.median_rt_ms/1000,'o-',color=color,label=pid)
axs[0].set_xticks([0,1],['Nearest dots (3, 5)','Other six dots']);axs[0].set_ylabel('Mean signed sensitivity');axs[0].axhline(0,color='gray',lw=.7)
axs[0].set_title('Where perturbations influence the response');axs[0].legend()
axs[1].set_xticks([1,2,3,4]);axs[1].set_xlabel('Quarter of session');axs[1].set_ylabel('Median response time (seconds)');axs[1].set_title('Response times across the session')
fig.savefig(OUT/'influence_and_time.png',dpi=170);plt.close(fig)

summary={'sources':sources,'quality':quality.to_dict('records'),
         'replay_max_error_px':float(audit.replay_error_px.max()),
         'baseline':baseline.to_dict('records'),'starting_side':start.to_dict('records'),
         'family_contrasts':contrasts.to_dict('records'),'near_far':nearfar.to_dict('records'),
         'maxima_perturb_range_px':[float(j.delta_px.min()),float(j.delta_px.max())],
         'original_perturb_range_px':[float(original.delta_px.min()),float(original.delta_px.max())],
         'largest_deviations':outliers.to_dict('records')}
(OUT/'metrics.json').write_text(json.dumps(summary,indent=2)+'\n')
print('QUALITY\n'+quality.round(3).to_string(index=False))
print('BASELINE\n'+baseline.round(3).to_string(index=False))
print('START\n'+start.round(3).to_string(index=False))
print('NEAR/FAR\n'+nearfar.round(3).to_string(index=False))
print('CONTRASTS\n'+contrasts.round(3).to_string(index=False))
print('LARGEST DEVIATIONS\n'+outliers.head(6).round(3).to_string(index=False))
