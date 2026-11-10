//! Typed simulation errors.
//!
//! Each error carries the *Python exception class* the reference engine
//! (motoquant/physics.py) raises for the same input, so the PyO3 front door
//! can re-raise the matching class (`ValueError`, `MemoryError`,
//! `OverflowError`, `ZeroDivisionError`) and callers that catch a specific
//! class keep working whichever engine ran. The wasm ABI reports the kind as a
//! string in the result header (`"kind": "memory"`).

use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ErrorKind {
    /// Python `ValueError` (bad config / bad argument).
    Value,
    /// Python `MemoryError` (the run would store more samples than the
    /// engine's hard cap; Python's `np.zeros` raises `MemoryError` instead).
    Memory,
    /// Python `OverflowError` (`int(inf)` sizing the output arrays).
    Overflow,
    /// Python `ZeroDivisionError` (`max_time / dt` with `dt == 0`).
    ZeroDivision,
}

impl ErrorKind {
    pub fn as_str(self) -> &'static str {
        match self {
            ErrorKind::Value => "value",
            ErrorKind::Memory => "memory",
            ErrorKind::Overflow => "overflow",
            ErrorKind::ZeroDivision => "zero_division",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SimError {
    pub kind: ErrorKind,
    pub msg: String,
}

impl SimError {
    pub fn value(msg: impl Into<String>) -> SimError {
        SimError { kind: ErrorKind::Value, msg: msg.into() }
    }
    pub fn memory(msg: impl Into<String>) -> SimError {
        SimError { kind: ErrorKind::Memory, msg: msg.into() }
    }
    pub fn overflow(msg: impl Into<String>) -> SimError {
        SimError { kind: ErrorKind::Overflow, msg: msg.into() }
    }
    pub fn zero_division(msg: impl Into<String>) -> SimError {
        SimError { kind: ErrorKind::ZeroDivision, msg: msg.into() }
    }
}

impl fmt::Display for SimError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.msg)
    }
}

impl std::error::Error for SimError {}

impl From<String> for SimError {
    fn from(msg: String) -> SimError {
        SimError::value(msg)
    }
}

impl From<&str> for SimError {
    fn from(msg: &str) -> SimError {
        SimError::value(msg)
    }
}

/// Python's `repr(float)` — so an error message built from a float reads
/// byte-for-byte like the Python reference's (`f"{x!r}"`): shortest
/// round-trip digits, positional for 1e-4 <= |x| < 1e16 (always with a
/// fractional part, `402.0`), scientific otherwise with a signed, >= 2-digit
/// exponent (`1e-05`, `1.5e+16`), and `nan` / `inf` / `-inf`.
pub fn py_float_repr(x: f64) -> String {
    if x.is_nan() {
        return "nan".to_string();
    }
    if x.is_infinite() {
        return if x > 0.0 { "inf".to_string() } else { "-inf".to_string() };
    }
    let sign = if x.is_sign_negative() { "-" } else { "" };
    if x == 0.0 {
        return format!("{sign}0.0");
    }
    // `{:e}` prints the shortest round-trip digits: "-4.02336e2", "1e-5".
    let s = format!("{:e}", x.abs());
    let (mant, exp) = s.split_once('e').expect("LowerExp always has an exponent");
    let exp: i32 = exp.parse().expect("integer exponent");
    let digits: String = mant.chars().filter(|c| c.is_ascii_digit()).collect();
    if !(-4..16).contains(&exp) {
        let m = if digits.len() > 1 {
            format!("{}.{}", &digits[..1], &digits[1..])
        } else {
            digits
        };
        let es = if exp < 0 { format!("-{:02}", -exp) } else { format!("+{exp:02}") };
        format!("{sign}{m}e{es}")
    } else if exp >= 0 {
        let int_len = exp as usize + 1;
        if digits.len() > int_len {
            format!("{sign}{}.{}", &digits[..int_len], &digits[int_len..])
        } else {
            format!("{sign}{digits}{}.0", "0".repeat(int_len - digits.len()))
        }
    } else {
        format!("{sign}0.{}{digits}", "0".repeat((-exp - 1) as usize))
    }
}

#[cfg(test)]
mod tests {
    use super::py_float_repr;

    #[test]
    fn matches_python_repr() {
        for (x, want) in [
            (402.336, "402.336"),
            (0.3048, "0.3048"),
            (0.0, "0.0"),
            (-0.0, "-0.0"),
            (-1.0, "-1.0"),
            (1.0, "1.0"),
            (100.0, "100.0"),
            (0.0001, "0.0001"),
            (0.00001, "1e-05"),
            (1.5e-7, "1.5e-07"),
            (1e15, "1000000000000000.0"),
            (1e16, "1e+16"),
            (1.2345e100, "1.2345e+100"),
            (123456.789, "123456.789"),
            (0.1 + 0.2, "0.30000000000000004"),
            (f64::NAN, "nan"),
            (f64::INFINITY, "inf"),
            (f64::NEG_INFINITY, "-inf"),
        ] {
            assert_eq!(py_float_repr(x), want, "{x:e}");
        }
    }
}
