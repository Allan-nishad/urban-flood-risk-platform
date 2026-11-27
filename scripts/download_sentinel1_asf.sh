#!/usr/bin/env bash
# Alaska Satellite Facility (ASF DAAC) Sentinel-1A Level-1 GRDH Retrieval Script
# Requires NASA Earthdata credentials in ~/.netrc
# Registration: https://urs.earthdata.nasa.gov/

mkdir -p data/raw/weather/sentinel1
COOKIE_JAR=~/.urs_cookies

# Pre-event baseline reference (dry/antecedent state): 2022-08-12T06:10:26+05:30
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data/raw/weather/sentinel1/S1A_IW_GRDH_1SDV_20220812T004026_20220812T004051_044512_054FD9_2CA3.zip" "https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20220812T004026_20220812T004051_044512_054FD9_2CA3.zip"

# Disaster event scene (acquired morning of peak flooding): 2022-09-05T06:10:28+05:30
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data/raw/weather/sentinel1/S1A_IW_GRDH_1SDV_20220905T004028_20220905T004053_044862_055BB0_85F8.zip" "https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20220905T004028_20220905T004053_044862_055BB0_85F8.zip"

# Post-event recession reference (+12 days): 2022-09-17T06:10:28+05:30
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data/raw/weather/sentinel1/S1A_IW_GRDH_1SDV_20220917T004028_20220917T004053_045037_056191_B23F.zip" "https://datapool.asf.alaska.edu/GRD_HD/SA/S1A_IW_GRDH_1SDV_20220917T004028_20220917T004053_045037_056191_B23F.zip"
