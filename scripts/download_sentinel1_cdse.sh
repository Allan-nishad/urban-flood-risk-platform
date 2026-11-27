#!/usr/bin/env bash
# Copernicus Data Space Ecosystem (CDSE) Sentinel-1A Level-1 GRDH Retrieval Script
# Requires CDSE OAuth access token in $CDSE_TOKEN or ~/.cdse_token
# Registration: https://dataspace.copernicus.eu/

mkdir -p data/raw/weather/sentinel1

# Pre-event baseline reference (dry/antecedent state): 2022-08-12T06:10:26+05:30
curl -H "Authorization: Bearer $CDSE_TOKEN" -o "data/raw/weather/sentinel1/S1A_IW_GRDH_1SDV_20220812T004026_20220812T004051_044512_054FD9_2CA3.SAFE.zip" "https://zipper.dataspace.copernicus.eu/odata/v1/Products(934efe81-0b22-5f86-8b3b-8a5eea0b4103)/$value"

# Disaster event scene (acquired morning of peak flooding): 2022-09-05T06:10:28+05:30
curl -H "Authorization: Bearer $CDSE_TOKEN" -o "data/raw/weather/sentinel1/S1A_IW_GRDH_1SDV_20220905T004028_20220905T004053_044862_055BB0_85F8.SAFE.zip" "https://zipper.dataspace.copernicus.eu/odata/v1/Products(c27b5ffa-71a9-5d55-b728-10c870356750)/$value"

# Post-event recession reference (+12 days): 2022-09-17T06:10:28+05:30
curl -H "Authorization: Bearer $CDSE_TOKEN" -o "data/raw/weather/sentinel1/S1A_IW_GRDH_1SDV_20220917T004028_20220917T004053_045037_056191_B23F.SAFE.zip" "https://zipper.dataspace.copernicus.eu/odata/v1/Products(4da4b0bc-7fa7-53ec-8289-42b784a0d9e2)/$value"
