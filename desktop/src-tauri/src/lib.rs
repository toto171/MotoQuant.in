// Library-side Tauri entry point. Keeps `main.rs` thin and makes the core
// logic unit-testable.
//
// HOSTED-ONLY ARCHITECTURE
// ========================
// MotoQuant Pro desktop is a thin, licensed *client* of the hosted API. The
// physics engine, optimizer, surrogate models, and bike/part catalog all live
// server-side and never ship inside this bundle — so the valuable IP is not
// present on the user's machine to be copied. There is NO local Python sidecar
// to spawn; the app simply points the React frontend at the hosted API base
// URL and authenticates against it at runtime.
//
// Security framing (honest): removing the sidecar does NOT make the client
// "uncrackable" — no client is. What it does deliver is that a copied or
// patched client is *worthless* without a valid authenticated, licensed
// session against the operator's server, because all compute happens there.

use std::sync::{Arc, Mutex};
use tauri::{Manager, State};

/// Compile-time default for the hosted API. Overridable at build/dev time via
/// the `MOTOQUANT_API_URL` environment variable (read once at startup).
const DEFAULT_API_URL: &str = "https://motoquant-api.onrender.com";

/// Shared state — the hosted API base URL the React frontend should hit.
/// Resolved once at startup; there is no local process to manage.
#[derive(Default)]
pub struct BackendState {
    pub base_url: Arc<Mutex<Option<String>>>,
}

/// Resolve the hosted API base URL.
/// Order: `MOTOQUANT_API_URL` env override → compile-time `DEFAULT_API_URL`.
/// Trailing slashes are trimmed so the frontend can concatenate `/api/...`.
fn resolve_api_url() -> String {
    let raw = std::env::var("MOTOQUANT_API_URL")
        .ok()
        .filter(|s| !s.trim().is_empty())
        .unwrap_or_else(|| DEFAULT_API_URL.to_string());
    raw.trim().trim_end_matches('/').to_string()
}

/// Return the base URL the React frontend should hit for API calls.
/// This resolves instantly — there is no sidecar to wait for.
#[tauri::command]
fn get_backend_url(state: State<'_, BackendState>) -> Result<String, String> {
    if let Some(url) = state.base_url.lock().unwrap().clone() {
        return Ok(url);
    }
    // Should never happen (setup() populates it), but resolve defensively.
    Ok(resolve_api_url())
}

/// OS keychain service name for credential storage (macOS Keychain /
/// Windows Credential Manager / Linux Secret Service). The frontend stores the
/// auth refresh token here instead of sessionStorage so it never touches
/// plaintext disk. See desktop/src/lib/secureStore.ts (with a sessionStorage
/// fallback when no keychain backend is available, e.g. headless Linux).
const KEYCHAIN_SERVICE: &str = "in.motoquant.desktop";

/// Read a secret from the OS keychain. Returns `None` when the key is absent.
#[tauri::command]
fn keychain_get(key: String) -> Result<Option<String>, String> {
    let entry = keyring::Entry::new(KEYCHAIN_SERVICE, &key).map_err(|e| e.to_string())?;
    match entry.get_password() {
        Ok(v) => Ok(Some(v)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(e) => Err(e.to_string()),
    }
}

/// Write (create or overwrite) a secret in the OS keychain.
#[tauri::command]
fn keychain_set(key: String, value: String) -> Result<(), String> {
    let entry = keyring::Entry::new(KEYCHAIN_SERVICE, &key).map_err(|e| e.to_string())?;
    entry.set_password(&value).map_err(|e| e.to_string())
}

/// Delete a secret from the OS keychain. A missing key is treated as success.
#[tauri::command]
fn keychain_delete(key: String) -> Result<(), String> {
    let entry = keyring::Entry::new(KEYCHAIN_SERVICE, &key).map_err(|e| e.to_string())?;
    match entry.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => Ok(()),
        Err(e) => Err(e.to_string()),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .manage(BackendState::default())
        .invoke_handler(tauri::generate_handler![
            get_backend_url,
            keychain_get,
            keychain_set,
            keychain_delete
        ])
        .setup(|app| {
            let url = resolve_api_url();
            log::info!("MotoQuant API base URL: {url}");
            let state = app.state::<BackendState>();
            *state.base_url.lock().unwrap() = Some(url);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
