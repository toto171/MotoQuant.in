// Library-side Tauri entry point. Keeps `main.rs` thin and makes the core
// logic unit-testable.

use anyhow::{Context, Result};
use std::{
    net::TcpListener,
    process::Stdio,
    sync::{Arc, Mutex},
};
use tauri::{Manager, State};
use tokio::{
    io::{AsyncBufReadExt, BufReader},
    process::{Child, Command},
    sync::oneshot,
};

/// Shared state — the Python sidecar's base URL (e.g. "http://127.0.0.1:43217").
#[derive(Default)]
pub struct BackendState {
    pub base_url: Arc<Mutex<Option<String>>>,
    pub child: Arc<Mutex<Option<Child>>>,
}

/// Return the base URL the React frontend should hit for API calls.
/// Waits up to 8 s for the sidecar to come up.
#[tauri::command]
async fn get_backend_url(state: State<'_, BackendState>) -> Result<String, String> {
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(8);
    loop {
        if let Some(url) = state.base_url.lock().unwrap().clone() {
            return Ok(url);
        }
        if std::time::Instant::now() > deadline {
            return Err("Python sidecar did not start within 8 s".to_string());
        }
        tokio::time::sleep(std::time::Duration::from_millis(100)).await;
    }
}

/// Pick a free ephemeral port. We do this Rust-side so that we can pass it
/// to the Python subprocess as an argument, avoiding any handshake protocol
/// over stdout.
fn pick_free_port() -> Result<u16> {
    let listener = TcpListener::bind("127.0.0.1:0").context("bind ephemeral")?;
    let port = listener.local_addr()?.port();
    drop(listener);
    Ok(port)
}

/// Spawn the Python sidecar (PyInstaller onefile binary shipped in the
/// bundle's `bin/` folder). In dev we instead expect the user to run
/// `uvicorn motoquant.api:app --port $PORT` manually — see README.
async fn spawn_sidecar(port: u16) -> Result<Child> {
    // In a production bundle Tauri resolves `externalBin` paths to absolute
    // paths via `resource_dir`; we use relative here for the dev-path and
    // assume `target/debug/motoquant-backend` is on PATH.
    let bin_name = if cfg!(windows) {
        "motoquant-backend.exe"
    } else {
        "motoquant-backend"
    };

    log::info!("Spawning {bin_name} on port {port}");

    let mut cmd = Command::new(bin_name);
    cmd.args([
        "--host",
        "127.0.0.1",
        "--port",
        &port.to_string(),
        "--log-level",
        "info",
    ])
    .stdout(Stdio::piped())
    .stderr(Stdio::piped())
    .kill_on_drop(true);

    let mut child = cmd.spawn().context("spawn python sidecar")?;
    let stderr = child.stderr.take().context("stderr pipe")?;
    let stdout = child.stdout.take().context("stdout pipe")?;

    // Pipe backend stderr/stdout to Rust log for debugging.
    tokio::spawn(async move {
        let mut reader = BufReader::new(stderr).lines();
        while let Ok(Some(line)) = reader.next_line().await {
            log::info!("[backend] {line}");
        }
    });
    tokio::spawn(async move {
        let mut reader = BufReader::new(stdout).lines();
        while let Ok(Some(line)) = reader.next_line().await {
            log::debug!("[backend] {line}");
        }
    });

    Ok(child)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .manage(BackendState::default())
        .invoke_handler(tauri::generate_handler![get_backend_url])
        .setup(|app| {
            let state = app.state::<BackendState>();
            let base_url = state.base_url.clone();
            let child_slot = state.child.clone();

            // Dev mode: if VITE has set TAURI_DEV_BACKEND_URL we skip
            // spawning and trust whatever the developer has running.
            if let Ok(dev_url) = std::env::var("MOTOQUANT_DEV_BACKEND_URL") {
                log::info!("Using dev backend: {dev_url}");
                *base_url.lock().unwrap() = Some(dev_url);
                return Ok(());
            }

            let (ready_tx, _ready_rx) = oneshot::channel::<()>();

            tauri::async_runtime::spawn(async move {
                match async {
                    let port = pick_free_port()?;
                    let child = spawn_sidecar(port).await?;
                    *child_slot.lock().unwrap() = Some(child);
                    *base_url.lock().unwrap() = Some(format!("http://127.0.0.1:{port}"));
                    let _ = ready_tx.send(());
                    Ok::<_, anyhow::Error>(())
                }
                .await
                {
                    Ok(_) => log::info!("Sidecar ready"),
                    Err(e) => log::error!("Sidecar boot failed: {e:#}"),
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
