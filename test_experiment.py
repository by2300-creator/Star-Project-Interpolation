"""Run with ../.venv/bin/python -m unittest -v test_experiment.
Uses SDL's dummy display; no participant data are written to the project.
"""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pygame
from canvas import Canvas, _anchor_vertices, MOVABLE_DOT_COLOR, screen_ordered_endpoints
from practice_feedback import evaluate_feedback
from recorder import DataRecorder
from run_exp import build_trials, parse_args, materialize_trial, main, compute_screen_px
from geometry import geometry_features
from experiment_design import build_practice_trials, DEFAULT_SMALL_FRACTION
from function import generate_function_points, SUPPORTED_FUNCTIONS
from curvature_maxima import (FAMILIES, CURVATURE_LEVELS, analytic_curvature, ARC_OFFSETS, REFERENCE_SPACINGS,
                              VISIBLE_CHORDS, VISIBLE_INDICES, TARGET_NEIGHBOR_DISTANCE, DESIGN_VERSION)


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.canvas = Canvas(pygame.display.set_mode((800, 800)), 800)
        self.canvas.highlight_time = 0
        self.canvas.require_fine_submission = False
        feedback_timer = patch('canvas.FEEDBACK_DURATION_MS',0)
        feedback_timer.start()
        self.addCleanup(feedback_timer.stop)

    def tearDown(self):
        pygame.quit()

    def submit(self, points, meta, moves=()):
        batches = [[pygame.event.Event(pygame.KEYDOWN, key=k) for k in moves],
                   [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(740, 26))]]
        with patch('pygame.event.get', side_effect=batches):
            return self.canvas.run_trial(1, points, meta, 10000)

    def test_all_conditions_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = DataRecorder(str(Path(directory)/'trials.csv'), str(Path(directory)/'presses.csv'))
            self.assertEqual(len(pd.read_csv(recorder.records_path)), 0)
            count = 0
            for block in ('identification', 'segmentation'):
                groups = {}
                for spec in build_trials(parse_args(['--block', block])):
                    points, meta = materialize_trial(spec, 63)
                    baseline = np.column_stack((meta['baseline_x_vals'], meta['baseline_y_vals']))
                    group_key = (spec['stimulus_id'], spec.get('matched_pose_id', 0))
                    previous = groups.setdefault(group_key, baseline)
                    np.testing.assert_allclose(previous, baseline)
                    delta = points[['x','y']].to_numpy() - baseline
                    self.assertAlmostEqual(np.linalg.norm(delta[meta['target_index']]), 0)
                    geo = geometry_features(baseline, meta['target_index'])
                    for i, sign in spec['perturbations']:
                        magnitude = spec.get('perturb_magnitude_units', spec['perturb_fraction'] * geo['spacing'][i])
                        normals = np.asarray(meta.get('analytic_normals', geo['normals']))
                        np.testing.assert_allclose(delta[i], sign * magnitude * normals[i], atol=1e-10)
                    final, presses, result = self.submit(points, meta, (pygame.K_z,))
                    normal = np.array([result['ref_up_x_px']-result['ref_down_x_px'], result['ref_up_y_px']-result['ref_down_y_px']])
                    normal /= np.linalg.norm(normal)
                    initial = np.array([meta['initial_movable_x_px'], meta['initial_movable_y_px']])
                    correct = np.array([result['correct_x_px'], result['correct_y_px']])
                    extent = np.dot(np.array([result['ref_up_x_px'], result['ref_up_y_px']])-correct, normal)
                    expected_up = min(np.dot(initial-correct,normal)+self.canvas.step_sizes[0],extent)
                    self.assertAlmostEqual(result['response_screen_up_px'],expected_up,places=7)
                    self.assertAlmostEqual(result['response_normal_px'],expected_up*meta['control_up_normal_sign'],places=7)
                    self.assertLess(result['ref_up_y_px'],result['ref_down_y_px'])
                    screen_pts = points[['screen_x','screen_y']].to_numpy()
                    self.assertTrue(np.all(np.linalg.norm(screen_pts - 400, axis=1) < 380))
                    if count < 3:
                        recorder.record(count + 1, final, presses, meta, result, points)
                        self.assertEqual(len(pd.read_csv(recorder.records_path)), count + 1)
                        self.assertEqual(len(pd.read_csv(recorder.presses_path)), count + 1)
                    count += 1
            self.assertEqual(count, 308 + 300)
            with self.assertRaises(FileExistsError):
                DataRecorder(recorder.records_path, recorder.presses_path)

    def test_geometry_invariance_and_circle_variation(self):
        for family in ('line','parabola','cubic','quartic','quintic','circle'):
            spec = next(s for s in build_trials(parse_args([])) if s['curve_family'] == family)
            points, meta = materialize_trial(spec, 63)
            base = np.column_stack((meta['baseline_x_vals'],meta['baseline_y_vals']))
            g = geometry_features(base, 4)
            angle = .73
            rotation = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
            h = geometry_features(base @ rotation.T * 2 + 7, 4)
            np.testing.assert_allclose(h['curvature'], g['curvature']/2, atol=1e-10)
            np.testing.assert_allclose(h['curvature_derivative'], g['curvature_derivative']/4, atol=1e-10)
            if family in ('line','circle'):
                self.assertLess(g['local_curvature_derivative_rms'], 1e-10)

    def test_main_creates_two_csvs_before_welcome_and_preserves_on_quit(self):
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory)/'session')
            def close_welcome(*args, **kwargs):
                self.assertEqual(len(list(Path(directory).glob('*.csv'))), 2)
                raise SystemExit
            with patch('run_exp.show_screen', side_effect=close_welcome):
                with self.assertRaises(SystemExit):
                    main(['--output-prefix', prefix])
            self.assertFalse(pygame.get_init())

    def test_main_records_two_submissions(self):
        specs = build_trials(parse_args([]))[:2]
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory)/'session')
            batches = [[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_1), pygame.event.Event(pygame.KEYDOWN,key=pygame.K_z)], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(compute_screen_px()-60,26))]] * 2
            with patch('run_exp.build_trials', return_value=specs), patch('run_exp.show_screen'), patch('pygame.event.get', side_effect=batches):
                self.assertEqual(main(['--skip-tutorial', '--output-prefix', prefix]), 0)
            responses = pd.read_csv(prefix + '_trials.csv')
            presses = pd.read_csv(prefix + '_presses.csv')
            self.assertEqual(len(responses), 2)
            self.assertEqual(responses.trial_uid.tolist(), presses.trial_uid.tolist())
            self.assertTrue((responses.num_points == 9).all())
            self.assertTrue((responses.screen_size_px == 1100).all())
            self.assertTrue((responses.input_version=='2026-10-04_screen_up_down_v2').all())
            self.assertTrue((responses.practice_feedback_received==False).all())
            self.assertTrue((responses.practice_good_fraction==.05).all())
            self.assertTrue((responses.practice_moderate_fraction==.15).all())
            self.assertTrue((responses.practice_feedback_duration_ms==1500).all())
            self.assertTrue((responses.step_sizes_px=='[30, 10, 1]').all())
            np.testing.assert_allclose(responses.response_normal_px,
                responses.response_screen_up_px*responses.control_up_normal_sign)

    def test_revised_conditions(self):
        trials = build_trials(parse_args(['--no-curvature-maxima', '--repetitions', '1']))
        self.assertEqual(len(trials), 108)
        self.assertEqual(sum(t['condition_type'] == 'baseline' for t in trials), 12)
        self.assertEqual(sum(t['condition_type'] == 'single' for t in trials), 96)
        for family in SUPPORTED_FUNCTIONS:
            family_trials = [t for t in trials if t['curve_family'] == family]
            off = [t for t in family_trials if t['target_index'] == 3]
            self.assertEqual(len(off), 1)
            self.assertEqual(off[0]['perturbations'], [])
            center = [t for t in family_trials if t['target_index'] == 4]
            self.assertEqual(len(center), 17)
            self.assertEqual(sum(t['condition_type'] == 'baseline' for t in center), 1)
            singles = [t for t in center if t['condition_type'] == 'single']
            self.assertEqual({t['perturbations'][0] for t in singles},
                             {(i, sign) for i in range(9) if i != 4 for sign in (-1, 1)})
            self.assertTrue(all(t['perturb_fraction'] == 8.0 / 60.0 for t in singles))
        extended = build_trials(parse_args(['--block', 'segmentation', '--targets', '3,4', '--repetitions', '1']))
        self.assertTrue(all(not t['perturbations'] for t in extended if t['target_index'] == 3))
        self.assertEqual(len(extended), 156)

    def test_default_repeats_each_condition_with_opposite_start(self):
        trials = build_trials(parse_args(['--no-curvature-maxima']))
        self.assertEqual(len(trials), 216)
        self.assertEqual(len({t['trial_uid'] for t in trials}), 216)
        self.assertEqual(sum(t['condition_type'] == 'baseline' for t in trials), 24)
        self.assertEqual(sum(t['condition_type'] == 'single' for t in trials), 192)
        groups = {}
        for trial in trials:
            groups.setdefault((trial['stimulus_id'], trial['condition_number']), []).append(trial)
        self.assertEqual(len(groups), 108)
        for repeats in groups.values():
            self.assertEqual(len(repeats), 2)
            self.assertEqual({t['repetition'] for t in repeats}, {1, 2})
            self.assertEqual({t['initial_side'] for t in repeats}, {-1, 1})
            first, second = repeats
            for field in ('perturbations', 'perturb_fraction', 'rotation_deg', 'force_reversed'):
                self.assertEqual(first[field], second[field])
        self.assertEqual(len(build_practice_trials()), 20)

    def test_practice_progression_and_geometry(self):
        specs = build_practice_trials()
        self.assertTrue(all(s['condition_type']=='baseline' and not s['perturbations'] for s in specs))
        self.assertEqual(len(specs), 20)
        self.assertEqual(specs, build_practice_trials())
        self.assertAlmostEqual(specs[0]['practice_strength_fraction'], .1)
        self.assertAlmostEqual(specs[-1]['practice_strength_fraction'], .9)
        self.assertEqual({s['curve_family'] for s in specs}, set(SUPPORTED_FUNCTIONS))
        depths = {}
        for spec in specs:
            points, meta = materialize_trial(spec, 63)
            baseline = np.column_stack((meta['baseline_x_vals'],meta['baseline_y_vals']))
            depth = np.max(np.abs(baseline[:,1]))
            family = spec['curve_family']
            if family != 'line':
                self.assertGreater(depth, 0)
                real, _ = generate_function_points(family, force_reversed=spec['force_reversed'],
                                                  target_index=spec['target_index'])
                self.assertLess(depth, np.max(np.abs(real.y)))
                self.assertGreater(depth, depths.get(family, 0))
            else:
                self.assertAlmostEqual(depth, 0)
            depths[family] = depth
            if family == 'circle':
                curvature = geometry_features(baseline, spec['target_index'])['curvature']
                np.testing.assert_allclose(curvature, curvature[0], atol=1e-8)
            final, presses, result = self.submit(points, meta)
            self.assertTrue(np.isfinite(final).all())
            self.assertLess(np.linalg.norm(np.asarray(final)-400), 380)

    def test_maxima_design_geometry_and_recording(self):
        trials = build_trials(parse_args([]))
        new = [s for s in trials if s['stimulus_set'] == 'curvature_maxima']
        self.assertEqual(len(trials), 308)
        self.assertEqual(len(new), 240)
        self.assertEqual(len({s['trial_uid'] for s in trials}), 308)
        self.assertEqual({s['repetition'] for s in new}, {1, 2})
        self.assertEqual({s['repetition'] for s in trials if s['stimulus_set']=='original'}, {1})
        for family in FAMILIES:
            for level in CURVATURE_LEVELS:
                group = [s for s in new if s['curve_family']==family and s['curvature_level']==level]
                self.assertEqual(len(group), 48)
                self.assertEqual(sum(s['condition_type']=='baseline' for s in group), 16)
                for spec in group:
                    pts, meta = materialize_trial(spec, 63)
                    u = np.asarray(meta['sample_parameters'])
                    n = FAMILIES[family]
                    peak = meta['curvature_peak_parameter']
                    self.assertAlmostEqual(u[4], peak)
                    if family == 'circle':
                        baseline = np.column_stack((meta['baseline_x_vals'], meta['baseline_y_vals']))
                        center = (baseline[0] + baseline[-1])/2
                        radius = meta['circle_radius_units']
                        np.testing.assert_allclose(np.linalg.norm(baseline-center, axis=1), radius)
                        self.assertAlmostEqual(meta['circle_radius_px'], 200.)
                        self.assertAlmostEqual(meta['circle_arc_span_rad'], np.pi)
                        self.assertEqual(meta['target_location_rule'], 'constant_curvature_arc_midpoint')
                        np.testing.assert_allclose(meta['sample_analytic_curvatures'], meta['target_analytic_curvature'])
                        np.testing.assert_allclose(np.diff(u)*radius, np.diff(ARC_OFFSETS))
                        normals = np.asarray(meta['analytic_normals'])
                        np.testing.assert_allclose(np.abs(np.sum(normals*(center-baseline), axis=1)), radius)
                    else:
                        k = abs(float(analytic_curvature(peak, n)))
                        self.assertGreater(k, abs(float(analytic_curvature(peak-1e-4, n))))
                        self.assertGreater(k, abs(float(analytic_curvature(peak+1e-4, n))))
                        # Independent quadrature checks polynomial arc resampling.
                        nodes, weights = np.polynomial.legendre.leggauss(32)
                        for segment, (a,b) in enumerate(zip(u[:-1], u[1:])):
                            q = (a+b)/2 + (b-a)/2*nodes
                            arc = np.sum(weights*np.sqrt(1+(n*q**(n-1))**2))*(b-a)/2*meta['normalization_scale']
                            actual_offsets = meta['sample_arc_offsets']
                            self.assertAlmostEqual(arc, actual_offsets[segment+1]-actual_offsets[segment], places=5)
                    _, _, result = self.submit(pts, meta)
                    self.assertEqual(meta['display_scale_px_per_unit'], 5.)
                    self.assertAlmostEqual(abs(meta['target_analytic_curvature'])/5, CURVATURE_LEVELS[level]/5)
                    self.assertAlmostEqual(meta['target_normal_x'], 0)
                    self.assertAlmostEqual(meta['target_normal_y'], 1)
                    if spec['condition_type'] == 'single':
                        self.assertAlmostEqual(abs(meta['perturb_pixels']), REFERENCE_SPACINGS[spec['perturbations'][0][0]]*spec['perturb_fraction']*5)
                # Baseline and both signs share start, pose and displacement.
                for point in (0,1,2,3,5,6,7,8):
                    pair = [s for s in group if s['repetition']==1 and s['matched_pose_id']==(0,1,2,3,5,6,7,8).index(point)+1]
                    self.assertEqual(len(pair), 3)
                    self.assertEqual(sum(s['condition_type']=='baseline' for s in pair), 1)
                    for field in ('rotation_deg','force_reversed','initial_offset_px','target_shift_x_units','target_shift_y_units'):
                        self.assertEqual(pair[0][field], pair[1][field])
                        self.assertEqual(pair[0][field], pair[2][field])
        with tempfile.TemporaryDirectory() as d:
            recorder = DataRecorder(str(Path(d)/'t.csv'), str(Path(d)/'p.csv'))
            for i, spec in enumerate([next(s for s in new if s['curve_family']=='circle'), next(s for s in trials if s['stimulus_set']=='original')], 1):
                pts, meta = materialize_trial(spec, 63)
                final, presses, result = self.submit(pts, meta)
                recorder.record(i, final, presses, meta, result, pts)
                self.assertEqual(len(pd.read_csv(recorder.records_path)), i)
                self.assertEqual(len(pd.read_csv(recorder.presses_path)), i)
            recorded = pd.read_csv(recorder.records_path)
            self.assertEqual(recorded.iloc[0].stimulus_set, 'curvature_maxima')
            self.assertAlmostEqual(recorded.iloc[0].circle_radius_px, 200.)
            self.assertAlmostEqual(recorded.iloc[0].circle_arc_span_rad, np.pi)
            self.assertEqual(recorded.iloc[0].sample_parameter_kind, 'circle_angle_radians')
            self.assertEqual(recorded.iloc[0].design_version, DESIGN_VERSION)
            self.assertEqual(recorded.iloc[0].screen_size_px, 800)
            self.assertLess(recorded.iloc[0].visible_chord_max_error_px, 1e-6)
            self.assertEqual(recorded.iloc[0].sampling_rule, 'matched_visible_chords_balanced_target_neighbors')
            self.assertAlmostEqual(abs(recorded.iloc[0].target_analytic_curvature_px), CURVATURE_LEVELS[new[0]['curvature_level']]/5)

    def test_strict_spacing_and_1100px_display(self):
        self.assertEqual(compute_screen_px(), 1100)
        self.canvas = Canvas(pygame.display.set_mode((1100, 1100)), 1100)
        self.canvas.highlight_time = 0
        self.canvas.require_fine_submission = False
        reference = VISIBLE_CHORDS*5
        max_raster_error = 0.
        for participant in range(1, 5):
            trials = build_trials(parse_args(['--participant-id', f'P{participant:03}']))
            for spec in trials:
                if spec['stimulus_set'] != 'curvature_maxima':
                    self.assertEqual(spec['geometry_protocol'], 'spacing_controlled_original')
                pts, meta = materialize_trial(spec, 63)
                baseline = np.column_stack((meta['baseline_x_vals'], meta['baseline_y_vals']))
                v = baseline[VISIBLE_INDICES]
                np.testing.assert_allclose(np.linalg.norm(np.diff(v,axis=0),axis=1)*5, reference, atol=1e-8, rtol=0)
                neighbors = np.linalg.norm(baseline[[3,5]]-baseline[4],axis=1)*5
                self.assertAlmostEqual(neighbors[0], neighbors[1], places=8)
                tolerance = .51 if spec['stimulus_set']=='curvature_maxima' else 2.59
                self.assertLessEqual(np.max(abs(neighbors-TARGET_NEIGHBOR_DISTANCE*5)), tolerance)
                # Actual arc positions are recorded, and are NOT matched in v8.
                if spec['curve_family'] != 'circle':
                    self.assertGreater(np.max(abs(np.asarray(meta['sample_arc_offsets'])-ARC_OFFSETS)), .01)
                batches = [[], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1040,26))]]
                with patch('pygame.event.get', side_effect=batches):
                    _, _, result = self.canvas.run_trial(1, pts, meta, 10000)
                self.assertEqual(meta['screen_size_px'], 1100)
                self.assertEqual(meta['display_scale_px_per_unit'], 5.)
                self.assertLess(np.linalg.norm(pts[['screen_x','screen_y']].to_numpy()-550,axis=1).max(), 528)
                self.assertLess(abs(meta['actual_initial_offset_px']-spec['initial_offset_px']), 1e-8)
                if spec['condition_type']=='baseline':
                    raster = pts[['screen_x','screen_y']].to_numpy()[VISIBLE_INDICES].astype(int)
                    error = np.max(abs(np.linalg.norm(np.diff(raster,axis=0),axis=1)-reference))
                    max_raster_error = max(max_raster_error, error)
        # Integer dot centers introduce bounded rounding error, despite exact
        # matching of the continuous coordinates. Do not claim exact raster gaps.
        self.assertLess(max_raster_error, np.sqrt(2))

    def test_original_spacing_preserves_shapes_and_matches_contexts(self):
        from original_controls import ORIGINAL_FAMILIES
        trials = build_trials(parse_args([]))
        original = [s for s in trials if s['stimulus_set']=='original']
        references = {(s['matched_pose_id'], s['condition_type'],
                       s['perturbations'][0][1] if s['perturbations'] else 0): s
                      for s in trials if s['stimulus_set']=='curvature_maxima'
                      and s['curve_family']=='parabola' and s['repetition']==1}
        self.assertEqual(len(original),68)
        for family, degree in ORIGINAL_FAMILIES.items():
            _, legacy = generate_function_points(family, target_index=4, force_reversed=False)
            group = [s for s in original if s['curve_family']==family]
            self.assertEqual(len(group),17)
            self.assertEqual(sum(s['condition_type']=='baseline' for s in group),1)
            self.assertEqual(sum(s['condition_type']=='single' and s['initial_side']==1 for s in group),8)
            for spec in group:
                points, meta = materialize_trial(spec,63)
                self.assertEqual(meta['design_version'],DESIGN_VERSION)
                self.assertEqual(meta['target_location_rule'],'original_zero_curvature_midpoint')
                self.assertEqual(meta['target_analytic_curvature_px'],0.)
                self.assertEqual(meta['baseline_context_scope'],'context_1_only')
                self.assertAlmostEqual(meta['normalization_scale'],legacy['normalization_scale'])
                self.assertAlmostEqual(meta['curve_strength'],legacy['curve_strength'])
                u = np.array(meta['sample_parameters'])
                self.assertEqual(u[4],0.)
                sign = -1 if spec['force_reversed'] else 1
                raw = np.column_stack((meta['baseline_x_vals'],meta['baseline_y_vals']))
                raw -= [spec['target_shift_x_units'],spec['target_shift_y_units']]
                raw[:,1] *= sign
                raw += [meta['shared_window_center_x'],meta['shared_window_center_y']]
                np.testing.assert_allclose(raw, meta['normalization_scale']*np.column_stack((u,meta['curve_strength']*u**degree)),atol=1e-10)
                derivative = meta['curve_strength']*degree*u**(degree-1)
                expected_normals = np.column_stack((-sign*derivative,np.ones(9))) / np.sqrt(1+derivative**2)[:,None]
                np.testing.assert_allclose(meta['analytic_normals'],expected_normals,atol=1e-12)
                expected_k_prime = sign*6*meta['curve_strength']/meta['normalization_scale']**2 if family=='cubic' else 0.
                self.assertAlmostEqual(meta['target_arc_curvature_derivative'],expected_k_prime)
                pattern_sign = spec['perturbations'][0][1] if spec['perturbations'] else 0
                ref = references[(spec['matched_pose_id'],spec['condition_type'],pattern_sign)]
                for field in ('rotation_deg','force_reversed','initial_offset_px', 'initial_side',
                              'target_shift_x_units','target_shift_y_units', 'perturb_magnitude_units'):
                    self.assertEqual(spec[field],ref[field])
                _, reference_meta = materialize_trial(ref,63)
                np.testing.assert_allclose([meta['baseline_x_vals'][4],meta['baseline_y_vals'][4]],
                                           [reference_meta['baseline_x_vals'][4],reference_meta['baseline_y_vals'][4]])
                if spec['condition_type']=='baseline':
                    self.assertEqual(spec['matched_pose_id'],1)
        # New geometry must not leak into practice, segmentation or legacy runs.
        for args in (['--no-curvature-maxima'], ['--block','segmentation']):
            self.assertTrue(all('geometry_protocol' not in s for s in build_trials(parse_args(args))))
        self.assertTrue(all('geometry_protocol' not in s for s in build_practice_trials()))
        with tempfile.TemporaryDirectory() as d:
            recorder = DataRecorder(str(Path(d)/'t.csv'),str(Path(d)/'p.csv'))
            spec = next(s for s in original if s['curve_family']=='cubic' and s['condition_type']=='single')
            points,meta = materialize_trial(spec,63)
            final,presses,result = self.submit(points,meta,(pygame.K_z,))
            recorder.record(1,final,presses,meta,result,points)
            row = pd.read_csv(recorder.records_path).iloc[0]
            self.assertEqual(row.geometry_protocol,'spacing_controlled_original')
            self.assertEqual(row.baseline_context_scope,'context_1_only')
            self.assertEqual(row.target_analytic_curvature_px,0.)
            self.assertLess(row.visible_chord_max_error_px,1e-6)
            self.assertEqual(pd.read_csv(recorder.presses_path).iloc[0].design_version,DESIGN_VERSION)

    def test_maxima_switch_validation_and_partitions(self):
        with patch('run_exp.ENABLE_CURVATURE_MAXIMA', False):
            self.assertTrue(all(s['stimulus_set']=='original' for s in build_trials(parse_args([]))))
        with self.assertRaises(ValueError):
            build_trials(parse_args(['--repetitions','2']))
        a = build_trials(parse_args(['--partition-count','2','--partition-index','1']))
        b = build_trials(parse_args(['--partition-count','2','--partition-index','2']))
        self.assertEqual(len(a), 137)
        self.assertEqual(len(b), 171)
        self.assertFalse({s['trial_uid'] for s in a} & {s['trial_uid'] for s in b})

    def test_reference_matches_original_parabola(self):
        reference, reference_meta = generate_function_points('parabola', target_index=4, force_reversed=False)
        new = [s for s in build_trials(parse_args([])) if s['stimulus_set']=='curvature_maxima']
        self.assertEqual(set(FAMILIES), {'parabola', 'circle', 'cubic', 'quartic', 'quintic'})
        for spec in new:
            _, meta = materialize_trial(spec, 63)
            self.assertAlmostEqual(abs(meta['target_analytic_curvature_px']), reference_meta['target_analytic_curvature']/5)
        for family in FAMILIES:
            for condition in range(24):
                repeats = [s for s in new if s['curve_family']==family and s['condition_number']==condition]
                self.assertEqual(len(repeats),2)
                self.assertEqual({s['initial_side'] for s in repeats},{-1,1})
                self.assertAlmostEqual(repeats[0]['initial_offset_px'], -repeats[1]['initial_offset_px'])

    def test_participant_order_and_pose_counterbalance(self):
        a = build_trials(parse_args(['--participant-id','P001']))
        self.assertEqual(a, build_trials(parse_args(['--participant-id','P001'])))
        b = build_trials(parse_args(['--participant-id','P002']))
        self.assertNotEqual([s['trial_uid'] for s in a], [s['trial_uid'] for s in b])
        self.assertEqual({s['trial_uid'] for s in a}, {s['trial_uid'] for s in b})
        self.assertFalse(any(s['stimulus_set']=='original' and s['curve_family'] in ('parabola','circle')
                             and s['target_index']==4 for s in a))
        self.assertEqual(sum(s['stimulus_set']=='original' and s['curve_family']=='parabola'
                             and s['target_index']==3 for s in a), 0)
        self.assertTrue(all(s['target_index']==4 for s in a))
        practice = build_practice_trials(include_off_center=False)
        self.assertEqual(len(practice),20)
        self.assertTrue(all(s['target_index']==4 for s in practice))
        self.assertEqual(sum(s['condition_type']=='baseline' for s in a),84)
        poses = {i:set() for i in range(1,9)}
        for participant in range(1,5):
            trials = build_trials(parse_args(['--participant-id',f'P{participant:03}']))
            for context in poses:
                matched = [s for s in trials if s['stimulus_set']=='curvature_maxima'
                           and s['matched_pose_id']==context and s['repetition']==1]
                self.assertEqual(len(matched),15)
                for field in ('rotation_deg','force_reversed','initial_offset_px',
                              'target_shift_x_units','target_shift_y_units'):
                    self.assertEqual(len({s[field] for s in matched}),1)
                targets = []
                for spec in matched:
                    _, meta = materialize_trial(spec, 63)
                    targets.append([meta['baseline_x_vals'][4], meta['baseline_y_vals'][4]])
                np.testing.assert_allclose(targets, np.tile(targets[0], (15,1)))
                poses[context].add((matched[0]['rotation_deg'],matched[0]['force_reversed']))
            # Exercise the real renderer for every pose group, including bounds.
            for spec in trials:
                if spec['stimulus_set']=='curvature_maxima':
                    pts, meta = materialize_trial(spec,63)
                    self.submit(pts,meta)
        for observed in poses.values():
            self.assertEqual(observed,{(-15.,False),(15.,False),(-15.,True),(15.,True)})

    def test_reported_quintic_off_center_target_and_response_axis(self):
        # Previous v5 trial 3 survives only in legacy mode, not combined mode.
        spec = next(s for s in build_trials(parse_args(['--no-curvature-maxima'])) if s['curve_family']=='quintic'
                    and s['stimulus_set']=='original' and s['target_index']==3)
        self.assertEqual(spec['condition_type'],'baseline')
        self.assertEqual(spec['perturbations'],[])
        pts, meta = materialize_trial(spec,63)
        _, _, result = self.submit(pts,meta)
        correct = np.array([result['correct_x_px'],result['correct_y_px']])
        np.testing.assert_allclose(correct,pts.loc[3,['screen_x','screen_y']].to_numpy(dtype=float))
        self.assertGreater(np.linalg.norm(correct-pts.loc[4,['screen_x','screen_y']].to_numpy(dtype=float)),1)
        start = np.array([meta['initial_movable_x_px'],meta['initial_movable_y_px']])
        self.assertAlmostEqual(np.linalg.norm(start-correct),abs(spec['initial_offset_px']))
        a = np.array([result['ref_up_x_px'],result['ref_up_y_px']])
        b = np.array([result['ref_down_x_px'],result['ref_down_y_px']])
        axis = (a-b)/np.linalg.norm(a-b)
        self.assertAlmostEqual(abs(np.dot(start-correct,axis)),np.linalg.norm(start-correct))

    def test_submission_requires_current_fine_mode_and_fine_movement(self):
        self.canvas.require_fine_submission = True
        for confirm in ('mouse', pygame.K_RETURN, pygame.K_SPACE):
            with self.subTest(confirm=confirm):
                pts, meta = materialize_trial(build_trials(parse_args([]))[0],63)
                key = lambda k: pygame.event.Event(pygame.KEYDOWN,key=k)
                up = lambda k: pygame.event.Event(pygame.KEYUP,key=k)
                click = pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(740,26))
                def submit_events():
                    return [click] if confirm=='mouse' else [up(confirm),key(confirm)]
                script = iter([submit_events(), [key(pygame.K_1)], submit_events(),
                               [key(pygame.K_z),key(pygame.K_3)], submit_events(),
                               [key(pygame.K_1)], submit_events()])
                posted=[]
                def events():
                    if posted:
                        batch=posted[:]; posted.clear(); return batch
                    return next(script)
                with patch('pygame.event.get',side_effect=events), patch('pygame.event.post',side_effect=posted.append):
                    _, _, result = self.canvas.run_trial(1,pts,meta,10000)
                self.assertEqual(result['blocked_submissions'],3)
                self.assertEqual(result['fine_moves'],1)
                self.assertEqual(result['submission_step_px'],1)
                self.assertEqual(meta['initial_step_px'],self.canvas.step_sizes[0])
        # Automatic reversal refinement also counts as fine adjustment.
        pts,meta=materialize_trial(build_trials(parse_args([]))[0],63)
        _,_,result=self.submit(pts,meta,[pygame.K_z,pygame.K_SLASH,pygame.K_z])
        self.assertEqual(result['submission_step_px'],1)
        self.assertEqual(result['fine_moves'],1)

    def test_experimenter_viewer_bypasses_gate_and_navigates_without_recording(self):
        from canvas import ExperimenterNavigation
        import check_exp
        self.canvas.experimenter_mode=True
        self.canvas.require_fine_submission=True
        pts,meta=materialize_trial(build_trials(parse_args([]))[0],63)
        _,_,result=self.submit(pts,meta,[pygame.K_c])
        self.assertAlmostEqual(result['response_normal_px'],0)
        self.assertEqual(result['fine_moves'],0)
        events=[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_g),
                pygame.event.Event(pygame.KEYDOWN,key=pygame.K_2,unicode='2'),
                pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)]
        with patch('pygame.event.get',return_value=events):
            with self.assertRaises(ExperimenterNavigation) as caught:
                self.canvas.run_trial(1,pts,meta,10000)
        self.assertEqual(caught.exception.value,1)
        seen=[]
        actions=iter([('relative',1),('relative',-1),('absolute',307),None,'exit'])
        def inspect(canvas, number, points, metadata, fps, record=False):
            self.assertTrue(canvas.experimenter_mode)
            self.assertFalse(canvas.require_fine_submission)
            seen.append(number)
            action=next(actions)
            if action=='exit': raise SystemExit
            if action is not None: raise ExperimenterNavigation(*action)
        with tempfile.TemporaryDirectory() as d:
            with patch.object(Canvas,'run_trial',inspect):
                self.assertEqual(check_exp.main(['--output-prefix',str(Path(d)/'never_written')]),0)
            self.assertEqual(list(Path(d).iterdir()),[])
        self.assertEqual(seen,['1/308','2/308','1/308','308/308','308/308'])

    def test_fine_step_and_stale_keyboard_confirmation(self):
        spec = build_trials(parse_args([]))[0]
        pts, meta = materialize_trial(spec, 63)
        self.canvas.default_step_idx = 2
        _, _, result = self.submit(pts, meta, [pygame.K_z])
        self.assertAlmostEqual(result['response_normal_px'], meta['actual_initial_offset_px']+meta['control_up_normal_sign'])
        self.assertEqual(meta['initial_step_px'], 1)
        batches = [[pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(740,26),trial_token=-1)],
                   [pygame.event.Event(pygame.QUIT)]]
        with patch('pygame.event.get',side_effect=batches):
            with self.assertRaises(SystemExit):
                self.canvas.run_trial(2, pts, meta, 10000)

    def test_markers_follow_axis_and_dot_draws_on_top(self):
        for a,b in [((250,30),(680,620)), ((35,300),(740,500)), ((400,25),(400,775))]:
            vertices = _anchor_vertices(b, a, 10)
            tip = np.array(vertices[0]) - a
            direction = np.array(b) - a
            self.assertGreater(np.dot(tip, direction), 0)
            self.assertAlmostEqual(tip[0]*direction[1]-tip[1]*direction[0], 0, places=8)
            for dot in (a,b):
                self.canvas.screen.fill((0,0,0))
                self.canvas.draw_response_guides(a,b,dot)
                self.assertEqual(tuple(self.canvas.screen.get_at(dot)[:3]), MOVABLE_DOT_COLOR)

    def test_screen_controls_and_outward_arrows(self):
        for positive,negative in [((400,775),(400,25)),((300,20),(600,750)),
                                  ((20,400),(780,400)),((780,400),(20,400))]:
            up,down,sign=screen_ordered_endpoints(positive,negative)
            self.assertLessEqual(up[1],down[1])
            if up[1]==down[1]: self.assertLess(up[0],down[0])
            self.assertEqual(up,positive if sign==1 else negative)
            with patch('canvas._draw_anchor_triangle') as draw:
                self.canvas.draw_response_guides(up,down,(400,400))
                for call,opposite in zip(draw.call_args_list,[down,up]):
                    _,toward,anchor,_=call.args
                    tip=np.array(_anchor_vertices(toward,anchor,10)[0])-anchor
                    outward=np.array(anchor)-opposite
                    self.assertGreater(np.dot(tip,outward),0)
        spec=build_trials(parse_args([]))[0]
        for angle in (0,45,90,135,180,225,270,315):
            for key,direction in [(pygame.K_z,-1),(pygame.K_UP,-1),(pygame.K_SLASH,1),(pygame.K_DOWN,1)]:
                rotated=dict(spec,rotation_deg=angle)
                points,meta=materialize_trial(rotated,63)
                _,_,result=self.submit(points,meta,(pygame.K_1,key))
                dy=result['final_y']-meta['initial_movable_y_px']
                dx=result['final_x']-meta['initial_movable_x_px']
                if abs(dy)>1e-8: self.assertGreater(dy*direction,0)
                else: self.assertGreater(dx*direction,0)

    def test_practice_feedback_boundaries_and_events(self):
        for error,expected in [(0,'good'),(5,'good'),(-5,'good'),(5.001,'moderate'),
                               (15,'moderate'),(-15,'moderate'),(15.001,'needs_adjustment')]:
            self.assertEqual(evaluate_feedback(error,100)['level'],expected)
            self.assertEqual(evaluate_feedback(error*2,200)['level'],expected)
        with self.assertRaises(ValueError): evaluate_feedback(1,0)
        message=evaluate_feedback(2,100)
        events=[pygame.event.Event(pygame.KEYDOWN,key=k) for k in [pygame.K_ESCAPE,pygame.K_RETURN,pygame.K_SPACE]]
        with patch('canvas.FEEDBACK_DURATION_MS',1500),patch('pygame.time.get_ticks',side_effect=[0,0,1500]),patch('pygame.event.get',return_value=events) as get:
            self.canvas.show_practice_feedback(message,10000)
            self.assertEqual(get.call_count,1)
        with patch('canvas.FEEDBACK_DURATION_MS',1500),patch('pygame.time.get_ticks',return_value=0),patch('pygame.event.get',return_value=[pygame.event.Event(pygame.QUIT)]):
            with self.assertRaises(SystemExit): self.canvas.show_practice_feedback(message,10000)

    def test_twenty_practice_trials_before_recorded_trials(self):
        real_specs = build_trials(parse_args([]))[:1]
        original = Canvas.run_trial
        practice_seen = []
        feedback_seen = []
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory)/'session')
            def automated(canvas, trial, points, meta, fps, record=True):
                if not record:
                    practice_seen.append(meta['practice_trial'])
                    self.assertEqual(len(pd.read_csv(prefix+'_trials.csv')), 0)
                    self.assertEqual(len(pd.read_csv(prefix+'_presses.csv')), 0)
                else:
                    self.assertEqual(practice_seen, list(range(1,21)))
                batches = [[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_1), pygame.event.Event(pygame.KEYDOWN,key=pygame.K_z)], [pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(compute_screen_px()-60,26))]]
                with patch('pygame.event.get', side_effect=batches), patch('pygame.time.delay'):
                    return original(canvas,trial,points,meta,10000,record=record)
            enter = pygame.event.Event(pygame.KEYDOWN,key=pygame.K_RETURN)
            with patch('run_exp.build_trials',return_value=real_specs), patch('run_exp.show_screen'), patch.object(Canvas,'run_trial',automated), patch.object(Canvas,'show_practice_feedback',side_effect=lambda feedback,fps:feedback_seen.append(feedback)), patch('pygame.event.get',return_value=[enter]):
                main(['--output-prefix',prefix])
            self.assertEqual(len(feedback_seen),20)
            self.assertTrue(all(f['reference_spacing_px']>0 for f in feedback_seen))
            self.assertEqual(len(pd.read_csv(prefix+'_trials.csv')),1)
            self.assertEqual(len(pd.read_csv(prefix+'_presses.csv')),1)

    def test_escape_is_ignored_without_submitting_or_quitting(self):
        from run_exp import show_screen
        esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        # Welcome/break screens ignore Escape rather than advancing.
        with patch('pygame.event.get', side_effect=[[esc],[enter]]) as events:
            show_screen(pygame,self.canvas.screen,'Test')
            self.assertEqual(events.call_count,2)
        with patch('pygame.event.get', side_effect=[[esc],[enter]]) as events:
            self.canvas.run_tutorial([],10000)
            self.assertEqual(events.call_count,2)
        spec = build_trials(parse_args([]))[0]
        for expert in (False,True):
            self.canvas.experimenter_mode = expert
            points,meta = materialize_trial(spec,63)
            _,presses,result = self.submit(points,meta,(pygame.K_ESCAPE,pygame.K_z))
            self.assertEqual(result['total_moves'],1)
            self.assertFalse(any('esc' in str(action).lower() for action in presses))

    def test_quit_does_not_submit(self):
        spec = build_trials(parse_args([]))[0]
        points, meta = materialize_trial(spec, 63)
        with patch('pygame.event.get', return_value=[pygame.event.Event(pygame.QUIT)]):
            with self.assertRaises(SystemExit):
                self.canvas.run_trial(1, points, meta, 60)

    def test_both_csvs_are_current_before_next_trial(self):
        specs = build_trials(parse_args([]))[:3]
        with tempfile.TemporaryDirectory() as directory:
            prefix = str(Path(directory)/'session')
            original_run_trial = Canvas.run_trial

            def check_disk_then_run(canvas, trial, points, meta, fps):
                responses = pd.read_csv(prefix + '_trials.csv')
                presses = pd.read_csv(prefix + '_presses.csv')
                self.assertEqual(len(responses), trial - 1)
                self.assertEqual(len(presses), trial - 1)
                self.assertEqual(responses.trial_uid.tolist(), presses.trial_uid.tolist())
                if trial == 3:
                    # Exit during the next trial: the previous two must already be durable.
                    raise SystemExit
                keys = [pygame.K_1] + [pygame.K_z] * trial
                batches = [[pygame.event.Event(pygame.KEYDOWN, key=k) for k in keys],
                           [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(compute_screen_px()-60,26))]]
                with patch('pygame.event.get', side_effect=batches):
                    return original_run_trial(canvas, trial, points, meta, fps)

            with patch('run_exp.build_trials', return_value=specs), patch('run_exp.show_screen'), patch.object(Canvas, 'run_trial', check_disk_then_run):
                with self.assertRaises(SystemExit):
                    main(['--skip-tutorial', '--output-prefix', prefix])
            responses = pd.read_csv(prefix + '_trials.csv')
            presses = pd.read_csv(prefix + '_presses.csv')
            self.assertEqual(responses.trial.tolist(), [1, 2])
            self.assertEqual(presses.trial.tolist(), [1, 2])
            self.assertEqual(presses.loc[0, 'press_1'], 'step_small_0')
            self.assertEqual(presses.loc[0, 'press_2'], 'up_0')
            self.assertTrue(pd.isna(presses.loc[0, 'press_3']))
            self.assertEqual(presses.loc[1, 'press_3'], 'up_0')

if __name__ == '__main__':
    unittest.main()
