"""Six-observer descriptive synthesis, preserving the v7/v9 protocol boundary.

User confirmed October 5 P001/P002 are different people from later P001/P002.
Raw CSVs are read-only. No observer/trial trimming or missing-value imputation.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
FILES=[
 ('Earlier_P001','earlier','P001_identification_s1_20261005_130147_514238_trials.csv'),
 ('Earlier_P002','earlier','P002_identification_s1_20261005_160417_388272_trials.csv'),
 ('Controlled_P001','controlled','P001_identification_s1_20261006_143346_615693_trials.csv'),
 ('Controlled_P002','controlled','P002_identification_s1_20261007_164415_661422_trials.csv'),
 ('Controlled_P003','controlled','P003_identification_s1_20261008_153307_043870_trials.csv'),
 ('Controlled_P004','controlled','P004_identification_s1_20261008_170149_687959_trials.csv'),
]
FAMILIES=['parabola','circle','cubic','quartic','quintic']
POINTS=[0,1,2,3,5,6,7,8]
sources=[];frames=[];audits=[];quality=[];geometry=[];coordinates=[]

def save(frame,name):
    frame.to_csv(OUT/(name+'.csv'),index=False)

def baseline_xy(r):
    return np.array([[getattr(r,f'x{i}_baseline_math'),getattr(r,f'y{i}_baseline_math')] for i in range(9)])*r.display_scale_px_per_unit

for observer,cohort,name in FILES:
    path=ROOT/'data'/name;press_path=path.with_name(name.replace('_trials.csv','_presses.csv'))
    t=pd.read_csv(path);p=pd.read_csv(press_path)
    assert len(t)==len(p)==308
    assert t.trial.tolist()==p.trial.tolist()==list(range(1,309))
    assert t.trial_uid.is_unique and t.trial_uid.tolist()==p.trial_uid.tolist()
    assert set(t.design_version)==set(p.design_version)
    assert t.groupby('stimulus_set').size().to_dict()=={'curvature_maxima':240,'original':68}
    assert set(t.input_version)=={'2026-10-04_screen_up_down_v2'}
    assert np.isfinite(t[['response_normal_px','reaction_time_ms']]).all().all()
    assert (t.reaction_time_ms>0).all()
    assert (t.submission_step_px==1).all() and (t.fine_moves>=1).all()
    assert (t.target_index==4).all() and (t.display_scale_px_per_unit==5).all()
    for family in FAMILIES:
        m=t[(t.stimulus_set=='curvature_maxima')&(t.curve_family==family)]
        assert m.condition_type.value_counts().to_dict()=={'single':32,'baseline':16}
        assert np.allclose(abs(m.target_analytic_curvature_px),.005)
    for source in (path,press_path):
        sources.append(dict(observer=observer,cohort=cohort,file=source.name,rows=308,sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    press_cols=sorted([c for c in p if c.startswith('press_')],key=lambda x:int(x.split('_')[1]))
    for r,(_,row) in zip(t.itertuples(),p.iterrows()):
        steps=json.loads(r.step_sizes_px);assert steps==[30,10,1] and r.initial_step_px==30
        pos=np.array([r.initial_movable_x_px,r.initial_movable_y_px])
        manual_idx=game_reversals=cumulative=moves=fine=0;last=None
        for col in press_cols:
            if pd.isna(row[col]):continue
            action,count=row[col].rsplit('_',1)
            if action.startswith('step_'):
                manual_idx={'step_small':2,'step_medium':1,'step_big':0}[action];game_reversals=0;last=None
            else:
                assert action in ('up','down'),action
                if last is not None and action!=last:game_reversals+=1;cumulative+=1
                step=steps[min(2,manual_idx+min(game_reversals,2))]
                target=np.array([getattr(r,f'ref_{action}_x_px'),getattr(r,f'ref_{action}_y_px')])
                delta=target-pos;distance=np.linalg.norm(delta);old=pos.copy()
                pos=target if distance<=step else pos+delta*step/distance
                fine+=int(step==1 and np.linalg.norm(pos-old)>1e-8);moves+=1;last=action
            assert int(count)==cumulative,(observer,r.trial,action,count,cumulative)
        error=np.linalg.norm(pos-[r.final_x_px,r.final_y_px])
        assert error<1e-7,(observer,r.trial,error)
        assert moves==r.total_moves and fine==r.fine_moves and r.r_count==0
        assert steps[min(2,manual_idx+min(game_reversals,2))]==r.submission_step_px
        up=np.array([r.ref_up_x_px-r.ref_down_x_px,r.ref_up_y_px-r.ref_down_y_px]);up/=np.linalg.norm(up)
        screen_up=np.dot(pos-[r.correct_x_px,r.correct_y_px],up)
        assert abs(screen_up-r.response_screen_up_px)<1e-7
        assert abs(screen_up*r.control_up_normal_sign-r.response_normal_px)<1e-7
        assert abs(abs(r.response_normal_px)-r.response_abs_px)<1e-7
        xy=baseline_xy(r)
        radii=np.linalg.norm(xy[[3,5]]-xy[4],axis=1)
        t.loc[r.Index,'neighbor_radius_px']=radii.mean()
        audits.append(dict(observer=observer,trial=r.trial,replay_error_px=error,fine_moves=fine))
    # Geometry is deterministic by family up to translation/reflection and pose.
    for (stimulus_set,family),g in t.groupby(['stimulus_set','curve_family']):
        r=next(g[g.condition_type=='baseline'].itertuples());xy=baseline_xy(r)
        normal=np.array([r.target_normal_x,r.target_normal_y]);normal/=np.linalg.norm(normal)
        tangent=np.array([normal[1],-normal[0]])
        centered=xy-xy[4]
        local=np.column_stack((centered@tangent,centered@normal))
        if stimulus_set=='curvature_maxima':local[:,1]*=np.sign(r.target_analytic_curvature_px)
        elif r.reversed:local[:,1]*=-1
        chords=np.linalg.norm(np.diff(xy[POINTS],axis=0),axis=1)
        radii=np.linalg.norm(xy[[3,5]]-xy[4],axis=1)
        geometry.append(dict(observer=observer,cohort=cohort,stimulus_set=stimulus_set,curve_family=family,
          central_gap_px=chords[3],neighbor_left_px=radii[0],neighbor_right_px=radii[1],neighbor_mean_px=radii.mean(),
          tangent_span_px=np.ptp(local[:,0]),normal_span_px=np.ptp(local[:,1]),
          diameter_px=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=2).max(),
          visible_polyline_length_px=chords.sum(),min_visible_chord_px=chords.min(),max_visible_chord_px=chords.max(),
          target_curvature_px=r.target_analytic_curvature_px,
          **{f'visible_chord_{i}_px':v for i,v in enumerate(chords)}))
        for i,(x,y) in enumerate(local):coordinates.append(dict(observer=observer,cohort=cohort,stimulus_set=stimulus_set,curve_family=family,point=i,x_px=x,y_px=y))
    t['observer']=observer;t['cohort']=cohort;t['source_file']=name
    t['curvature_sign']=np.sign(t.target_analytic_curvature_px)
    t['aligned_bias_px']=np.where(t.stimulus_set=='curvature_maxima',t.response_normal_px*t.curvature_sign,np.nan)
    t['absolute_error_neighbor_fraction']=t.response_abs_px/t.neighbor_radius_px
    quality.append(dict(observer=observer,cohort=cohort,participant_id=t.participant_id.iloc[0],date=name.split('_')[3],
       counterbalance_group=int(t.counterbalance_group.iloc[0]),trials=len(t),median_seconds=t.reaction_time_ms.median()/1000,
       trial_minutes=t.reaction_time_ms.sum()/60000,median_fine_moves=t.fine_moves.median(),
       blocked_trials=int((t.blocked_submissions>0).sum()),max_abs_response_px=t.response_abs_px.max(),
       responses_over_50px=int((t.response_abs_px>50).sum()),design_versions='; '.join(sorted(t.design_version.unique())),
       screen_size_px=t.screen_size_px.iloc[0] if 'screen_size_px' in t else np.nan))
    frames.append(t)

t=pd.concat(frames,ignore_index=True);assert len(t)==1848 and t.observer.nunique()==6
save(pd.DataFrame(sources),'sources');save(pd.DataFrame(audits),'recording_audit');save(pd.DataFrame(quality),'observer_quality')
save(pd.DataFrame(geometry),'geometry_by_observer');save(pd.DataFrame(coordinates),'canonical_coordinates')
save(t[['observer','cohort','source_file','trial','trial_uid','stimulus_set','curve_family','condition_type',
        'perturb_index','perturb_sign','response_normal_px','response_abs_px','aligned_bias_px','neighbor_radius_px',
        'absolute_error_neighbor_fraction','reaction_time_ms','initial_side','matched_pose_id','repetition']],'derived_responses')

pairs=[]
for (observer,stimulus_set,family),g in t.groupby(['observer','stimulus_set','curve_family']):
    for (point,rep),s in g[g.condition_type=='single'].groupby(['perturb_index','repetition']):
        assert len(s)==2 and set(s.perturb_sign)=={-1,1}
        plus=s[s.perturb_sign==1].iloc[0];minus=s[s.perturb_sign==-1].iloc[0]
        for field in ['initial_side','initial_offset_px','rotation_deg','reversed']:
            assert plus[field]==minus[field],(observer,field)
        assert np.allclose(baseline_xy(plus),baseline_xy(minus))
        delta=abs(json.loads(plus.perturb_actual_px)[0]);assert abs(delta-abs(json.loads(minus.perturb_actual_px)[0]))<1e-8
        zeros=g[(g.condition_type=='baseline')&(g.matched_pose_id==plus.matched_pose_id)&(g.repetition==rep)]
        if stimulus_set=='curvature_maxima':assert len(zeros)==1
        assert len(zeros)<=1
        r0=np.nan
        if len(zeros):
            zero=zeros.iloc[0]
            assert np.allclose(baseline_xy(plus),baseline_xy(zero))
            for field in ['initial_side','initial_offset_px','rotation_deg','reversed']:assert zero[field]==plus[field]
            r0=zero.response_normal_px
        pairs.append(dict(observer=observer,cohort=plus.cohort,stimulus_set=stimulus_set,curve_family=family,
         point=int(point),repetition=int(rep),initial_side=plus.initial_side,delta_px=delta,
         baseline_px=r0,minus_px=minus.response_normal_px,plus_px=plus.response_normal_px,
         minus_shift_px=minus.response_normal_px-r0,plus_shift_px=plus.response_normal_px-r0,
         sensitivity=(plus.response_normal_px-minus.response_normal_px)/(2*delta),
         asymmetry_px=(plus.response_normal_px+minus.response_normal_px)/2-r0,
         minus_trial=int(minus.trial),plus_trial=int(plus.trial)))
j=pd.DataFrame(pairs);assert len(j)==672
j['region']=np.where(abs(j.point-4)==1,'nearest',np.where(abs(j.point-4)==2,'next','outer'))
save(j,'paired_influences')
profile=j.groupby(['observer','cohort','stimulus_set','curve_family','point'],as_index=False).sensitivity.mean()
save(profile,'observer_influence_profiles')
regions=j.groupby(['observer','cohort','stimulus_set','curve_family','region'],as_index=False).sensitivity.mean()
save(regions,'observer_region_influences')
b=t[(t.stimulus_set=='curvature_maxima')&(t.condition_type=='baseline')]
base=b.groupby(['observer','cohort','curve_family'],as_index=False).agg(n=('trial','size'),
    bias_px=('aligned_bias_px','mean'),mae_px=('response_abs_px','mean'),median_error_px=('response_abs_px','median'),
    mae_neighbor_fraction=('absolute_error_neighbor_fraction','mean'))
save(base,'observer_baselines')
starts=[]
for (observer,cohort,family),g in b.groupby(['observer','cohort','curve_family']):
    p=g.pivot(index='matched_pose_id',columns='initial_side',values='response_normal_px')
    starts.append(dict(observer=observer,cohort=cohort,curve_family=family,start_difference_px=(p[1]-p[-1]).mean(),
                       absolute_pair_difference_px=(p[1]-p[-1]).abs().mean()))
save(pd.DataFrame(starts),'starting_side_effects')
summary=base.merge(regions[regions.stimulus_set=='curvature_maxima'].pivot(index=['observer','cohort','curve_family'],columns='region',values='sensitivity').reset_index())
summary=summary.merge(pd.DataFrame(quality)[['observer','counterbalance_group']],on='observer')
save(summary,'observer_family_summary')
cols=['bias_px','mae_px','mae_neighbor_fraction','nearest','next','outer']
cohort_summary=summary.groupby(['cohort','curve_family'],as_index=False)[cols].mean()
save(cohort_summary,'cohort_family_summary')
# Exploratory synthesis only: each independently confirmed observer has weight 1/6.
combined=summary.groupby('curve_family',as_index=False)[cols].mean()
save(combined,'all_six_descriptive_summary')
contrasts=[]
for observer,g in summary.groupby('observer'):
    ref=g[g.curve_family=='parabola'].iloc[0]
    for r in g[g.curve_family!='parabola'].itertuples():
        contrasts.append(dict(observer=observer,cohort=r.cohort,comparison=r.curve_family+' minus parabola',
           nearest_difference=r.nearest-ref.nearest,bias_difference_px=r.bias_px-ref.bias_px,mae_difference_px=r.mae_px-ref.mae_px))
ct=pd.DataFrame(contrasts);save(ct,'observer_primary_contrasts')
ct_groups=ct.merge(pd.DataFrame(quality)[['observer','counterbalance_group']],on='observer')
save(ct_groups[ct_groups.counterbalance_group.isin([0,1])].groupby(['cohort','comparison'],as_index=False)[['nearest_difference','bias_difference_px','mae_difference_px']].mean(),'common_group_contrasts')
sens=[]
for comparison,g in ct.groupby('comparison'):
    values=g.set_index('observer').nearest_difference
    sens.append(dict(comparison=comparison,all_six_mean=values.mean(),earlier_mean=g[g.cohort=='earlier'].nearest_difference.mean(),
        controlled_mean=g[g.cohort=='controlled'].nearest_difference.mean(),positive=int((values>1e-10).sum()),negative=int((values< -1e-10).sum()),
        leave_one_observer_out_min=min(values.drop(o).mean() for o in values.index),leave_one_observer_out_max=max(values.drop(o).mean() for o in values.index)))
save(pd.DataFrame(sens),'contrast_sensitivity')
lr=profile[(profile.stimulus_set=='curvature_maxima')&profile.point.isin([3,5])].pivot(index=['observer','cohort','curve_family'],columns='point',values='sensitivity').reset_index()
lr['left_minus_right']=lr[3]-lr[5];save(lr,'nearest_left_right')
group_weighted=summary.groupby(['counterbalance_group','curve_family'])[cols].mean().groupby('curve_family').mean().reset_index()
save(group_weighted,'equal_counterbalance_group_sensitivity')
gp=profile.groupby(['cohort','stimulus_set','curve_family','point'],as_index=False).sensitivity.mean()
save(gp,'cohort_influence_profiles')
save(j[j.stimulus_set=='curvature_maxima'].groupby(['cohort','curve_family','point'],as_index=False)[['delta_px','minus_shift_px','plus_shift_px','sensitivity','asymmetry_px']].mean(),'responses_by_perturbation')
save(t.sort_values('response_abs_px',ascending=False)[['observer','cohort','trial','stimulus_set','curve_family','condition_type','perturb_index','response_normal_px','response_abs_px','reaction_time_ms']].head(30),'largest_responses')
geom=pd.DataFrame(geometry).groupby(['cohort','stimulus_set','curve_family'],as_index=False).mean(numeric_only=True)
save(geom,'geometry_summary')
coord=pd.DataFrame(coordinates).groupby(['cohort','stimulus_set','curve_family','point'],as_index=False)[['x_px','y_px']].mean()
old=coord[coord.cohort=='earlier'];new=coord[coord.cohort=='controlled']
displacement=old.merge(new,on=['stimulus_set','curve_family','point'],suffixes=('_earlier','_controlled'))
displacement['sampling_displacement_px']=np.hypot(displacement.x_px_controlled-displacement.x_px_earlier,displacement.y_px_controlled-displacement.y_px_earlier)
save(displacement,'sampling_changes')
assert displacement[(displacement.stimulus_set=='curvature_maxima')&(displacement.curve_family=='circle')].sampling_displacement_px.max()<1e-7
# Explicit sensitivity check for an unusually large baseline; primary tables
# above retain the observation. Never use an outlier-dependent threshold.
largest=b[b.cohort=='earlier'].response_abs_px.idxmax()
without=b.drop(index=largest)
baseline_check=without.groupby(['observer','cohort','curve_family'],as_index=False).agg(mae_px=('response_abs_px','mean'),bias_px=('aligned_bias_px','mean'))
save(baseline_check.groupby(['cohort','curve_family'],as_index=False)[['mae_px','bias_px']].mean(),'single_large_baseline_sensitivity')
# Validate v9 results against the previous independent four-observer report.
previous=pd.read_csv(ROOT/'analysis/P001_P004_20261009/family_summary.csv').set_index('curve_family')
current=cohort_summary[cohort_summary.cohort=='controlled'].set_index('curve_family').reindex(previous.index)
assert np.allclose(previous[['nearest','next','outer']],current[['nearest','next','outer']])
assert np.allclose(previous.mean_abs_px,current.mae_px)
assert np.allclose(previous.curvature_aligned_bias_px,current.bias_px)
metrics=dict(total_observers=6,total_trials=len(t),earlier_trials=int((t.cohort=='earlier').sum()),controlled_trials=int((t.cohort=='controlled').sum()),
             matched_trials=int((t.stimulus_set=='curvature_maxima').sum()),original_trials=int((t.stimulus_set=='original').sum()),
             max_replay_error_px=max(a['replay_error_px'] for a in audits),old_circle_trials=int(((t.cohort=='earlier')&(t.curve_family=='circle')).sum()),
             observer_identity='User confirmed older and later reused IDs refer to different people.',
             old_screen_size='Not explicitly recorded in v7 CSV; no imputation from current settings.')
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
print('QUALITY\n',pd.DataFrame(quality).round(3).to_string(index=False))
print('\nCOHORT SUMMARY\n',cohort_summary.round(4).to_string(index=False))
print('\nALL SIX\n',combined.round(4).to_string(index=False))
print('\nCONTRASTS\n',pd.DataFrame(sens).round(4).to_string(index=False))
print('\nOBSERVER NEAREST\n',summary.pivot(index='observer',columns='curve_family',values='nearest').round(3).to_string())
print('\nGEOMETRY\n',geom[['cohort','stimulus_set','curve_family','central_gap_px','neighbor_mean_px','tangent_span_px','normal_span_px']].round(3).to_string(index=False))
print('\nMETRICS\n',json.dumps(metrics,indent=2))
