"""Descriptive single-subject analysis; raw CSVs are never modified."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from run_exp import build_trials, parse_args, materialize_trial

stem = ROOT / 'data/pilot_identification_s1_20260925_201233_021660'
t = pd.read_csv(str(stem) + '_trials.csv')
p = pd.read_csv(str(stem) + '_presses.csv')
assert t.trial.tolist() == list(range(1, 109))
assert not t.trial_uid.duplicated().any()
assert t.trial_uid.equals(p.trial_uid) and t.trial.equals(p.trial)
assert np.isfinite(t[['response_normal_px', 'reaction_time_ms', 'total_moves']]).all().all()
specs = build_trials(parse_args(['--no-curvature-maxima', '--repetitions', '1']))
assert [s['trial_uid'] for s in specs] == t.trial_uid.tolist()
coord_error = 0.
for spec, (_, row) in zip(specs, t.iterrows()):
    pts, meta = materialize_trial(spec, 63)
    for i in range(9):
        coord_error = max(coord_error, abs(row[f'x{i}_math']-pts.loc[i, 'x']), abs(row[f'y{i}_math']-pts.loc[i, 'y']))
cols = sorted([c for c in p if c.startswith('press_')], key=lambda c: int(c.split('_')[1]))
audit = []
for (_, r), (_, b) in zip(t.iterrows(), p.iterrows()):
    pos = np.array([r.initial_movable_x_px, r.initial_movable_y_px])
    last = None
    game = cumulative = base = manual = 0
    steps = []
    for c in cols:
        if pd.isna(b[c]):
            continue
        action, count = b[c].rsplit('_', 1)
        if action.startswith('step_'):
            base = {'step_small': 2, 'step_medium': 1, 'step_big': 0}[action]
            game = 0
            last = None
            manual += 1
        else:
            assert action in ('up', 'down')
            if last is not None and last != action:
                game += 1
                cumulative += 1
            step = [10, 5, 1][min(2, base + min(game, 2))]
            steps.append(step)
            target = np.array([r[f'ref_{action}_x_px'], r[f'ref_{action}_y_px']])
            delta = target - pos
            dist = np.linalg.norm(delta)
            pos = target if dist <= step else pos + delta * step / dist
            last = action
        assert int(count) == cumulative
    assert len(steps) == r.total_moves
    audit.append(dict(trial=r.trial, manual=manual, reversals=cumulative,
                      one_px=steps.count(1), five_px=steps.count(5), ten_px=steps.count(10),
                      replay_error=np.linalg.norm(pos-[r.final_x_px, r.final_y_px])))
a = pd.DataFrame(audit)
t = t.merge(a, on='trial', validate='one_to_one')
assert a.replay_error.max() < 1e-8
unit = t[['ref_up_x_px', 'ref_up_y_px']].to_numpy()-t[['ref_down_x_px', 'ref_down_y_px']].to_numpy()
unit /= np.linalg.norm(unit, axis=1)[:, None]
projection = np.sum((t[['final_x_px', 'final_y_px']].to_numpy()-t[['correct_x_px', 'correct_y_px']].to_numpy())*unit, axis=1)
assert np.max(np.abs(projection-t.response_normal_px)) < 1e-8
s = t[t.condition_type == 'single'].copy()
base = t[t.condition_type == 'baseline'].copy()
pairs = []
for (family, point), g in s.groupby(['curve_family', 'perturb_index']):
    plus = g[g.perturb_sign == 1].iloc[0]
    minus = g[g.perturb_sign == -1].iloc[0]
    for col in ['stimulus_id', 'initial_side', 'rotation_deg', 'reversed', 'display_scale_px_per_unit']:
        assert plus[col] == minus[col]
    delta = abs(json.loads(plus.perturb_actual_px)[0])
    diff = plus.response_normal_px-minus.response_normal_px
    pairs.append(dict(curve_family=family, point=int(point), distance=abs(int(point)-4),
                      delta_px=delta, minus_response_px=minus.response_normal_px,
                      plus_response_px=plus.response_normal_px, difference_px=diff,
                      influence=diff/(2*delta), plus_trial=int(plus.trial), minus_trial=int(minus.trial)))
j = pd.DataFrame(pairs)
order = ['line', 'parabola', 'cubic', 'quartic', 'quintic', 'circle']
summary = s.groupby('curve_family').agg(n=('trial', 'size'), mean_signed_px=('response_normal_px', 'mean'),
    mean_absolute_px=('response_abs_px', 'mean'), median_rt_ms=('reaction_time_ms', 'median'))
summary['minus_mean_px'] = s[s.perturb_sign == -1].groupby('curve_family').response_normal_px.mean()
summary['plus_mean_px'] = s[s.perturb_sign == 1].groupby('curve_family').response_normal_px.mean()
summary['plus_minus_difference_px'] = summary.plus_mean_px-summary.minus_mean_px
summary['mean_influence'] = j.groupby('curve_family').influence.mean()
summary = summary.reindex(order)
metrics = dict(trials=len(t), matched_pairs=len(j), max_coordinate_error=float(coord_error),
    max_press_replay_error=float(a.replay_error.max()), median_rt_ms=float(t.reaction_time_ms.median()),
    active_minutes=float(t.reaction_time_ms.sum()/60000), total_moves=int(t.total_moves.sum()),
    no_movement_trials=t.loc[t.total_moves == 0, 'trial'].tolist(),
    one_px_trials=int((a.one_px > 0).sum()), manual_step_trials=int((a.manual > 0).sum()),
    no_reversal_trials=int((a.reversals == 0).sum()),
    endpoints_multiple_10=int(np.isclose(t.response_normal_px/10, np.round(t.response_normal_px/10), atol=1e-8).sum()),
    perturb_min_px=float(j.delta_px.min()), perturb_max_px=float(j.delta_px.max()),
    positive_pairs=int((j.difference_px > 1e-8).sum()), zero_pairs=int((j.difference_px.abs() <= 1e-8).sum()),
    negative_pairs=int((j.difference_px < -1e-8).sum()))
print(json.dumps(metrics, indent=2))
print('SINGLE TRIAL SUMMARY\n', summary.round(3).to_string())
print('BASELINES\n', base[['trial', 'curve_family', 'target_index', 'response_normal_px', 'total_moves', 'reaction_time_ms']].round(3).to_string(index=False))
print('PAIR DIFFERENCES\n', j.pivot(index='curve_family', columns='point', values='difference_px').reindex(order).round(2).to_string())
print('INFLUENCES\n', j.pivot(index='curve_family', columns='point', values='influence').reindex(order).round(3).to_string())
print('STEP TOTALS', a[['one_px', 'five_px', 'ten_px', 'manual']].sum().to_dict())
print('NEAR FAR\n', j.assign(neighbor=j.distance == 1).groupby(['curve_family','neighbor']).influence.mean().round(3).to_string())
print('QUARTERS\n', t.assign(quarter=(t.trial-1)//27+1).groupby('quarter').agg(median_rt_ms=('reaction_time_ms','median'), mean_abs_px=('response_abs_px','mean')).to_string())
print('START\n', s.groupby(['curve_family','initial_side']).response_normal_px.mean().round(3).to_string())
j.to_csv(OUT/'matched_influences.csv', index=False)
summary.to_csv(OUT/'shape_summary.csv')
(OUT/'metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 3, figsize=(12, 7), layout='constrained', sharex=True, sharey=True)
for ax, family in zip(axes.flat, order):
    z = j[j.curve_family == family].sort_values('point')
    for col, label, color, marker in [('minus_response_px', 'Negative perturbation', '#26788e', 'o'), ('plus_response_px', 'Positive perturbation', '#c65c32', 's')]:
        ax.plot(z.point, z[col], marker=marker, color=color, label=label)
    ax.axhline(0, color='#888888', linewidth=.8)
    ax.axvline(4, color='#cccccc', linestyle=':', linewidth=1)
    ax.set(title=family.capitalize(), xlabel='Perturbed dot index (target = 4)', ylabel='Signed response (pixels)', xticks=[0,1,2,3,5,6,7,8])
axes[0,0].legend(fontsize=8)
fig.suptitle('New subject: responses to opposite perturbations\nOne observation per dot and direction; baselines excluded', fontsize=13)
fig.savefig(OUT/'responses.png', dpi=170)
plt.close(fig)
