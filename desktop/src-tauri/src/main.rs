// MotoQuant Pro desktop entry point.
//
// HOSTED-ONLY: the Tauri (Rust) side is deliberately tiny. Its only job is to
// resolve the hosted API base URL and expose it to the React frontend via the
// `get_backend_url` command. There is NO bundled physics engine, catalog, or
// Python sidecar — all compute lives behind the operator's authenticated,
// licensed API. The app is a thin client; a copied client is useless without a
// valid licensed session against the server. See desktop/SECURITY.md and ADR-0001.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    motoquant_desktop_lib::run();
}
