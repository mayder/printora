#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_DIR="$ROOT_DIR/agent"
OUTPUT_DIR="${PRINTORA_AGENT_RELEASE_DIR:-$ROOT_DIR/backend/app/data/agent_releases}"
SIGNING_KEY="${PRINTORA_AGENT_SIGNING_KEY_FILE:-}"
VERSION="${PRINTORA_AGENT_RELEASE_VERSION:-}"
PLATFORM="${PRINTORA_AGENT_RELEASE_PLATFORM:-linux/arm64}"
PUBLIC_KEY="$ROOT_DIR/packaging/agent/agent-release-ed25519.pub"
EXPECTED_KEY_ID="sha256:e241d16ebb469da7436ff050a36212635557eab1322495a2c62e2ca6caf24cdc"

fail() {
  printf '[agent-release] ERRO: %s\n' "$*" >&2
  exit 1
}

[[ -n "$VERSION" ]] || fail "PRINTORA_AGENT_RELEASE_VERSION obrigatório"
[[ -n "$SIGNING_KEY" && -f "$SIGNING_KEY" ]] || fail "chave privada de assinatura ausente"
[[ "$PLATFORM" == "linux/arm64" ]] || fail "plataforma não suportada: $PLATFORM"
[[ -f "$PUBLIC_KEY" ]] || fail "chave pública de release ausente"

source_version="$(awk -F'"' '/^const Version = / {print $2; exit}' "$AGENT_DIR/internal/agent/config.go")"
[[ "$source_version" == "$VERSION" ]] || fail "versão do código $source_version difere de $VERSION"

toolchain="$(cd "$AGENT_DIR" && go version | awk '{print $3}')"
[[ "$toolchain" == "go1.25.12" ]] || fail "toolchain inesperada: $toolchain"

actual_key_id="sha256:$(openssl pkey -pubin -in "$PUBLIC_KEY" -outform DER 2>/dev/null | openssl dgst -sha256 | awk '{print $NF}')"
[[ "$actual_key_id" == "$EXPECTED_KEY_ID" ]] || fail "fingerprint da chave pública divergente"

private_public_fingerprint="$(
  openssl pkey -in "$SIGNING_KEY" -pubout -outform DER 2>/dev/null |
    openssl dgst -sha256 |
    awk '{print $NF}'
)"
[[ "sha256:$private_public_fingerprint" == "$EXPECTED_KEY_ID" ]] || fail "chave privada não corresponde à chave pública"

work_dir="$(mktemp -d)"
trap 'rm -rf "$work_dir"' EXIT
mkdir -p "$OUTPUT_DIR"

build_binary() {
  local target="$1"
  (
    cd "$AGENT_DIR"
    env \
      CGO_ENABLED=0 \
      GOOS=linux \
      GOARCH=arm64 \
      GOWORK=off \
      SOURCE_DATE_EPOCH=0 \
      go build \
        -mod=readonly \
        -trimpath \
        -buildvcs=false \
        -ldflags='-buildid= -s -w' \
        -o "$target" \
        ./cmd/printora-agent
  )
}

build_binary "$work_dir/agent-a"
build_binary "$work_dir/agent-b"
cmp -s "$work_dir/agent-a" "$work_dir/agent-b" || fail "build não reproduzível"

artifact_base="printora-agent-linux-arm64-$VERSION"
binary="$OUTPUT_DIR/$artifact_base"
sbom="$OUTPUT_DIR/$artifact_base.sbom.cdx.json"
checksums="$OUTPUT_DIR/$artifact_base.SHA256SUMS"
checksums_signature="$checksums.sig"

if [[ -e "$binary" ]] && ! cmp -s "$work_dir/agent-a" "$binary"; then
  fail "artefato imutável já existe com conteúdo diferente: $binary"
fi
install -m 0755 "$work_dir/agent-a" "$binary"

(
  cd "$AGENT_DIR"
  go run github.com/CycloneDX/cyclonedx-gomod/cmd/cyclonedx-gomod@v1.10.0 \
    mod \
    -json \
    -noserial \
    -notimestamp \
    -output-version 1.6 \
    -output "$work_dir/sbom.json" \
    .
)

if [[ -e "$sbom" ]] && ! cmp -s "$work_dir/sbom.json" "$sbom"; then
  fail "SBOM imutável já existe com conteúdo diferente: $sbom"
fi
install -m 0644 "$work_dir/sbom.json" "$sbom"

(
  cd "$OUTPUT_DIR"
  shasum -a 256 "$(basename "$binary")" "$(basename "$sbom")" > "$checksums"
)
openssl pkeyutl -sign -inkey "$SIGNING_KEY" -rawin -in "$checksums" -out "$work_dir/checksums.sig"
openssl base64 -A -in "$work_dir/checksums.sig" > "$checksums_signature"
printf '\n' >> "$checksums_signature"

binary_sha256="$(shasum -a 256 "$binary" | awk '{print $1}')"
printf '%s' "$binary_sha256" > "$work_dir/binary-digest.txt"
openssl pkeyutl -sign -inkey "$SIGNING_KEY" -rawin \
  -in "$work_dir/binary-digest.txt" -out "$work_dir/binary.sig"
binary_signature="$(openssl base64 -A -in "$work_dir/binary.sig")"

openssl base64 -d -A -in "$checksums_signature" -out "$work_dir/checksums-verify.sig"
openssl pkeyutl -verify -pubin -inkey "$PUBLIC_KEY" -rawin \
  -in "$checksums" -sigfile "$work_dir/checksums-verify.sig" >/dev/null
printf '%s' "$binary_signature" | openssl base64 -d -A -out "$work_dir/binary-verify.sig"
openssl pkeyutl -verify -pubin -inkey "$PUBLIC_KEY" -rawin \
  -in "$work_dir/binary-digest.txt" -sigfile "$work_dir/binary-verify.sig" >/dev/null

python3 - "$OUTPUT_DIR/$artifact_base.metadata.json" "$VERSION" "$PLATFORM" \
  "$binary_sha256" "$binary_signature" "$EXPECTED_KEY_ID" "$toolchain" <<'PY'
import json
import pathlib
import sys

path, version, platform, sha256, signature, key_id, toolchain = sys.argv[1:]
payload = {
    "platform": platform,
    "version": version,
    "sha256": sha256,
    "signature": signature,
    "signature_algorithm": "ed25519-sha256",
    "signing_key_id": key_id,
    "toolchain": toolchain,
    "reproducible_build": True,
}
pathlib.Path(path).write_text(
    json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

printf '[agent-release] artefato=%s\n' "$binary"
printf '[agent-release] sha256=%s\n' "$binary_sha256"
printf '[agent-release] assinatura verificada\n'
