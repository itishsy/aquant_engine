#!/usr/bin/env sh
set -eu

VERSION="147.0.7727.57"
BASE_URL="https://storage.googleapis.com/chrome-for-testing-public/${VERSION}/linux64"
ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ARCHIVE_PATH="${ROOT_DIR}/chrome-linux64.zip"
EXTRACT_DIR="${ROOT_DIR}"

if command -v curl >/dev/null 2>&1; then
  downloader=(curl -fL "${BASE_URL}/chrome-linux64.zip" -o "${ARCHIVE_PATH}")
elif command -v wget >/dev/null 2>&1; then
  downloader=(wget -O "${ARCHIVE_PATH}" "${BASE_URL}/chrome-linux64.zip")
else
  echo "curl or wget is required to download Chrome." >&2
  exit 1
fi

echo "Downloading Chrome for Testing ${VERSION}..."
"${downloader[@]}"

echo "Extracting archive..."
rm -rf "${EXTRACT_DIR}/chrome-linux64"
unzip -o "${ARCHIVE_PATH}" -d "${EXTRACT_DIR}" >/dev/null

chmod +x "${EXTRACT_DIR}/chrome-linux64/chrome" \
         "${EXTRACT_DIR}/chrome-linux64/chrome-wrapper" \
         "${EXTRACT_DIR}/chrome-linux64/chrome_crashpad_handler" \
         "${EXTRACT_DIR}/chrome-linux64/chrome_sandbox"

echo "Chrome installed to ${EXTRACT_DIR}/chrome-linux64"
