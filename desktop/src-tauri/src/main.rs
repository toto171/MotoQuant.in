// MotoQuant Pro desktop entry point.
//
// The Tauri (Rust) side is deliberately tiny: its only responsibility is to
// boot the bundled Python FastAPI sidecar, learn the ephemeral port it bound
// to, and expose that port to the React frontend via a `get_backend_url`
// command. All business logic stays in Python (motoquant.api).
//
// Rationale: the physics engine, 290-bike catalog, 465-part library, and
// calibration pipeline are ~18k lines of mature Python validated to
// K5 10.033s / R1 10.286s / Hayabusa 10.471s. See ADR-0001.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    motoquant_desktop_lib::run();
}
