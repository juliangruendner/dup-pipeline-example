#!/usr/bin/env bash
set -e

BASE_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit 1 ; pwd -P )"
FHIR_BASE_URL=${DATA_NODE_TESTDATA_UPLOAD_FHIR_BASE_URL:-http://localhost:8088/fhir}

send_bundle() {
  curl -X POST -H "Content-Type: application/json" --cacert "$BASE_DIR/auth/cert.pem" -d @- "$FHIR_BASE_URL"
}

FILES=("$BASE_DIR"/testdata/*)
for fhirBundle in "${FILES[@]}"; do
  case "$fhirBundle" in
    *.ndjson)
      echo "Sending Testdata bundles from $fhirBundle ..."
      while IFS= read -r line || [ -n "$line" ]; do
        [ -z "$line" ] && continue
        printf '%s' "$line" | send_bundle
      done < "$fhirBundle"
      ;;
    *.json)
      echo "Sending Testdata bundle $fhirBundle ..."
      send_bundle < "$fhirBundle"
      ;;
    *)
      echo "Skipping $fhirBundle (not .json or .ndjson)"
      ;;
  esac
done
