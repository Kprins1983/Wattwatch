"""Bounded, local, deterministic hourly anomaly detector; no HA dependencies."""
from __future__ import annotations
from dataclasses import dataclass, field
from math import isfinite
from statistics import median

HOUR = 3600
DAY = 86400
RETENTION = 21 * DAY
LEARNING = 7 * DAY
MIN_HOURS = 120
SENSITIVITY_MARGINS = {"normal": 1.0, "wide": 1.5, "sensitive": 0.5}


def watts(value, unit):
    """Reject missing, negative (export), non-power and nonfinite readings."""
    try:
        number = float(value) * {"W": 1, "kW": 1000, "mW": .001}[unit]
    except (TypeError, ValueError, KeyError, OverflowError):
        return None
    return number if isfinite(number) and number >= 0 else None


def quantile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


@dataclass
class Profile:
    """Store only completed hours; do not bridge outages or restart gaps."""
    history: list = field(default_factory=list)
    short_history: list = field(default_factory=list)
    short_samples: list = field(default_factory=list)
    short_blocks: list = field(default_factory=list)
    short_alert: dict = field(default_factory=dict)
    last_alert: float = 0
    first_seen: float = 0
    last_evaluation: dict = field(default_factory=dict)
    # All fields below are intentionally transient across restart.
    previous_time: float | None = None
    previous_watts: float | None = None
    bucket: int | None = None
    bucket_hour: int = 0
    bucket_day: str = ""
    integral: float = 0
    coverage: float = 0
    candidate: str = ""
    consecutive: int = 0
    anomaly: bool = False
    available: bool = False
    current_watts: float | None = None

    def dump(self):
        return {"history": self.history, "short_history": self.short_history, "last_alert": self.last_alert,
                "first_seen": self.first_seen, "last_evaluation": self.last_evaluation}

    @classmethod
    def load(cls, data):
        return cls(history=data.get("history", []), short_history=data.get("short_history", []),
                   first_seen=data.get("first_seen", 0),
                   last_alert=data.get("last_alert", 0),
                   last_evaluation=data.get("last_evaluation", {}))

    def progress(self, now):
        if not self.history:
            return 0
        duration = max(0, now - self.first_seen) / LEARNING
        return round(100 * min(1, duration, len(self.history) / MIN_HOURS))

    def reset_continuity(self):
        self.candidate = ""
        self.consecutive = 0
        self.anomaly = False

    def evaluate(self, record, sensitivity="normal"):
        """Use earlier days at a similar local hour; never train on this record."""
        end = record["start"] + HOUR
        if end - self.first_seen < LEARNING or len(self.history) < MIN_HOURS:
            self.reset_continuity()
            return {"status": "learning"}
        refs = [r for r in self.history
                if r["day"] != record["day"]
                and min(abs(r["hour"] - record["hour"]),
                        24 - abs(r["hour"] - record["hour"])) <= 1]
        if len({r["day"] for r in refs}) < 5:
            self.reset_continuity()
            return {"status": "learning"}
        values = [r["watts"] for r in refs]
        center = median(values)
        mad = median(abs(v - center) for v in values)
        margin = max(20, center * .5, 4 * mad) * SENSITIVITY_MARGINS[sensitivity]
        lower = max(0, quantile(values, .05) - margin)
        upper = quantile(values, .95) + margin
        direction = ("high" if record["watts"] > upper else
                     "low" if record["watts"] < lower else "")
        if direction:
            self.consecutive = self.consecutive + 1 if self.candidate == direction else 1
            self.candidate = direction
            self.anomaly = self.consecutive >= 2
        else:
            self.reset_continuity()
        return {"status": "anomaly" if self.anomaly else "normal",
                "direction": direction, "average_watts": round(record["watts"], 2),
                "expected_watts": round(center, 2), "lower_watts": round(lower, 2),
                "upper_watts": round(upper, 2), "reference_hours": len(refs),
                "evaluated_at": end}

    def short_check(self, now, value, local_hour, local_day, sensitivity):
        """Evaluate recent continuous ten-minute blocks against earlier windows."""
        samples = self.short_samples
        if value is None or not samples or not 0 < now - samples[-1][0] <= 90:
            samples.clear()
            self.short_blocks.clear()
            self.short_alert = {}
        if value is None:
            return None
        samples.append((now, value))
        duration = now - samples[0][0]
        if duration < 600:
            return None

        mean = sum(power * (end - start) for (start, power), (end, _)
                   in zip(samples, samples[1:])) / duration
        samples[:] = [(now, value)]
        blocks = self.short_blocks
        blocks.append(mean)
        del blocks[:-6]
        self.short_history = [r for r in self.short_history if r[0] >= now - RETENTION]
        # Each stored row contains the end time, local hour/day and means
        # for the 20, 30 and 60 minute windows available at that instant.
        means = [sum(blocks[-n:]) / n if len(blocks) >= n else None for n in (2, 3, 6)]
        ready = self.progress(now) == 100
        had_alert = bool(self.short_alert)
        self.short_alert = {}
        for index, size in enumerate((2, 3, 6)):
            average = means[index]
            if not ready or average is None:
                continue
            refs = [r for r in self.short_history if r[2] != local_day
                    and (r[1] - local_hour) % 24 in (0, 1, 23) and r[3 + index] is not None]
            if len({r[2] for r in refs}) < 5:
                continue
            values = [r[3 + index] for r in refs]
            center = median(values)
            margin = max(2, center * .25) * SENSITIVITY_MARGINS[sensitivity]
            lower, upper = max(0, min(values) - margin), max(values) + margin
            recent = blocks[-size:]
            if average > upper and min(recent) > center + margin:
                direction = "high"
            elif average < lower and max(recent) < center - margin:
                direction = "low"
            else:
                continue
            self.short_alert = dict(status="anomaly", direction=direction,
                                    window_minutes=size * 10, average_watts=round(average, 2),
                                    expected_watts=round(center, 2), lower_watts=round(lower, 2),
                                    upper_watts=round(upper, 2), evaluated_at=now)
            return self.short_alert
        if not self.anomaly and any(v is not None for v in means):
            self.short_history.append([now, local_hour, local_day, *means])
        return {"status": "normal"} if had_alert else None

    def sample(self, now, value, local_hour, local_day, sensitivity="normal"):
        """One sample/minute; time-weighted hold with a 90s maximum gap."""
        short_result = self.short_check(now, value, local_hour, local_day, sensitivity)
        self.available = value is not None
        self.current_watts = value
        if not self.first_seen:
            self.first_seen = now
        self.history = [r for r in self.history if r["start"] >= now - RETENTION]
        current_bucket = int(now // HOUR)
        result = None
        if self.bucket is None:
            self.bucket = current_bucket
            self.bucket_hour, self.bucket_day = local_hour, local_day
        # Accumulate only continuous, valid observations. At a boundary, the
        # previous value contributes only up to that boundary.
        elapsed = now - self.previous_time if self.previous_time is not None else 0
        continuous = 0 < elapsed <= 90 and self.previous_watts is not None and value is not None
        if continuous:
            seconds = max(0, min(now, (self.bucket + 1) * HOUR) - self.previous_time)
            self.integral += self.previous_watts * seconds
            self.coverage += seconds
        elif self.previous_time is not None:
            self.reset_continuity()
        if current_bucket != self.bucket:
            if self.coverage >= 2700 and current_bucket == self.bucket + 1:
                record = {"start": self.bucket * HOUR, "hour": self.bucket_hour,
                          "day": self.bucket_day, "watts": round(self.integral / self.coverage, 3)}
                result = self.evaluate(record, sensitivity)
                self.last_evaluation = result
                # Quarantine even unconfirmed outliers to prevent learning away
                # a persistent fault. A deliberate new regime needs a reset.
                if not result.get("direction"):
                    self.history.append(record)
            else:
                self.reset_continuity()
                self.last_evaluation = {"status": "insufficient_data"}
            self.bucket = current_bucket
            self.bucket_hour, self.bucket_day = local_hour, local_day
            self.integral = self.coverage = 0
            if continuous:
                seconds = max(0, now - current_bucket * HOUR)
                self.integral = self.previous_watts * seconds
                self.coverage = seconds
        self.previous_time, self.previous_watts = now, value
        if self.anomaly:
            return result
        if self.short_alert:
            return short_result if short_result else None
        return result or short_result

    def status(self, now):
        if not self.available:
            return "unavailable"
        if self.anomaly or self.short_alert:
            return "anomaly"
        if self.progress(now) < 100 or self.last_evaluation.get("status") == "learning":
            return "learning"
        if self.last_evaluation.get("status") == "insufficient_data":
            return "insufficient_data"
        return "normal"
