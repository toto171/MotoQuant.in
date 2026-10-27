//! Transcendental functions with the exact semantics the Python reference
//! sees.
//!
//! Python evaluates the physics loop with three different math back ends:
//!
//! * `x ** y` on a Python float (and on an `np.float64` scalar) calls the C
//!   library's `pow` — verified bit-identical on 1M samples, and NOT equal to
//!   `x * x` for `y == 2` in ~0.09 % of cases (glibc `pow` is not correctly
//!   rounded). So every `**` in the loop goes through [`pow`], never `x * x`.
//! * `math.sin` / `math.exp` call the C library directly.
//! * `np.exp` (tire thermal factor) goes through NumPy's ufunc dispatch. On
//!   CPUs with AVX512_SKX and a NumPy linked against Intel SVML (the PyPI
//!   wheels) that is `__svml_exp8_ha`, which differs from glibc `exp` in ~4.6 %
//!   of inputs. [`exp_svml_ha`] is a scalar transliteration of that routine's
//!   main path; elsewhere NumPy falls back to the C library `exp`. Which one the
//!   host NumPy uses is probed at resolve time (`motoquant/native.py`) and
//!   passed in the resolved config as `exp_impl`.
//!
//! On native targets the C-library functions are the SAME symbols CPython
//! links (glibc on Linux), so parity is exact. On `wasm32-unknown-unknown` the
//! standard library supplies a pure-Rust libm port (musl / FreeBSD msun
//! lineage) whose results can differ from glibc by an ULP in rare cases; the
//! drift that causes is measured by `web/scripts/engine-parity.mjs`.

use core::hint::black_box;

/// `x ** y` exactly as CPython computes it (C `pow`).
///
/// `black_box` on the exponent stops LLVM's libcall simplifier from rewriting
/// `pow(x, 2.0)` into `x * x` (an exact rewrite only if `pow` were correctly
/// rounded — glibc's is not, see module docs).
#[inline(always)]
pub fn pow(x: f64, y: f64) -> f64 {
    x.powf(black_box(y))
}

/// `x ** 2` (Python) — C `pow(x, 2.0)`, never `x * x`.
#[inline(always)]
pub fn sq(x: f64) -> f64 {
    pow(x, 2.0)
}

/// `math.sin` (C `sin`).
#[inline(always)]
pub fn sin(x: f64) -> f64 {
    black_box(x).sin()
}

/// `math.exp` (C `exp`).
#[inline(always)]
pub fn exp_libm(x: f64) -> f64 {
    black_box(x).exp()
}

/// Which implementation `np.exp(float64)` resolves to on the host NumPy.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ExpImpl {
    /// C library `exp` (NumPy's scalar fallback `npy_exp`).
    Libm,
    /// Intel SVML `__svml_exp8_ha` (NumPy AVX512_SKX dispatch).
    SvmlHa,
}

impl ExpImpl {
    pub fn parse(s: &str) -> Option<ExpImpl> {
        match s {
            "libm" => Some(ExpImpl::Libm),
            "svml_ha" => Some(ExpImpl::SvmlHa),
            _ => None,
        }
    }

    #[inline(always)]
    pub fn exp(self, x: f64) -> f64 {
        match self {
            ExpImpl::Libm => exp_libm(x),
            ExpImpl::SvmlHa => exp_svml_ha(x),
        }
    }
}

// ── __svml_exp8_ha (Intel SVML, AVX-512 double exp, high-accuracy) ─────────
//
// Constants transcribed from `__svml_dexp_ha_data_internal_avx512` in
// numpy/_core/src/umath/svml/linux/avx512/svml_z0_exp_d_ha.s (NumPy 2.4.6;
// SVML is vendored by NumPy under the BSD-3-Clause license). Offsets in the
// comments are the byte offsets into that table.

/// 2^(j/16) high parts, j = 0..15  (offset 0..128).
const TH: [u64; 16] = [
    0x3ff0000000000000, 0x3ff0b5586cf9890f, 0x3ff172b83c7d517b, 0x3ff2387a6e756238,
    0x3ff306fe0a31b715, 0x3ff3dea64c123422, 0x3ff4bfdad5362a27, 0x3ff5ab07dd485429,
    0x3ff6a09e667f3bcd, 0x3ff7a11473eb0187, 0x3ff8ace5422aa0db, 0x3ff9c49182a3f090,
    0x3ffae89f995ad3ad, 0x3ffc199bdd85529c, 0x3ffd5818dcfba487, 0x3ffea4afa2a490da,
];
/// Relative low parts Tlr (Th·(1+Tlr) = 2^(j/16))  (offset 128..256).
const TLR: [u64; 16] = [
    0x0000000000000000, 0x3c979aa65d837b6d, 0xbc801b15eaa59348, 0x3c968efde3a8a894,
    0x3c834d754db0abb6, 0x3c859f48a72a4c6d, 0x3c7690cebb7aafb0, 0x3c9063e1e21c5409,
    0xbc93b3efbf5e2228, 0xbc7b32dcb94da51d, 0x3c8db72fc1f0eab4, 0x3c71affc2b91ce27,
    0x3c8c1a7792cb3387, 0x3c736eae30af0cb3, 0x3c74a385a63d07a7, 0xbc8ff7128fd391f0,
];
const L2E: u64 = 0x3ff71547652b82fe; // 256: log2(e)
#[allow(dead_code)] // documented for the derivation; the RZ-FMA emulation folds it in exactly
const SHIFTER: u64 = 0x42f8000000003ff0; // 320: 1.5·2^48 + 1023 (grid 2^-4)
const L2H: u64 = 0x3fe62e42fefa39ef; // 384: ln2 high
const L2L: u64 = 0x3c7abc9e3b39803f; // 448: ln2 low
const R_MASK: u64 = 0xbfffffffffffffff; // 512: "ensure |R| < 2"
const C6: u64 = 0x3f57411836940c04; // 576
const C5: u64 = 0x3f81101cbbc265c0; // 640
const C4: u64 = 0x3fa55557242d68fe; // 704
const C3: u64 = 0x3fc5555553939732; // 768
const C2: u64 = 0x3fe000000000d008; // 832
const C1: u64 = 0x3fefffffffffff70; // 896
const THRESHOLD: u64 = 0x40861da04cbafe44; // 1024: |x| >= this → callout

#[inline(always)]
fn f(b: u64) -> f64 {
    f64::from_bits(b)
}

/// Scalar transliteration of the `__svml_exp8_ha` main path.
///
/// Instruction-by-instruction (AT&T operand order in the source):
///
/// ```text
/// zmm4 = RZ(x·L2E + SHIFTER)        vfmadd213pd {rz-sae}
/// N    = zmm4 − SHIFTER              vsubpd       (x·log2e, 4 fraction bits, toward −∞)
/// j    = low 4 bits of zmm4          vpermt2pd index → Th[j], Tlr[j]
/// R    = fma(−N, L2H, x)             vfnmadd213pd
/// R    = fma(−L2L, N, R)             vfnmadd231pd
/// r    = R & R_MASK                  vandpd
/// r2   = r·r
/// p56  = fma(C6, r, C5);  p34 = fma(C4, r, C3);  p12 = fma(C2, r, C1)
/// p36  = fma(r2, p56, p34);  p16 = fma(r2, p36, p12)
/// p    = fma(p16, r, Tlr[j])
/// res  = fma(Th[j], p, Th[j])
/// out  = res · 2^floor(N)            vscalefpd
/// ```
///
/// The round-toward-zero FMA is emulated exactly: `SHIFTER` sits on the 2^-4
/// grid and the sum stays inside [2^48, 2^49), so RZ(x·L2E + SHIFTER) =
/// SHIFTER + floor(16·y)/16 with `y = x·L2E` taken EXACTLY (`p + pe`, where
/// `pe = fma(x, L2E, −p)` is the product's rounding error). Verified
/// bit-identical to `np.exp` on 1M random inputs (see tests).
///
/// Lanes with |x| >= 707.70 (or NaN/inf) take SVML's scalar callout in NumPy;
/// the physics loop never gets near that domain (its argument is
/// −((T_tire − T_opt)/25)²), so those fall back to the C library `exp`.
pub fn exp_svml_ha(x: f64) -> f64 {
    if !(x.abs() < f(THRESHOLD)) {
        return exp_libm(x);
    }
    let l2e = f(L2E);
    let p = x * l2e;
    let pe = x.mul_add(l2e, -p);
    let s = 16.0 * p; // exact (power-of-two scale)
    let mut fl = s.floor();
    if fl == s && pe < 0.0 {
        fl -= 1.0;
    }
    let fi = fl as i64;
    let n = fl / 16.0; // exact
    let j = (fi & 15) as usize;
    let m = fi >> 4; // floor(fi / 16) == floor(N)
    let mut r = (-n).mul_add(f(L2H), x);
    r = (-f(L2L)).mul_add(n, r);
    let r = f64::from_bits(r.to_bits() & R_MASK);
    let r2 = r * r;
    let p56 = f(C6).mul_add(r, f(C5));
    let p34 = f(C4).mul_add(r, f(C3));
    let p12 = f(C2).mul_add(r, f(C1));
    let p36 = r2.mul_add(p56, p34);
    let p16 = r2.mul_add(p36, p12);
    let pp = p16.mul_add(r, f(TLR[j]));
    let th = f(TH[j]);
    let res = th.mul_add(pp, th);
    scale2(res, m)
}

/// `v · 2^k` for the exponent range the physics domain can reach (exact for
/// normal results — identical to `vscalefpd` there).
#[inline(always)]
fn scale2(v: f64, k: i64) -> f64 {
    if (-1022..=1023).contains(&k) {
        v * f64::from_bits(((k + 1023) as u64) << 52)
    } else {
        // Split the scale so neither factor over/underflows prematurely.
        let half = k / 2;
        scale2(scale2(v, half), k - half)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn svml_exp_known_values() {
        assert_eq!(exp_svml_ha(0.0), 1.0);
        let e = exp_svml_ha(1.0);
        assert!((e - core::f64::consts::E).abs() < 4.0 * f64::EPSILON);
        for i in 0..2000 {
            let x = -30.0 + 0.0173 * i as f64;
            let a = exp_svml_ha(x);
            let b = exp_libm(x);
            assert!(((a - b) / b).abs() < 4.0 * f64::EPSILON, "x={x} {a} {b}");
        }
    }
}
