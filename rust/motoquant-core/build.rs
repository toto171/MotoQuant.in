//! Build script: stamp the crate with a fingerprint of its own sources.
//!
//! `SOURCE_FINGERPRINT` (FNV-1a 64 over `Cargo.toml`, every `src/**/*.rs`
//! and the workspace `Cargo.lock`, in sorted path order) is compiled into the
//! PyO3 module (`motoquant_core.SOURCE_FINGERPRINT`) and the wasm build
//! (`source_fingerprint_hi/lo` exports). `motoquant/native.py` recomputes the
//! same hash from the checkout, so a binary built from older sources is
//! reported as STALE instead of being trusted (docs/RUST_CORE.md).
//!
//! The scheme must stay identical to `native._source_fingerprint()`:
//! for each file, feed `relative/posix/path`, `\0`, the raw bytes, `\0`.

use std::fs;
use std::path::{Path, PathBuf};

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

fn fnv1a(mut h: u64, bytes: &[u8]) -> u64 {
    for &b in bytes {
        h ^= u64::from(b);
        h = h.wrapping_mul(FNV_PRIME);
    }
    h
}

fn rs_files(dir: &Path, rel: &str, out: &mut Vec<(String, PathBuf)>) {
    let mut entries: Vec<_> = fs::read_dir(dir)
        .unwrap_or_else(|e| panic!("read_dir {}: {e}", dir.display()))
        .map(|e| e.expect("dir entry").path())
        .collect();
    entries.sort();
    for p in entries {
        let name = p.file_name().unwrap().to_string_lossy().into_owned();
        let r = format!("{rel}/{name}");
        if p.is_dir() {
            rs_files(&p, &r, out);
        } else if name.ends_with(".rs") {
            out.push((r, p));
        }
    }
}

fn main() {
    let crate_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let mut files: Vec<(String, PathBuf)> = vec![("Cargo.toml".into(), crate_dir.join("Cargo.toml"))];
    rs_files(&crate_dir.join("src"), "src", &mut files);
    let lock = crate_dir.join("..").join("Cargo.lock");
    if lock.exists() {
        files.push(("../Cargo.lock".into(), lock.clone()));
    }
    files.sort_by(|a, b| a.0.cmp(&b.0));

    let mut h = FNV_OFFSET;
    for (rel, path) in &files {
        let data = fs::read(path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
        h = fnv1a(h, rel.as_bytes());
        h = fnv1a(h, &[0]);
        h = fnv1a(h, &data);
        h = fnv1a(h, &[0]);
    }

    let out = PathBuf::from(std::env::var("OUT_DIR").unwrap()).join("fingerprint.rs");
    fs::write(
        &out,
        format!("/// FNV-1a 64 of this crate's sources at build time (see build.rs).\npub const SOURCE_FINGERPRINT: u64 = {h:#018x};\n"),
    )
    .expect("write fingerprint.rs");

    println!("cargo:rerun-if-changed=Cargo.toml");
    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=../Cargo.lock");
    println!("cargo:rerun-if-changed=build.rs");
}
