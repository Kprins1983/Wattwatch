"""Playback tests using the real minute sampler and stored profiles."""
import importlib.util
import sys
import unittest
from pathlib import Path

path = Path(__file__).parents[1] / 'custom_components/wattwatch/engine.py'
spec = importlib.util.spec_from_file_location('short_engine', path)
engine = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = engine
spec.loader.exec_module(engine)


def feed(profile, start, count, power):
    alerts = []
    for minute in range(start, start + count):
        result = profile.sample(86400 + minute * 60, power(minute),
                                minute // 60 % 24, str(minute // 1440))
        if result and result['status'] == 'anomaly':
            alerts.append(result.copy())
    return alerts


class ShortWindows(unittest.TestCase):
    def test_constant_load_changes_spike_and_gap(self):
        trained = engine.Profile()
        self.assertFalse(feed(trained, 0, 10081, lambda m: 90))
        for level, direction in [(0, 'low'), (180, 'high')]:
            p = engine.Profile.load(trained.dump())
            self.assertFalse(feed(p, 10081, 20, lambda m: level))
            self.assertEqual(feed(p, 10101, 1, lambda m: level)[0]['direction'], direction)
        p = engine.Profile.load(trained.dump())
        self.assertFalse(feed(p, 10081, 41, lambda m: 2000 if m == 10084 else 90))
        self.assertFalse(feed(p, 10122, 31, lambda m: None if m == 10137 else 0))

    def test_normal_compressor_cycle_and_prolonged_stop(self):
        p = engine.Profile()
        self.assertFalse(feed(p, 0, 8 * 1440, lambda m: 100 if m % 60 < 20 else 0))
        alerts = feed(p, 8 * 1440, 121, lambda m: 0)
        self.assertTrue(any(r['direction'] == 'low' for r in alerts))

    def test_sensitivity_changes_short_and_hourly_detection(self):
        baseline = engine.Profile()
        feed(baseline, 0, 10081, lambda m: 100)
        for mode, short_alarm, hourly_alarm in [
                ('sensitive', True, True), ('normal', True, False), ('wide', False, False)]:
            p = engine.Profile.load(baseline.dump())
            for minute in range(21):
                result = p.sample(10 * 86400 + minute * 60, 130, 0, '10', mode)
            self.assertEqual(bool(result and result['status'] == 'anomaly'), short_alarm)
            for hour in range(2):
                result = p.evaluate(dict(start=10 * 86400 + hour * 3600,
                                         hour=hour, day='10', watts=140), mode)
            self.assertEqual(result['status'] == 'anomaly', hourly_alarm)
