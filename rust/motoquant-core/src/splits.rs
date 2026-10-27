//! `SimResult.extract_splits()` (physics.py) — split times/speeds by linear
//! interpolation on the position channel, NumPy `searchsorted` semantics.
//!
//! 2026-10 epoch: splits are timed from the start beam, which the bike
//! clears after `rollout_m` of travel from rest:
//! `time_D = t(x = rollout_m + D) - t(x = rollout_m)`, `speed_D = v(x =
//! rollout_m + D)`; `max_distance_m` is measured past the beam.

use crate::interp::searchsorted_left;

pub const SIXTY_FOOT_M: f64 = 18.288;
pub const THREE30_FT_M: f64 = 100.584;
pub const EIGHTH_MILE_M: f64 = 201.168;
pub const THOUSAND_FT_M: f64 = 304.8;
pub const QUARTER_MILE_M: f64 = 402.336;
/// constants.ROLLOUT_M — 1 ft drag-strip rollout (2026-10 physics epoch).
pub const ROLLOUT_M: f64 = 0.3048;

#[derive(Debug, Clone, Default, serde::Serialize)]
pub struct Splits {
    pub time_60ft: f64,
    pub speed_60ft: f64,
    pub time_330ft: f64,
    pub speed_330ft: f64,
    pub time_eighth: f64,
    pub speed_eighth: f64,
    pub time_1000ft: f64,
    pub speed_1000ft: f64,
    pub time_quarter: f64,
    pub speed_quarter: f64,
    pub finished_quarter: bool,
    pub max_distance_m: f64,
    pub elapsed_time_s: f64,
    /// The rollout the splits were timed with (`SimResult.rollout_m`).
    pub rollout_m: f64,
}

/// `SimResult.time_speed_at(dist)` — (t, v) at ABSOLUTE position `dist`.
fn time_speed_at(x: &[f64], t: &[f64], v: &[f64], dist: f64) -> Option<(f64, f64)> {
    let idx = searchsorted_left(x, dist);
    if idx < t.len() {
        if idx > 0 && x[idx] != x[idx - 1] {
            let frac = (dist - x[idx - 1]) / (x[idx] - x[idx - 1]);
            Some((
                t[idx - 1] + frac * (t[idx] - t[idx - 1]),
                v[idx - 1] + frac * (v[idx] - v[idx - 1]),
            ))
        } else {
            Some((t[idx], v[idx]))
        }
    } else {
        None
    }
}

/// `SimResult.split_at(dist)` — (time from the start beam, speed) after
/// `dist` metres of TIMED distance, i.e. at absolute `rollout_m + dist`.
fn split_at(x: &[f64], t: &[f64], v: &[f64], rollout_m: f64, dist: f64) -> Option<(f64, f64)> {
    let mut t0 = 0.0;
    if rollout_m > 0.0 {
        t0 = time_speed_at(x, t, v, rollout_m)?.0;
    }
    let (ta, va) = time_speed_at(x, t, v, rollout_m + dist)?;
    Some((ta - t0, va))
}

/// `SimResult.extract_splits()` with `SimResult.rollout_m = rollout_m`.
pub fn extract_splits(t: &[f64], x: &[f64], v: &[f64], rollout_m: f64) -> Splits {
    let mut s = Splits {
        rollout_m,
        ..Splits::default()
    };
    if let Some(&xl) = x.last() {
        // `max(0.0, float(self.x[-1]) - self.rollout_m)`
        let d = xl - rollout_m;
        s.max_distance_m = if d > 0.0 { d } else { 0.0 };
    }
    if let Some(&tl) = t.last() {
        s.elapsed_time_s = tl;
    }
    if let Some((a, b)) = split_at(x, t, v, rollout_m, SIXTY_FOOT_M) {
        s.time_60ft = a;
        s.speed_60ft = b;
    }
    if let Some((a, b)) = split_at(x, t, v, rollout_m, THREE30_FT_M) {
        s.time_330ft = a;
        s.speed_330ft = b;
    }
    if let Some((a, b)) = split_at(x, t, v, rollout_m, EIGHTH_MILE_M) {
        s.time_eighth = a;
        s.speed_eighth = b;
    }
    if let Some((a, b)) = split_at(x, t, v, rollout_m, THOUSAND_FT_M) {
        s.time_1000ft = a;
        s.speed_1000ft = b;
    }
    if let Some((a, b)) = split_at(x, t, v, rollout_m, QUARTER_MILE_M) {
        s.time_quarter = a;
        s.speed_quarter = b;
    }
    s.finished_quarter = s.time_quarter > 0.0;
    s
}
