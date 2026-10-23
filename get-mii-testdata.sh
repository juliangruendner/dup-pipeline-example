#!/usr/bin/env bash

MII_TESTDATA_DOWNLOAD_URL="https://github.com/medizininformatik-initiative/mii-testdata/releases/download/v2026.0.0-rc.1/testdata-bundles-ndjson-20260330-135816.zip"

wget -O testdata.zip "$MII_TESTDATA_DOWNLOAD_URL"
unzip testdata.zip -d testdata-temp
mkdir testdata
cd testdata-temp/ || exit


find . -name '*.ndjson' -exec mv {} ../testdata \;

cd ..
rm testdata.zip
rm -rf testdata-temp
