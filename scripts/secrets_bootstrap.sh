#!/usr/bin/env bash
# secrets_bootstrap.sh — One-time setup of ~/.motoquant-secrets/git-creds.env
#
# This is the file the preflight script reads to load PRIMARY_PAT + BACKUP_PAT.
# Lives OUTSIDE the FUSE mount (~/, not the workspace folder), so it's not
# subject to the FUSE permission tier that randomly blocks tokens.md reads.
#
# Run this once, after issuing two GitHub fine-grained PATs:
#   1. PRIMARY  — your active token, used for every push
#   2. BACKUP   — emergency-only, kept cold; used if PRIMARY fails validation
#
# Both should be:
#   - Owner: da25mem5s02-debug
#   - Repository scope: da25mem5s02-debug/MotoQuant_v1 (single repo)
#   - Permissions: Contents R&W · Metadata R
#   - Different expiry dates (so you never lose both at once)
#
# Recommended cadence:
#   - PRIMARY: rotate every 30 days
#   - BACKUP:  rotate every 90 days
#
# Usage:
#   bash scripts/secrets_bootstrap.sh
#   # interactive prompts for both PATs

set -euo pipefail

# SECRETS_DIR resolution: same logic as session_preflight.sh.
# Override via MOTOQUANT_SECRETS_DIR for sandboxes where HOME is read-only
# or full. Real machines use $HOME/.motoquant-secrets/.
SECRETS_DIR="${MOTOQUANT_SECRETS_DIR:-}"
if [[ -z "${SECRETS_DIR}" ]]; then
  if [[ -w "${HOME}" ]] 2>/dev/null && touch "${HOME}/.motoquant-secrets-probe" 2>/dev/null; then
    rm -f "${HOME}/.motoquant-secrets-probe"
    SECRETS_DIR="${HOME}/.motoquant-secrets"
  else
    SECRETS_DIR="/tmp/.motoquant-secrets"
  fi
fi
readonly SECRETS_DIR
readonly SECRETS_FILE="${SECRETS_DIR}/git-creds.env"
readonly REPO_URL="https://github.com/da25mem5s02-debug/MotoQuant_v1.git"

log()   { printf "\033[36m[secrets]\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m[secrets WARN]\033[0m %s\n" "$*" >&2; }
fatal() { printf "\033[31m[secrets FATAL]\033[0m %s\n" "$*" >&2; exit 1; }

mkdir -p "${SECRETS_DIR}"
chmod 700 "${SECRETS_DIR}"

# Guard against accidental overwrite
if [[ -f "${SECRETS_FILE}" ]]; then
  warn "${SECRETS_FILE} already exists."
  read -rp "Overwrite? Old PATs will be lost. [yN] " ans
  if [[ "${ans}" != "y" && "${ans}" != "Y" ]]; then
    fatal "aborted by user"
  fi
fi

echo
log "Step 1 of 2 — PRIMARY PAT (active token, used every session)"
read -rsp "Paste PRIMARY_PAT (starts github_pat_, then Enter): " primary
echo
[[ -z "${primary}" ]] && fatal "PRIMARY_PAT cannot be empty"
[[ "${primary}" != github_pat_* ]] && warn "doesn't start with github_pat_ — verify you copied the right thing"

log "validating PRIMARY against ${REPO_URL}..."
if git -c "credential.helper=" \
      -c "credential.helper=!f() { echo username=x-access-token; echo password=${primary}; }; f" \
      ls-remote --heads "${REPO_URL}" main >/dev/null 2>&1; then
  log "PRIMARY: ✓ verified"
else
  fatal "PRIMARY failed validation — check token was copied correctly + has Contents R&W on this repo"
fi

echo
log "Step 2 of 2 — BACKUP PAT (cold spare, used only if primary fails)"
read -rsp "Paste BACKUP_PAT (or Enter to skip): " backup
echo
if [[ -n "${backup}" ]]; then
  log "validating BACKUP..."
  if git -c "credential.helper=" \
        -c "credential.helper=!f() { echo username=x-access-token; echo password=${backup}; }; f" \
        ls-remote --heads "${REPO_URL}" main >/dev/null 2>&1; then
    log "BACKUP: ✓ verified"
  else
    warn "BACKUP failed validation — saving anyway, but it won't help in an emergency"
  fi
else
  warn "no BACKUP — recommend you generate one and re-run this script"
fi

# Write the env file atomically (write to .tmp, fsync, mv)
cat > "${SECRETS_FILE}.tmp" <<EOF
# MotoQuant git credentials — DO NOT COMMIT
# Created: $(date -Iseconds)
# Read by: scripts/session_preflight.sh
# Identity policy (CLAUDE.md standing git-auth note):
#   user.name  = Arya Desai
#   user.email = da25mem5s02@student.nitw.ac.in

PRIMARY_PAT="${primary}"
PRIMARY_ROTATED="$(date -Iseconds)"
PRIMARY_EXPIRES="$(date -d '+30 days' -I 2>/dev/null || echo 'unknown')"

BACKUP_PAT="${backup:-}"
BACKUP_ROTATED="$([[ -n "${backup:-}" ]] && date -Iseconds || echo 'never-set')"
BACKUP_EXPIRES="$([[ -n "${backup:-}" ]] && date -d '+90 days' -I 2>/dev/null || echo 'never-set')"
EOF
mv -f "${SECRETS_FILE}.tmp" "${SECRETS_FILE}"
chmod 600 "${SECRETS_FILE}"

echo
log "========================================"
log "✓ Credentials saved to ${SECRETS_FILE}"
log "  mode: $(stat -c '%a' "${SECRETS_FILE}")"
log "  size: $(stat -c '%s' "${SECRETS_FILE}") bytes"
log "========================================"
log "Next steps:"
log "  1. Verify preflight can read it:"
log "       bash scripts/session_preflight.sh"
log "  2. Add a calendar reminder to rotate PRIMARY in 30 days."
log "  3. Add a calendar reminder to rotate BACKUP in 90 days."
log "  4. Once verified, you can delete the PAT from tokens.md"
log "     (preflight will never read tokens.md again)."
