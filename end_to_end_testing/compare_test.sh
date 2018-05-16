# Script to run l1b-geo-run with a variety of errors, for two bands. Just
# saved so we have a record of what we did.
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.2,0.2,0.2" 2>&1 | tee diff_1_e1.log
mv l1b_geo_run l1b_geo_run_1_e1
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.4,0.4,0.4" 2>&1 | tee diff_2_e1.log
mv l1b_geo_run l1b_geo_run_2_e1
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.6,0.6,0.6" 2>&1 | tee diff_3_e1.log
mv l1b_geo_run l1b_geo_run_3_e1
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.8,0.8,0.8" 2>&1 | tee diff_4_e1.log
mv l1b_geo_run l1b_geo_run_4_e1
make l1b-geo-run PROCESS_ARG="--orbit-offset=1.0,1.0,1.0" 2>&1 | tee diff_5_e1.log
mv l1b_geo_run l1b_geo_run_5_e1

make l1b-geo-run PROCESS_ARG="--orbit-offset=0.2,0.2,0.2 --ecostress-band=5 --landsat-band=62" 2>&1 | tee diff_1_e5.log
mv l1b_geo_run l1b_geo_run_1_e5
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.4,0.4,0.4  --ecostress-band=5 --landsat-band=62" 2>&1 | tee diff_2_e5.log
mv l1b_geo_run l1b_geo_run_2_e5
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.6,0.6,0.6  --ecostress-band=5 --landsat-band=62" 2>&1 | tee diff_3_e5.log
mv l1b_geo_run l1b_geo_run_3_e5
make l1b-geo-run PROCESS_ARG="--orbit-offset=0.8,0.8,0.8 --ecostress-band=5 --landsat-band=62" 2>&1 | tee diff_4_e5.log
mv l1b_geo_run l1b_geo_run_4_e5
make l1b-geo-run PROCESS_ARG="--orbit-offset=1.0,1.0,1.0  --ecostress-band=5 --landsat-band=62" 2>&1 | tee diff_5_e5.log
mv l1b_geo_run l1b_geo_run_5_e5

