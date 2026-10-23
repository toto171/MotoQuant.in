//! `np.interp` and `np.searchsorted` with NumPy's exact semantics.
//!
//! Ported from numpy/_core/src/multiarray/compiled_base.c (`arr_interp`,
//! `binary_search_with_guess`, `_linear_search`) and npysort/binsearch.cpp
//! (left-side binary search), NumPy 2.4.6. The physics engine calls
//! `float(np.interp(rpm, xp, fp))` once per torque lookup with a scalar `x`,
//! so the search always starts from guess 0 and the slope is computed inline
//! (NumPy only pre-computes slopes when len(xp) <= len(x), i.e. len(xp) == 1,
//! which takes the dedicated single-point branch).

const LIKELY_IN_CACHE_SIZE: isize = 8;

#[inline]
fn linear_search(key: f64, arr: &[f64], i0: isize) -> isize {
    let len = arr.len() as isize;
    let mut i = i0;
    while i < len && key >= arr[i as usize] {
        i += 1;
    }
    i - 1
}

/// Index `i` with `arr[i] <= key < arr[i+1]`; -1 below range, `len` above.
pub fn binary_search_with_guess(key: f64, arr: &[f64], guess: isize) -> isize {
    let len = arr.len() as isize;
    let mut imin: isize = 0;
    let mut imax: isize = len;
    let a = |i: isize| arr[i as usize];

    if key > a(len - 1) {
        return len;
    } else if key < a(0) {
        return -1;
    }
    if len <= 4 {
        return linear_search(key, arr, 1);
    }
    let mut guess = guess;
    if guess > len - 3 {
        guess = len - 3;
    }
    if guess < 1 {
        guess = 1;
    }
    if key < a(guess) {
        if key < a(guess - 1) {
            imax = guess - 1;
            if guess > LIKELY_IN_CACHE_SIZE && key >= a(guess - LIKELY_IN_CACHE_SIZE) {
                imin = guess - LIKELY_IN_CACHE_SIZE;
            }
        } else {
            return guess - 1;
        }
    } else if key < a(guess + 1) {
        return guess;
    } else if key < a(guess + 2) {
        return guess + 1;
    } else {
        imin = guess + 2;
        if guess < len - LIKELY_IN_CACHE_SIZE - 1 && key < a(guess + LIKELY_IN_CACHE_SIZE) {
            imax = guess + LIKELY_IN_CACHE_SIZE;
        }
    }
    while imin < imax {
        let imid = imin + ((imax - imin) >> 1);
        if key >= a(imid) {
            imin = imid + 1;
        } else {
            imax = imid;
        }
    }
    imin - 1
}

/// `float(np.interp(x, xp, fp))` for a scalar `x` (default left/right fills).
///
/// Panics only on an empty `xp` (NumPy raises ValueError there; the resolver
/// rejects such curves before they reach Rust).
pub fn np_interp(x: f64, xp: &[f64], fp: &[f64]) -> f64 {
    let lenxp = xp.len();
    let lval = fp[0];
    let rval = fp[lenxp - 1];
    if lenxp == 1 {
        let xp_val = xp[0];
        return if x < xp_val {
            lval
        } else if x > xp_val {
            rval
        } else {
            fp[0]
        };
    }
    if x.is_nan() {
        return x;
    }
    let j = binary_search_with_guess(x, xp, 0);
    if j == -1 {
        return lval;
    }
    let lenxp_i = lenxp as isize;
    if j == lenxp_i {
        return rval;
    }
    let j = j as usize;
    if j == lenxp - 1 {
        return fp[j];
    }
    if xp[j] == x {
        return fp[j];
    }
    let slope = (fp[j + 1] - fp[j]) / (xp[j + 1] - xp[j]);
    let mut res = slope * (x - xp[j]) + fp[j];
    if res.is_nan() {
        res = slope * (x - xp[j + 1]) + fp[j + 1];
        if res.is_nan() && fp[j] == fp[j + 1] {
            res = fp[j];
        }
    }
    res
}

/// NumPy's sort-order `DOUBLE_LT` (NaNs sort last).
#[inline]
fn double_lt(a: f64, b: f64) -> bool {
    a < b || (b.is_nan() && !a.is_nan())
}

/// `np.searchsorted(arr, key)` (side='left') for one key: NumPy's bisection
/// with the NaN-aware `DOUBLE_LT` comparator (npysort/binsearch.cpp).
pub fn searchsorted_left(arr: &[f64], key: f64) -> usize {
    let mut min_idx: usize = 0;
    let mut max_idx: usize = arr.len();
    while min_idx < max_idx {
        let mid = min_idx + ((max_idx - min_idx) >> 1);
        if double_lt(arr[mid], key) {
            min_idx = mid + 1;
        } else {
            max_idx = mid;
        }
    }
    min_idx
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn interp_basics() {
        let xp = [1000.0, 2000.0, 3000.0, 4000.0, 5000.0, 6000.0];
        let fp = [10.0, 20.0, 40.0, 35.0, 30.0, 5.0];
        assert_eq!(np_interp(500.0, &xp, &fp), 10.0);
        assert_eq!(np_interp(7000.0, &xp, &fp), 5.0);
        assert_eq!(np_interp(6000.0, &xp, &fp), 5.0);
        assert_eq!(np_interp(3000.0, &xp, &fp), 40.0);
        assert_eq!(np_interp(2500.0, &xp, &fp), 30.0);
        assert!(np_interp(f64::NAN, &xp, &fp).is_nan());
        assert_eq!(np_interp(3.0, &[2.0], &[9.0]), 9.0);
    }

    #[test]
    fn searchsorted_matches_definition() {
        let a = [0.0, 1.0, 1.0, 2.0, 5.0];
        assert_eq!(searchsorted_left(&a, -1.0), 0);
        assert_eq!(searchsorted_left(&a, 1.0), 1);
        assert_eq!(searchsorted_left(&a, 1.5), 3);
        assert_eq!(searchsorted_left(&a, 9.0), 5);
    }
}
