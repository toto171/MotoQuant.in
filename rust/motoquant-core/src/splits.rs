//! `SimResult.extract_splits()` (physics.py) — split times/speeds by linear
//! interpolation on the position channel, NumPy `searchsorted` semantics.

use crate::interp::searchsorted_left;

pub const SIXTY_FOOT_M: f64 = 18.288;
pub const THREE30_FT_M: f64 = 100.584;
pub const EIGHTH_MILE_M: f64 = 201.168;
pub const THOUSAND_FT_M: f64 = 304.8;
pub const QUARTER_MILE_M: f64 = 402.336;

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
}

fn split_at(x: &[f64], t: &[f64], v: &[f64], dist: f64) -> Option<(f64, f64)> {
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

pub fn extract_splits(t: &[f64], x: &[f64], v: &[f64]) -> Splits {
    let mut s = Splits::default();
    if let Some(&xl) = x.last() {
        s.max_distance_m = xl;
    }
    if let Some(&tl) = t.last() {
        s.elapsed_time_s = tl;
    }
    if let Some((a, b)) = split_at(x, t, v, SIXTY_FOOT_M) {
        s.time_60ft = a;
        s.speed_60ft = b;
    }
    if let Some((a, b)) = split_at(x, t, v, THREE30_FT_M) {
        s.time_330ft = a;
        s.speed_330ft = b;
    }
    if let Some((a, b)) = split_at(x, t, v, EIGHTH_MILE_M) {
        s.time_eighth = a;
        s.speed_eighth = b;
    }
    if let Some((a, b)) = split_at(x, t, v, THOUSAND_FT_M) {
        s.time_1000ft = a;
        s.speed_1000ft = b;
    }
    if let Some((a, b)) = split_at(x, t, v, QUARTER_MILE_M) {
        s.time_quarter = a;
        s.speed_quarter = b;
    }
    s.finished_quarter = s.time_quarter > 0.0;
    s
}
