#!/bin/bash
# ==============================================================================
# Script: generate_manifest.sh
# Mục đích: Tính toán SHA-256 Checksum cho các tệp NIST ACVP JSON để lập manifest
# Tác giả: Trần Phạm Thiên Ân - MSSV: 1150080127
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="$DIR/src/test/resources/nist-acvp"
OUTPUT_FILE="$TARGET_DIR/manifest.json"

echo "=== Đang tạo manifest.json cho dữ liệu NIST ACVP ==="

AES_FILE="$TARGET_DIR/aes-gcm-sample.json"
RSA_FILE="$TARGET_DIR/rsa-oaep-sample.json"

SHA_AES=$(shasum -a 256 "$AES_FILE" | awk '{print $1}')
SIZE_AES=$(stat -f%z "$AES_FILE" 2>/dev/null || stat -c%s "$AES_FILE")

SHA_RSA=$(shasum -a 256 "$RSA_FILE" | awk '{print $1}')
SIZE_RSA=$(stat -f%z "$RSA_FILE" 2>/dev/null || stat -c%s "$RSA_FILE")

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat <<EOF > "$OUTPUT_FILE"
{
  "dataset": "NIST ACVP Test Vectors (Selective Extraction)",
  "source_repository": "https://github.com/usnistgov/ACVP-Server",
  "branch_path": "gen-val/json-files/",
  "license": "NIST Software License (Public Domain / 17 U.S.C. 105)",
  "student": "Trần Phạm Thiên Ân",
  "student_id": "1150080127",
  "generated_at": "$TIMESTAMP",
  "files": [
    {
      "name": "aes-gcm-sample.json",
      "algorithm": "AES-GCM-256",
      "sha256": "$SHA_AES",
      "size_bytes": $SIZE_AES
    },
    {
      "name": "rsa-oaep-sample.json",
      "algorithm": "RSA-OAEP-2048",
      "sha256": "$SHA_RSA",
      "size_bytes": $SIZE_RSA
    }
  ]
}
EOF

echo "Đã tạo thành công: $OUTPUT_FILE"
cat "$OUTPUT_FILE"

