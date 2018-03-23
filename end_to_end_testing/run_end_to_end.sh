# Sometimes useful to run test data through the system. This is a short
# script to do this, recorded so I don't have to figure out path names
# etc. each time.

l1_osp_dir="/home/smyth/Local/ecostress-test-data/latest/l1_osp_dir"
scene_file="/home/smyth/Local/ecostress-test-data/latest/Scene_80005_20150124T204251_20150124T204533.txt"

l1a_raw_process L0B_80005_20150124T204251_0100_01.h5 ${scene_file} ${l1_osp_dir} l1a_raw_run

l1a_cal_process l1a_raw_run/*BB*_80005_001*.h5 l1a_raw_run/*PIX*_80005_001*.h5 ${l1_osp_dir} l1a_cal_run
l1a_cal_process l1a_raw_run/*BB*_80005_002*.h5 l1a_raw_run/*PIX*_80005_002*.h5 ${l1_osp_dir} l1a_cal_run
l1a_cal_process l1a_raw_run/*BB*_80005_003*.h5 l1a_raw_run/*PIX*_80005_003*.h5 ${l1_osp_dir} l1a_cal_run

l1b_rad_process l1a_cal_run/*PIX*_80005_001*.h5 l1a_cal_run/*GAIN*_80005_001*.h5 l1a_raw_run/*ATT*_80005_*.h5 ${l1_osp_dir} l1b_rad_run
l1b_rad_process l1a_cal_run/*PIX*_80005_002*.h5 l1a_cal_run/*GAIN*_80005_002*.h5 l1a_raw_run/*ATT*_80005_*.h5 ${l1_osp_dir} l1b_rad_run
l1b_rad_process l1a_cal_run/*PIX*_80005_003*.h5 l1a_cal_run/*GAIN*_80005_003*.h5 l1a_raw_run/*ATT*_80005_*.h5 ${l1_osp_dir} l1b_rad_run

l1b_geo_process l1a_raw_run/*ATT*_80005_*.h5 ${l1_osp_dir} l1b_geo_run l1b_rad_run/*RAD*_80005_*.h5

l1b_project --all-band l1b_geo_run/*GEO*80005*_001*.h5 l1b_rad_run/*RAD*_80005_001*.h5 geo
l1b_project --all-band-real l1b_geo_run/*GEO*80005*_001*.h5 l1b_rad_run/*RAD*_80005_001*.h5 geo


