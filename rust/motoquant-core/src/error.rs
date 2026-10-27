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
