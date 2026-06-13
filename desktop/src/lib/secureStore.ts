// Secure storage for the auth refresh token.
// =================================================================
// Prefers the OS keychain (macOS Keychain / Windows Credential Manager /
// Linux Secret Service) exposed by the Rust side as the `keychain_*` Tauri
// commands. Falls back to `sessionStorage` when NOT running under Tauri
// (dev / browser) or when the keychain is unavailable at runtime (e.g. a
// headless Linux box with no Secret Service provider) so the session never
// hard-fails. The refresh token therefore never touches plaintext disk in the
// packaged app; sessionStorage is only the dev/degraded path and is cleared
// on app close.

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function invokeCmd<T>(
  cmd: string,
  args?: Record<string, unknown>,
): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<T>(cmd, args);
}

function ssGet(key: string): string | null {
  try {
    return sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

function ssSet(key: string, value: string | null): void {
  try {
    if (value) sessionStorage.setItem(key, value);
    else sessionStorage.removeItem(key);
  } catch {
    /* sessionStorage unavailable — degrade to in-memory-only session */
  }
}

/** Read a secret. Keychain first under Tauri, else sessionStorage. */
export async function getSecret(key: string): Promise<string | null> {
  if (isTauriRuntime()) {
    try {
      const v = await invokeCmd<string | null>("keychain_get", { key });
      return v ?? null;
    } catch (err) {
      console.warn(
        "[secureStore] keychain_get failed; falling back to sessionStorage:",
        err,
      );
    }
  }
  return ssGet(key);
}

/** Write (value) or clear (null) a secret. Keychain first under Tauri. */
export async function setSecret(key: string, value: string | null): Promise<void> {
  if (isTauriRuntime()) {
    try {
      if (value) await invokeCmd<void>("keychain_set", { key, value });
      else await invokeCmd<void>("keychain_delete", { key });
      // Never leave a stale plaintext copy behind in sessionStorage.
      ssSet(key, null);
      return;
    } catch (err) {
      console.warn(
        "[secureStore] keychain write failed; falling back to sessionStorage:",
        err,
      );
    }
  }
  ssSet(key, value);
}
