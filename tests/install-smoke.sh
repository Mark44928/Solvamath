#!/data/data/com.termux/files/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="${TMPDIR:-${RUNNER_TEMP:-$HOME/.cache}}/solvamath-install-smoke.$$"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/home" "$TMP/data" "$TMP/prefix"
export HOME="$TMP/home" XDG_DATA_HOME="$TMP/data" PREFIX="$TMP/prefix"

bash "$ROOT/install.sh" >/dev/null
test -L "$TMP/prefix/bin/solvamath"
"$TMP/prefix/bin/solvamath" --version | grep -Fq "solvamath"
bash "$ROOT/install.sh" --uninstall >/dev/null
test ! -e "$TMP/prefix/bin/solvamath"
test ! -e "$TMP/data/solvamath/venv"
custom="$TMP/custom"
bash "$ROOT/install.sh" --prefix "$custom" >/dev/null
test -L "$custom/bin/solvamath"
bash "$ROOT/install.sh" --uninstall >/dev/null
test ! -e "$custom/bin/solvamath"
echo "installer smoke OK"
