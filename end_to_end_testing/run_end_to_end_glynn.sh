# Sometimes useful to run test data through the system. This is a short
# script to do this, recorded so I don't have to figure out path names
# etc. each time.

l1_osp_dir="/home/smyth/Local/ecostress-test-data/latest/l1_osp_dir"
scene_file="/home/smyth/Local/ecostress-test-data/latest/Scene_80006_20150124T204431_20150124T204523.txt"
l0b_file="L0B_80006_20150124T204431_0100_01.h5"

l1a_raw_process ${l0b_file} ${scene_file} ${l1_osp_dir} l1a_raw_run

l1a_cal_process l1a_raw_run/*BB*_80006_001*.h5 l1a_raw_run/*PIX*_80006_001*.h5 ${l1_osp_dir} l1a_cal_run

l1b_rad_process l1a_cal_run/*PIX*_80006_001*.h5 l1a_cal_run/*GAIN*_80006_001*.h5 l1a_raw_run/*ATT*_80006_*.h5 ${l1_osp_dir} l1b_rad_run

l1b_geo_process l1a_raw_run/*ATT*_80006_*.h5 ${l1_osp_dir} l1b_geo_run l1b_rad_run/*RAD*_80006_001*.h5

l1b_project --all-band l1b_geo_run/*GEO*80006*_001*.h5 l1b_rad_run/*RAD*_80006_001*.h5 glynn_geo
l1b_project --all-band-real l1b_geo_run/*GEO*80006*_001*.h5 l1b_rad_run/*RAD*_80006_001*.h5 glynn_geo
