"""Descriptive v9 analysis. Source CSVs are read-only; no observer exclusions.

Run with the bundled Python interpreter. Output participant-level summaries,
matched pairs/triples and an independent keypress reconstruction audit.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FILES = [
    'P001_identification_s1_20261006_143346_615693_trials.csv',
    'P002_identification_s1_20261007_164415_661422_trials.csv',
    'P003_identification_s1_20261008_153307_043870_trials.csv',
    'P004_identification_s1_20261008_170149_687959_trials.csv',
    'P005_identification_s1_20261016_113514_474972_trials.csv',
    'P006_identification_s1_20261016_152919_895489_trials.csv',
    'P007_identification_s1_20261017_105046_564768_trials.csv',
]
FAMILIES = ['parabola','circle','cubic','quartic','quintic']
POINTS = [0,1,2,3,5,6,7,8]
PID = [f'P{i:03d}' for i in range(1,8)]
N = len(PID)
assert not any('20261005' in name for name in FILES)
frames, audits, sources, quality = [], [], [], []

for pid, name in zip(PID,FILES):
    path = ROOT/'data'/name
    press_path = path.with_name(name.replace('_trials.csv','_presses.csv'))
    t, p = pd.read_csv(path), pd.read_csv(press_path)
    assert len(t)==len(p)==308
    assert t.trial.tolist()==p.trial.tolist()==list(range(1,309))
    assert t.trial_uid.is_unique and t.trial_uid.tolist()==p.trial_uid.tolist()
    assert set(t.participant_id)=={pid} and set(t.design_version)=={'2026-10-06_all_chords_v9'}
    assert set(p.design_version)==set(t.design_version)
    assert set(t.counterbalance_group)=={PID.index(pid)%4}
    assert (t.screen_size_px==1100).all() and (t.target_index==4).all()
    assert (t.display_scale_px_per_unit==5).all()
    assert set(t.input_version)=={'2026-10-04_screen_up_down_v2'}
    assert set(t.practice_protocol_version)=={'2026-10-04_unperturbed_feedback_v1'}
    assert t.practice_feedback_received.all()
    assert (t.submission_step_px==1).all() and (t.fine_moves>=1).all()
    assert np.isfinite(t[['response_normal_px','reaction_time_ms']]).all().all()
    assert (t.reaction_time_ms>0).all()
    assert t.groupby('stimulus_set').size().to_dict()=={'curvature_maxima':240,'original':68}
    for family in FAMILIES:
        g=t[(t.stimulus_set=='curvature_maxima')&(t.curve_family==family)]
        assert g.condition_type.value_counts().to_dict()=={'single':32,'baseline':16}
    assert (t[t.stimulus_set=='original'].baseline_context_scope=='context_1_only').all()
    for source in (path,press_path):
        sources.append(dict(participant_id=pid,file=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=308))
    press_cols=sorted([c for c in p if c.startswith('press_')],key=lambda x:int(x.split('_')[1]))
    for r, (_, row) in zip(t.itertuples(),p.iterrows()):
        steps=json.loads(r.step_sizes_px)
        assert steps==[30,10,1] and r.initial_step_px==30
        pos=np.array([r.initial_movable_x_px,r.initial_movable_y_px])
        manual_idx=game_reversals=cumulative=moves=fine=manual_count=0
        last=None
        for col in press_cols:
            if pd.isna(row[col]): continue
            action,count=row[col].rsplit('_',1)
            if action.startswith('step_'):
                manual_idx={'step_small':2,'step_medium':1,'step_big':0}[action]
                game_reversals=0; last=None; manual_count+=1
            else:
                assert action in ('up','down'),action
                if last is not None and action!=last:
                    game_reversals+=1; cumulative+=1
                step=steps[min(2,manual_idx+min(game_reversals,2))]
                target=np.array([getattr(r,f'ref_{action}_x_px'),getattr(r,f'ref_{action}_y_px')])
                delta=target-pos;distance=np.linalg.norm(delta);old=pos.copy()
                pos=target if distance<=step else pos+delta*step/distance
                fine+=int(step==1 and np.linalg.norm(pos-old)>1e-8)
                moves+=1;last=action
            assert int(count)==cumulative,(pid,r.trial,action,count,cumulative)
        replay_error=np.linalg.norm(pos-[r.final_x_px,r.final_y_px])
        assert replay_error<1e-7,(pid,r.trial,replay_error)
        assert moves==r.total_moves and fine==r.fine_moves
        assert r.r_count==0  # Recorder's r_count counts resets, not reversals.
        assert steps[min(2,manual_idx+min(game_reversals,2))]==r.submission_step_px
        up=np.array([r.ref_up_x_px-r.ref_down_x_px,r.ref_up_y_px-r.ref_down_y_px])
        up/=np.linalg.norm(up)
        screen_up=np.dot(pos-[r.correct_x_px,r.correct_y_px],up)
        assert abs(screen_up-r.response_screen_up_px)<1e-7
        assert abs(screen_up*r.control_up_normal_sign-r.response_normal_px)<1e-7
        assert abs(abs(r.response_normal_px)-r.response_abs_px)<1e-7
        # Validate stored geometry, independently of the current generator.
        baseline=np.array([[getattr(r,f'x{i}_baseline_math'),getattr(r,f'y{i}_baseline_math')] for i in range(9)])
        chords=np.linalg.norm(np.diff(baseline[POINTS],axis=0),axis=1)*r.display_scale_px_per_unit
        assert np.max(abs(chords-json.loads(r.reference_visible_chords_px)))<1e-6
        expected_k=0. if r.stimulus_set=='original' else .005
        assert abs(abs(r.target_analytic_curvature_px)-expected_k)<1e-9
        audits.append(dict(participant_id=pid,trial=r.trial,replay_error_px=replay_error,
                           fine_moves=fine,manual_step_changes=manual_count,reversals=cumulative))
    t['source_file']=name
    t['curvature_sign']=np.sign(t.target_analytic_curvature_px)
    # Positive is toward the concave side/chord: a locally shallower completion.
    t['curvature_aligned_response_px']=np.where(t.stimulus_set=='curvature_maxima',t.response_normal_px*t.curvature_sign,np.nan)
    t['trial_quarter']=((t.trial-1)//77)+1
    quality.append(dict(participant_id=pid,date=name.split('_')[3],trials=len(t),counterbalance_group=int(t.counterbalance_group.iloc[0]),
                        active_trial_minutes=t.reaction_time_ms.sum()/60000,median_trial_seconds=t.reaction_time_ms.median()/1000,
                        median_fine_moves=t.fine_moves.median(),blocked_trials=int((t.blocked_submissions>0).sum()),
                        blocked_attempts=int(t.blocked_submissions.sum()),max_abs_response_px=t.response_abs_px.max(),
                        responses_over_50px=int((t.response_abs_px>50).sum())))
    frames.append(t)

t=pd.concat(frames,ignore_index=True)
pd.DataFrame(sources).to_csv(OUT/'sources.csv',index=False)
pd.DataFrame(audits).to_csv(OUT/'recording_audit.csv',index=False)
q=pd.DataFrame(quality);q.to_csv(OUT/'participant_quality.csv',index=False)
m=t[t.stimulus_set=='curvature_maxima'].copy()
b=m[m.condition_type=='baseline'].copy()
assert len(t)==308*N and len(m)==240*N and len(b)==80*N

pairs=[]
for key,g in t.groupby(['participant_id','stimulus_set','curve_family','matched_pose_id','repetition']):
    singles=g[g.condition_type=='single']; zeros=g[g.condition_type=='baseline']
    assert len(singles)==2
    for field in ('rotation_deg','reversed','initial_side','initial_offset_px','target_shift_x_units',
                  'target_shift_y_units','pose_combination','display_scale_px_per_unit'):
        assert g[field].nunique()==1,(key,field)
    assert len(zeros)==(1 if key[1]=='curvature_maxima' or key[3]==1 else 0)
    plus=singles[singles.perturb_sign==1].iloc[0];minus=singles[singles.perturb_sign==-1].iloc[0]
    assert plus.perturb_index==minus.perturb_index
    delta=abs(json.loads(plus.perturb_actual_px)[0]);dm=abs(json.loads(minus.perturb_actual_px)[0])
    assert abs(delta-dm)<1e-8
    zero=zeros.iloc[0] if len(zeros) else None
    rp,rm=plus.response_normal_px,minus.response_normal_px
    r0=zero.response_normal_px if zero is not None else np.nan
    pairs.append(dict(participant_id=key[0],stimulus_set=key[1],curve_family=key[2],matched_pose_id=key[3],repetition=key[4],
                      point=int(plus.perturb_index),initial_side=plus.initial_side,curvature_sign=plus.curvature_sign,
                      baseline_trial=int(zero.trial) if zero is not None else np.nan,minus_trial=int(minus.trial),plus_trial=int(plus.trial),
                      baseline_px=r0,minus_px=rm,plus_px=rp,delta_px=delta,
                      minus_shift_px=rm-r0,plus_shift_px=rp-r0,sensitivity=(rp-rm)/(2*delta),
                      asymmetry_px=(rp+rm)/2-r0,
                      maximum_abs_response_px=max(abs(rp),abs(rm),abs(r0) if zero is not None else 0)))
j=pd.DataFrame(pairs);j['distance_rank']=abs(j.point-4)
assert len(j)==112*N and (j.stimulus_set=='curvature_maxima').sum()==80*N
assert j.baseline_trial.notna().sum()==84*N
j.to_csv(OUT/'paired_influences.csv',index=False)
jm=j[j.stimulus_set=='curvature_maxima']
profile=j.groupby(['participant_id','stimulus_set','curve_family','point'],as_index=False).sensitivity.mean()
profile.to_csv(OUT/'participant_influence_profiles.csv',index=False)
baseline=b.groupby(['participant_id','curve_family'],as_index=False).agg(
    n=('trial','size'),curvature_aligned_bias_px=('curvature_aligned_response_px','mean'),
    mean_abs_px=('response_abs_px','mean'),median_abs_px=('response_abs_px','median'),
    sd_aligned_px=('curvature_aligned_response_px','std'))
baseline.to_csv(OUT/'baseline_summary.csv',index=False)

starts=[]
for key,g in m.groupby(['participant_id','curve_family']):
    base=g[g.condition_type=='baseline'].pivot(index='matched_pose_id',columns='initial_side',values='response_normal_px')
    all_conditions=g.assign(treatment=g.perturb_sign.fillna(0)).pivot(index=['matched_pose_id','treatment'],columns='initial_side',values='response_normal_px')
    dif=base[1]-base[-1]
    starts.append(dict(participant_id=key[0],curve_family=key[1],baseline_positive_minus_negative_start_px=dif.mean(),
                       baseline_mean_abs_start_difference_px=dif.abs().mean(),all_positive_minus_negative_start_px=(all_conditions[1]-all_conditions[-1]).mean()))
start=pd.DataFrame(starts);start.to_csv(OUT/'starting_side_effects.csv',index=False)

contrasts=[]
for pid in PID:
    bias=baseline[baseline.participant_id==pid].set_index('curve_family').curvature_aligned_bias_px
    profiles=profile[(profile.participant_id==pid)&(profile.stimulus_set=='curvature_maxima')].pivot(index='point',columns='curve_family',values='sensitivity')
    for other in FAMILIES[1:]:
        difference=profiles[other]-profiles.parabola
        contrasts.append(dict(participant_id=pid,comparison=other+' minus parabola',
                              bias_difference_px=bias[other]-bias.parabola,
                              mean_sensitivity_difference=difference.mean(),
                              nearest_sensitivity_difference=difference.loc[[3,5]].mean(),
                              profile_rms_difference=np.sqrt(np.mean(difference**2))))
contrasts=pd.DataFrame(contrasts);contrasts.to_csv(OUT/'primary_contrasts.csv',index=False)

nearfar=j.assign(region=np.where(j.distance_rank==1,'nearest',np.where(j.distance_rank==2,'next','outer'))).groupby(
    ['participant_id','stimulus_set','curve_family','region'],as_index=False).agg(mean_sensitivity=('sensitivity','mean'),mean_abs_sensitivity=('sensitivity',lambda x:x.abs().mean()))
nearfar.to_csv(OUT/'near_far_summary.csv',index=False)
condition_time=t.groupby(['participant_id','trial_quarter'],as_index=False).agg(median_seconds=('reaction_time_ms',lambda x:x.median()/1000),
                  median_abs_response_px=('response_abs_px','median'))
condition_time.to_csv(OUT/'time_course.csv',index=False)
extreme=t.sort_values('response_abs_px',ascending=False).head(20)
extreme[['participant_id','trial','trial_uid','stimulus_set','curve_family','condition_type','perturb_index','perturb_sign',
         'response_normal_px','response_abs_px','reaction_time_ms','initial_side']].to_csv(OUT/'largest_deviations.csv',index=False)
# Sensitivity checks are descriptive, not data cleaning. Retain all primary data.
robust=[]
for family,g in jm.groupby('curve_family'):
    by_person=g.groupby('participant_id').sensitivity.mean()
    idx=g.sensitivity.abs().idxmax()
    robust.append(dict(curve_family=family,mean_sensitivity=g.sensitivity.mean(),
                       median_participant_mean=by_person.median(),
                       leave_one_participant_out_min=min(by_person.drop(pid).mean() for pid in PID),
                       leave_one_participant_out_max=max(by_person.drop(pid).mean() for pid in PID),
                       largest_abs_pair_sensitivity=g.loc[idx,'sensitivity'],
                       mean_without_largest_pair=g.drop(idx).sensitivity.mean(),
                       flagged_pair_participant=g.loc[idx,'participant_id'],flagged_pair_plus_trial=g.loc[idx,'plus_trial'],
                       flagged_pair_minus_trial=g.loc[idx,'minus_trial']))
pd.DataFrame(robust).to_csv(OUT/'sensitivity_checks.csv',index=False)

# Compare originals to maxima using the SAME first-start protocol, not both
# maximum repetitions versus the one available original repetition.
original_pairs=j[j.stimulus_set=='original']
secondary=jm[jm.repetition==1].merge(original_pairs,on=['participant_id','curve_family','point'],suffixes=('_maximum','_original'))
assert len(secondary)==24*N
assert (secondary.initial_side_maximum==secondary.initial_side_original).all()
assert np.allclose(secondary.delta_px_maximum,secondary.delta_px_original)
secondary['sensitivity_difference']=secondary.sensitivity_maximum-secondary.sensitivity_original
secondary[['participant_id','curve_family','point','sensitivity_maximum','sensitivity_original','sensitivity_difference']].to_csv(OUT/'original_maximum_same_start_contrasts.csv',index=False)
left_right=jm[jm.point.isin([3,5])].groupby(['participant_id','curve_family','point']).sensitivity.mean().unstack()
left_right['point3_minus_point5']=left_right[3]-left_right[5]
left_right.reset_index().to_csv(OUT/'nearest_left_right.csv',index=False)
nearest=jm[jm.distance_rank==1].groupby(['participant_id','curve_family']).sensitivity.mean().unstack()
nearest_checks=[]
for family in FAMILIES[1:]:
    d=nearest[family]-nearest.parabola
    nearest_checks.append(dict(comparison=family+' minus parabola',mean_difference=d.mean(),
                              participants_positive=int((d>1e-10).sum()),participants_negative=int((d < -1e-10).sum()),
                              participants_zero=int((d.abs()<=1e-10).sum()),
                              leave_one_participant_out_min=min(d.drop(pid).mean() for pid in PID),
                              leave_one_participant_out_max=max(d.drop(pid).mean() for pid in PID)))
pd.DataFrame(nearest_checks).to_csv(OUT/'nearest_contrast_sensitivity_checks.csv',index=False)

summary=baseline.groupby('curve_family')[['curvature_aligned_bias_px','mean_abs_px']].mean().reindex(FAMILIES)
summary['baseline_start_effect_px']=start.groupby('curve_family').baseline_positive_minus_negative_start_px.mean()
nf=nearfar[nearfar.stimulus_set=='curvature_maxima'].groupby(['curve_family','region']).mean_sensitivity.mean().unstack()
summary=summary.join(nf).reset_index();summary.to_csv(OUT/'family_summary.csv',index=False)
group_profile=profile[profile.stimulus_set=='curvature_maxima'].groupby(['curve_family','point']).sensitivity.mean().unstack().reindex(FAMILIES)
group_profile.to_csv(OUT/'group_influence_profiles.csv')
perturb_response=jm.groupby(['curve_family','point'],as_index=False).agg(delta_px=('delta_px','mean'),baseline_px=('baseline_px','mean'),
                        negative_shift_px=('minus_shift_px','mean'),positive_shift_px=('plus_shift_px','mean'),
                        sensitivity=('sensitivity','mean'),asymmetry_px=('asymmetry_px','mean'))
perturb_response.to_csv(OUT/'responses_by_perturbation.csv',index=False)
o=t[t.stimulus_set=='original']
o[o.condition_type=='baseline'][['participant_id','curve_family','response_normal_px','response_abs_px','matched_pose_id']].to_csv(OUT/'original_baselines.csv',index=False)
metrics=dict(total_trials=len(t),participants=len(PID),matched_trials=len(m),matched_baselines=len(b),original_trials=len(o),
             maximum_replay_error_px=max(a['replay_error_px'] for a in audits),excluded_files=sorted(f.name for f in (ROOT/'data').glob('P00[12]*20261005*.csv')),
             exclusion_rule='Exclude October 5 P001/P002; explicitly include only seven v9 sessions listed in FILES.',
             minimum_perturbation_px=float(j.delta_px.min()),maximum_perturbation_px=float(j.delta_px.max()),
             baseline_start_effect_px=float(start.baseline_positive_minus_negative_start_px.mean()))
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('QUALITY\n'+q.round(3).to_string(index=False))
print('\nFAMILY SUMMARY\n'+summary.round(3).to_string(index=False))
print('\nBASELINE PER PARTICIPANT\n'+baseline.pivot(index='participant_id',columns='curve_family',values='curvature_aligned_bias_px').round(3).to_string())
print('\nPRIMARY CONTRASTS\n'+contrasts.round(3).to_string(index=False))
print('\nINFLUENCE PROFILES\n'+group_profile.round(3).to_string())
print('\nSTART EFFECTS\n'+start.round(3).to_string(index=False))
print('\nEXTREMES\n'+extreme[['participant_id','trial','curve_family','stimulus_set','condition_type','response_normal_px']].head(8).round(3).to_string(index=False))
print('\nMETRICS\n'+json.dumps(metrics,indent=2))

# Additional seven-observer summaries. Preserve repeated-measures structure:
# bootstrap whole participants, using the same draw across family contrasts.
rng=np.random.default_rng(20261020)
draws=rng.integers(0,N,size=(50000,N))
def interval(values):
    values=np.asarray(values,float)
    assert len(values)==N
    return np.quantile(values[draws].mean(axis=1),[.025,.975])

contrast_intervals=[]
for family in FAMILIES[1:]:
    for outcome in ['nearest_sensitivity_difference','bias_difference_px']:
        v=contrasts[contrasts.comparison==family+' minus parabola'].set_index('participant_id')[outcome].reindex(PID)
        lo,hi=interval(v)
        contrast_intervals.append(dict(comparison=family+' minus parabola',outcome=outcome,mean=v.mean(),median=v.median(),
            lower_95=lo,upper_95=hi,positive=int((v>1e-10).sum()),negative=int((v < -1e-10).sum()),zero=int((abs(v)<=1e-10).sum()),
            first_four_mean=v.iloc[:4].mean(),new_three_mean=v.iloc[4:].mean()))
ci=pd.DataFrame(contrast_intervals);ci.to_csv(OUT/'primary_contrast_intervals.csv',index=False)

family_intervals=[]
for family in FAMILIES:
    for outcome,values in [
        ('mean_absolute_error_px',baseline[baseline.curve_family==family].set_index('participant_id').mean_abs_px.reindex(PID)),
        ('curvature_aligned_bias_px',baseline[baseline.curve_family==family].set_index('participant_id').curvature_aligned_bias_px.reindex(PID)),
        ('nearest_influence',nearest[family].reindex(PID)),
    ]:
        lo,hi=interval(values)
        family_intervals.append(dict(curve_family=family,outcome=outcome,mean=values.mean(),lower_95=lo,upper_95=hi))
pd.DataFrame(family_intervals).to_csv(OUT/'family_intervals.csv',index=False)

batch=baseline.merge(nearest.reset_index().melt(id_vars='participant_id',var_name='curve_family',value_name='nearest'),
                     on=['participant_id','curve_family'])
batch['collection_batch']=np.where(batch.participant_id.isin(PID[:4]),'P001-P004','P005-P007')
batch.groupby(['collection_batch','curve_family'],as_index=False)[['curvature_aligned_bias_px','mean_abs_px','nearest']].mean().to_csv(OUT/'collection_batch_summary.csv',index=False)
group_data=batch.merge(q[['participant_id','counterbalance_group']],on='participant_id')
group_data.groupby(['counterbalance_group','curve_family'])[['curvature_aligned_bias_px','mean_abs_px','nearest']].mean().groupby('curve_family').mean().reset_index().to_csv(OUT/'equal_group_sensitivity.csv',index=False)

# All primary analyses retain large baseline settings. This is a labeled,
# post-hoc sensitivity check at a fixed 50 px descriptive threshold.
flagged=b[b.response_abs_px>50]
flagged[['participant_id','trial','curve_family','response_normal_px','response_abs_px']].to_csv(OUT/'baselines_over_50px.csv',index=False)
trimmed=b[b.response_abs_px<=50].groupby(['participant_id','curve_family'],as_index=False).agg(mean_abs_px=('response_abs_px','mean'),bias_px=('curvature_aligned_response_px','mean'))
trimmed.groupby('curve_family',as_index=False)[['mean_abs_px','bias_px']].mean().to_csv(OUT/'large_baseline_sensitivity.csv',index=False)

region_signs=[]
for region,g in jm.assign(region=np.where(jm.distance_rank==1,'nearest',np.where(jm.distance_rank==2,'next','outer'))).groupby('region'):
    region_signs.append(dict(region=region,n_pairs=len(g),positive=int((g.sensitivity>1e-10).sum()),
        negative=int((g.sensitivity < -1e-10).sum()),zero=int((g.sensitivity.abs()<=1e-10).sum()),mean=g.sensitivity.mean(),
        minus_shift_px=g.minus_shift_px.mean(),plus_shift_px=g.plus_shift_px.mean()))
pd.DataFrame(region_signs).to_csv(OUT/'region_summary.csv',index=False)

lr=left_right.groupby('participant_id').mean().reindex(PID)
lr.to_csv(OUT/'participant_left_right_summary.csv')
qq=(nearest.quintic-nearest.quartic).reindex(PID)
lo,hi=interval(qq)
pd.DataFrame([dict(comparison='quintic minus quartic',mean=qq.mean(),lower_95=lo,upper_95=hi,
                  positive=int((qq>1e-10).sum()),negative=int((qq < -1e-10).sum()),
                  first_four_mean=qq.iloc[:4].mean(),new_three_mean=qq.iloc[4:].mean())]).to_csv(OUT/'quartic_quintic_secondary.csv',index=False)

secondary_summary=secondary[secondary.point.isin([3,5])].groupby(['participant_id','curve_family']).sensitivity_difference.mean().unstack().reindex(PID)
rows=[]
for family in secondary_summary:
    v=secondary_summary[family];lo,hi=interval(v)
    rows.append(dict(curve_family=family,maximum_minus_original_nearest=v.mean(),lower_95=lo,upper_95=hi,
                     positive=int((v>1e-10).sum()),negative=int((v < -1e-10).sum())))
pd.DataFrame(rows).to_csv(OUT/'original_maximum_summary.csv',index=False)

# Earlier four-observer values must reproduce the archived analysis.
prev=pd.read_csv(ROOT/'analysis/P001_P004_20261009/baseline_summary.csv')
old=baseline[baseline.participant_id.isin(PID[:4])]
assert np.allclose(prev.sort_values(['participant_id','curve_family']).mean_abs_px,
                   old.sort_values(['participant_id','curve_family']).mean_abs_px)
t[['participant_id','source_file','trial','trial_uid','stimulus_set','curve_family','condition_type','repetition',
   'matched_pose_id','perturb_index','perturb_sign','initial_side','response_normal_px','response_abs_px',
   'curvature_aligned_response_px','reaction_time_ms']].to_csv(OUT/'derived_responses.csv',index=False)
print('\nPRIMARY EXPLORATORY INTERVALS\n'+ci.round(4).to_string(index=False))
