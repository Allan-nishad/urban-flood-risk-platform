#!/usr/bin/env bash
# NASA GES DISC GPM IMERG V07B Automated Granule Retrieval Script
# Requires NASA Earthdata credentials configured in ~/.netrc or ~/.urs_cookies
# Reference: https://disc.gsfc.nasa.gov/information/howto?title=How%20to%20Download%20Data%20Files%20from%20HTTPS%20Service%20with%20wget

mkdir -p data\raw\rainfall\gpm_imerg_v07
COOKIE_JAR=~/.urs_cookies

mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220825-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220825-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220826-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220826-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220827-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220827-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220828-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220828-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220829-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220829-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220830-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220830-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/08
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/08/3B-DAY.MS.MRG.3IMERG.20220831-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/08/3B-DAY.MS.MRG.3IMERG.20220831-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220901-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220901-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220902-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220902-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220903-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220903-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220904-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220904-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220905-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220905-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220906-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220906-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220907-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220907-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220908-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220908-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220909-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220909-S000000-E235959.V07B.nc4"
mkdir -p data\raw\rainfall\gpm_imerg_v07/2022/09
curl -b $COOKIE_JAR -c $COOKIE_JAR -L --netrc -o "data\raw\rainfall\gpm_imerg_v07/2022/09/3B-DAY.MS.MRG.3IMERG.20220910-S000000-E235959.V07B.nc4" "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGDF.07/2022/09/3B-DAY.MS.MRG.3IMERG.20220910-S000000-E235959.V07B.nc4"