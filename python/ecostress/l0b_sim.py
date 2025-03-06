import numpy as np
import h5py  # type: ignore

# from .misc import time_split, ecostress_file_name
from .write_standard_metadata import WriteStandardMetadata
import os
import re
from datetime import datetime
from geocal import Time  # type: ignore

# import pkt_defs.py

J2KS = 946728000.0  # seconds from UNIX EPOCH to J2000 EPOCH 2000-01-01:12:00:00
GPSS = 315964800.0  # seconds from UNIX EPOCH to GPS EPOCH 1980-01-06:00:00:00
GP2K = J2KS - GPSS  # difference

"""
New L0B contents

"flex/bip": shape (203, 64, 256, 6), type "<i2">
"flex/id_line": shape (203, 64), type "<u4">
"flex/id_packet": shape (203,), type "<u4">
"flex/state": shape (203,), type "<u4">
"flex/time_fsw": shape (203,), type "<f8">
"flex/time_sync_fpie": shape (203,), type "<u8">
"flex/time_sync_fsw": shape (203,), type "<u8">

By seconds:

"hk/bad/hr/attitude": shape (479, 4), type "<f4">
"hk/bad/hr/position": shape (479, 3), type "<f4">
"hk/bad/hr/time": shape (479,), type "<f8">
"hk/bad/hr/time_fsw": shape (479,), type "<f8">
"hk/bad/hr/velocity": shape (479, 3), type "<f4">

"hk/bad/hr/time_dpuio": shape (479,), type "<u8">
"hk/bad/hr/time_error_correction": shape (479,), type "<f8">

"hk/status/mode/dpuio": shape (479,), type "<u4">
"hk/status/mode/op": shape (479,), type "<u4">
"hk/status/motor/bb1": shape (479,), type "<u4">
"hk/status/motor/bb2": shape (479,), type "<u4">
"hk/status/motor/last/register": shape (479,), type "|u1">
"hk/status/motor/last/value": shape (479,), type "<u4">
"hk/status/motor/mode": shape (479,), type "<u4">
"hk/status/motor/position": shape (479, 5), type "<u4">
"hk/status/motor/pstate": shape (479,), type "|u1">
"hk/status/motor/rate": shape (479, 5), type "<u4">
"hk/status/motor/sun_safe": shape (479,), type "<u4">
"hk/status/motor/time": shape (479, 5), type "<f8">
"hk/status/motor/wait": shape (479,), type "|u1">
"hk/status/temperature": shape (479, 2, 5), type "<u2">
"hk/status/time": shape (479,), type "<f8">
"hk/status/time_fsw": shape (479,), type "<f8">

Motor control modes (uint8):

0: IDLE
1: SPINNING
2: BLACKBODY_1
3: BLACKBODY_2
4: SUNSAFE
5: MANUAL

P6_R(dn): (0.06021953 * dn) - 507.6739 - OR6
P7_R(dn): (0.05874407 * dn) - 501.7596 - OR7
P8_R(dn): (0.06097170 * dn) - 500.0066
P9_R(dn): (0.06017587 * dn) - 501.1489

kc1 = PRT_313_T( P7_R(raw.AnalogsTemp_BB_COLD_1) )
kc2 = PRT_314_T( P7_R(raw.AnalogsTemp_BB_COLD_2) )
kc3 = PRT_317_T( P7_R(raw.AnalogsTemp_BB_COLD_3) )
kc4 = PRT_315_T( P7_R(raw.AnalogsTemp_BB_COLD_4) )
kc5 = PRT_318_T( P7_R(raw.AnalogsTemp_BB_COLD_5) )
kh1 = PRT_465_T( P7_R(raw.AnalogsTemp_BB_HOT_1) )
kh2 = PRT_466_T( P7_R(raw.AnalogsTemp_BB_HOT_2) )
kh3 = PRT_467_T( P7_R(raw.AnalogsTemp_BB_HOT_3) )
kh4 = PRT_468_T( P7_R(raw.AnalogsTemp_BB_HOT_4) )
kh5 = PRT_469_T( P7_R(raw.AnalogsTemp_BB_HOT_5) )

OR7 = 0

PRT_313_T = -251.317967433, 0.239896820, 0.0000112950 
PRT_314_T = -251.292298761, 0.240556797, 0.0000106890 
PRT_315_T = -251.586351114, 0.241068843, 0.0000103820 
PRT_317_T = -251.232620017, 0.240397229, 0.0000107746 
PRT_318_T = -252.648616198, 0.242199907, 0.0000102870 
PRT_320_T = -248.318808633, 0.235249359, 0.0000128970 
PRT_343_T = -249.183019039, 0.236078108, 0.0000129710
PRT_449_T = -248.291451026, 0.234993147, 0.0000131630 
PRT_450_T = -248.506534677, 0.235773805, 0.0000127110 
PRT_452_T = -248.527405294, 0.235959618, 0.0000124980 
PRT_460_T = -247.917423853, 0.234297755, 0.0000135960 
PRT_465_T = -248.079410647, 0.234477690, 0.0000135210 
PRT_466_T = -248.227089752, 0.234806579, 0.0000134300 
PRT_467_T = -248.223699750, 0.234794972, 0.0000132930 
PRT_468_T = -248.326045842, 0.234842736, 0.0000134580 
PRT_469_T = -248.021569284, 0.234107049, 0.0000137990 
"""
"""
# short word offsets into FPIE packet array

# packet primary header
HSYNC = 0
PKTID = HSYNC + 2
ENCOD = PKTID + 2
ISTATE = ENCOD + 128
FTIME = ISTATE + 2
DTIME = FTIME + 4
DSYNC = DTIME + 4
PLEN = DSYNC + 4

# compression header
f_n_m = 148
f_b_d = f_n_m + 2
f_n_x = f_b_d + 2
f_n_y = f_n_x + 2
f_n_z = f_n_y + 2
f_k_i = f_n_z + 2
f_c_s = f_k_i + 2

# comp init data
cb1 = 162
cb2 = cb1 + 20
cb3 = cb2 + 20
cb4 = cb3 + 20
cb5 = cb4 + 20
cb6 = cb5 + 20
HSUM = 282
HDR_LEN = 284

# uncompressed data block
DB1 = HDR_LEN
DB2 = DB1 + 16384
DB3 = DB2 + 16384
DB4 = DB3 + 16384
DB5 = DB4 + 16384
DB6 = DB5 + 16384
DSUM = DB6 + 16384

# total packet length in 16 bit words
PKT_LEN = DSUM + 2
"""
BANDS = 6
# number of pixels per focal plane
PPFP = 256
# number of focal planes per full scan
# FPPSC = 5400
# number of FPs in each BB per scan
BBLEN = 64
# number of FPs per raw packet
FPPPKT = 64
# Scans per scene
SCPS = 44


class L0BSimulate(object):
    # This is used to generate L0 simulated data. We take the output of the
    # l1a_raw pge and reverse the processing to produce a L0 file.
    def __init__(self, l1a_raw_att_fname, l1a_eng_fname, scene_files, osp_dir=None):
        # Create a L0Simulate to process the given files. The orbit based files
        # are passed in as a file name, and the scene based files are passed as a dict
        # with keys of scene id. The values in the dict are an array, the first entry
        # is the L1A_RAW_PIX file and the second is the L1A_BB file.
        self.l1a_eng_fname = l1a_eng_fname
        if osp_dir is None:
            self.osp_dir = os.path.dirname(self.l1a_eng_fname)
        else:
            self.osp_dir = osp_dir
        self.l1a_raw_att_fname = l1a_raw_att_fname
        self.scene_files = scene_files

    def kelvin2DN(self, x, K):
        # convert Kelvin temperature to PRT DN values given PRT coefficients
        # a = array of coefficients
        # K = kelvin temperature
        # DN is the "+" solution of quadratic wth the following coefficients
        a = x[0] * x[3] * x[3]
        b = 2.0 * x[0] * x[3] * x[4] + x[1] * x[3]
        c = (
            x[0] * x[4] * x[4] + x[1] * x[4] + x[2] - (K - 273.15)
        )  # needs to be celsius
        rdn = (np.sqrt(b * b - 4.0 * a * c) - b) / (2.0 * a)
        dn = int(rdn + 0.5)
        # print("kelvin2DN,X=%f %f %f %f %f K=%f RDN=%f DN=%d" % (x[0],x[1],x[2],x[3],x[4],K,rdn,dn))
        return dn  # little-Endian

    def create_file(self, l0b_fname):
        print("====  CREATE_FILE L0B_FNAME %s ====" % l0b_fname)
        print("====  Start time  ", datetime.now(), "  ====")

        #  Read the PRT coefficients
        PRT = np.zeros((17, 3), dtype=np.float64)
        with open(self.osp_dir + "/prt_coef.txt", "r") as pf:
            for i, pvl in enumerate(pf):
                p0, p1, p2, p3 = re.split(r"\s+", pvl.strip())
                PRT[i, 0] = float(p1)
                PRT[i, 1] = float(p2)
                PRT[i, 2] = float(p3)
                print(
                    "PRT[%d](%s) = %20.12f %20.12f %20.12f"
                    % (i, p0, PRT[i, 0], PRT[i, 1], PRT[i, 2])
                )
        pf.close()
        kc = np.zeros((5, 5), dtype=np.float64)
        kh = np.zeros((5, 5), dtype=np.float64)
        kc[0,] = PRT[1, 2], PRT[1, 1], PRT[1, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kc[1,] = PRT[2, 2], PRT[2, 1], PRT[2, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kc[2,] = PRT[4, 2], PRT[4, 1], PRT[4, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kc[3,] = PRT[3, 2], PRT[3, 1], PRT[3, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kc[4,] = PRT[5, 2], PRT[5, 1], PRT[5, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kh[0,] = PRT[12, 2], PRT[12, 1], PRT[12, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kh[1,] = PRT[13, 2], PRT[13, 1], PRT[13, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kh[2,] = PRT[14, 2], PRT[14, 1], PRT[14, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kh[3,] = PRT[15, 2], PRT[15, 1], PRT[15, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])
        kh[4,] = PRT[16, 2], PRT[16, 1], PRT[16, 0], PRT[0, 0], -(PRT[0, 1] + PRT[0, 2])

        #  Get EV start codes for BB and IMG pixels
        ev_codes = np.zeros((4, 4), dtype=np.int32)
        ev_names = [p0 for p0 in range(5)]
        " open EV codes file "
        RPM = 0
        FP_DUR = 0
        MAX_FPIE = 0
        FPPSC = 0
        with open(self.osp_dir + "/ev_codes.txt", "r") as ef:
            for i, evl in enumerate(ef):
                p0, p1, p2, p3, p4 = re.split(r"\s+", evl.strip())
                ev_names[i] = p0
                if i < 4:
                    ev_codes[i, 0] = int(p1)
                    ev_codes[i, 1] = int(p2)
                    ev_codes[i, 2] = int(p3)
                    ev_codes[i, 3] = int(p4)
                    print(
                        "EV_CODES[%d](%s) = (%d,%d) (%d,%d)"
                        % (
                            i,
                            ev_names[i],
                            ev_codes[i, 0],
                            ev_codes[i, 1],
                            ev_codes[i, 2],
                            ev_codes[i, 3],
                        )
                    )
                else:
                    RPM = float(p1)  # RPM = 25.396627  # 25.4 nominal
                    FP_DUR = (
                        float(p2) / 1000000.0
                    )  # FP_DUR = 0.000032196620  # 0.0000322 nominal
                    MAX_FPIE = int(p3)  # MAX_FPIE=1749248
                    FPPSC = int(p4)
                    print(
                        "RPM=%f FP_DUR=%f20.10 MAX_FPIE=%d FPPSC=%d"
                        % (RPM, FP_DUR, MAX_FPIE, FPPSC)
                    )

        ef.close()
        ev0 = ev_codes[3, 0]
        ev1 = ev_codes[3, 1]
        ev2 = ev_codes[3, 2]

        if RPM == 0.0 or FP_DUR == 0.0 or MAX_FPIE == 0 or FPPSC == 0:
            print("*** Input parameters not set ***")
            return -3
        PKT_DUR = FP_DUR * float(FPPPKT)
        # FPIE mirror encoder - 50.95 degree swath width
        # covered by 25.475 degree of mirror scan.  Mirror
        # is 2-sided, so every other scan is 180 degrees apart
        EV_DUR = 60.0 / RPM / float(MAX_FPIE)  # = 1.3504 microsecond/count
        FP_EV = FP_DUR * RPM * MAX_FPIE / 60.0  # = 22.922887 counts/FP
        # Total FPs per scan including hot and cold BB
        FPB3 = FPPSC + BBLEN * 2

        # backup times from IMG to BB3 and BB2
        dt3 = (ev_codes[2, 0] - ev_codes[0, 0]) * EV_DUR
        dt2 = (ev_codes[2, 0] - ev_codes[1, 0]) * EV_DUR
        print("DT3=%f, DT2=%f" % (dt3, dt2))

        # bo = [5, 3, 2, 0, 1, 4]  # L0B to L1A (raw pix)
        bo = [3, 4, 2, 1, 5, 0]  # L1A to L0B (sim)

        self.l0b_fname = l0b_fname
        l0b_fd = h5py.File(self.l0b_fname, "w", driver="core")
        l1e = h5py.File(self.l1a_eng_fname, "r")

        # Write Standarad Metadata fake-out WriteStandardMetadata()
        m = WriteStandardMetadata(
            l0b_fd,
            product_specfic_group="L0BMetadata",
            proc_lev_desc="Level 0B Data Parameters",
            pge_name="L0B",
            build_id="0.0",
            pge_version="0.0",
            level0_file=True,
        )
        m.set("RangeBeginningDate", l1e["/StandardMetadata/RangeBeginningDate"][()])
        m.set("RangeBeginningTime", l1e["/StandardMetadata/RangeBeginningTime"][()])
        m.set("RangeEndingDate", l1e["/StandardMetadata/RangeEndingDate"][()])
        m.set("RangeEndingTime", l1e["/StandardMetadata/RangeEndingTime"][()])
        m.set("StartOrbitNumber", l1e["/StandardMetadata/StartOrbitNumber"][()])
        m.set("StopOrbitNumber", l1e["/StandardMetadata/StopOrbitNumber"][()])
        m.write()
        l0b_fd.flush()

        # copy data from raw attitude/ephemeris and engineering file to HK packets
        att_fd = h5py.File(self.l1a_raw_att_fname, "r")
        aq = att_fd["Attitude/quaternion"]
        aqc, aqr = aq.shape
        at = att_fd["Attitude/time_j2000"]
        ep = att_fd["Ephemeris/eci_position"]
        epc, epr = ep.shape
        ev = att_fd["Ephemeris/eci_velocity"]
        et = att_fd["Ephemeris/time_j2000"]

        r2k = l1e["rtdBlackbodyGradients/RTD_295K"]
        r3k = l1e["rtdBlackbodyGradients/RTD_325K"]
        enc, enr = r2k.shape

        # create ancillary data sets
        print("Creating HK Group")
        l0b_fd.create_group("/hk")
        l0b_fd.create_group("/hk/bad")

        hbh = l0b_fd.create_group("/hk/bad/hr")
        att = hbh.create_dataset("attitude", (aqc, 4), dtype=np.float32)
        pos = hbh.create_dataset("position", (epc, 3), dtype=np.float32)
        att_time = hbh.create_dataset("time", (aqc,), dtype=np.float64)
        att_fsw = hbh.create_dataset("time_fsw", (epc,), dtype=np.float64)
        vel = hbh.create_dataset("velocity", (epc, 3), dtype=np.float32)

        tdpuio = hbh.create_dataset("time_dpuio", (aqc,), dtype=np.uint64)
        tdpuio[:] = 0
        tcorr = hbh.create_dataset("time_error_correction", (aqc,), dtype=np.float64)
        tcorr[:] = 0

        hs = l0b_fd.create_group("/hk/status")
        hsmd = l0b_fd.create_group("/hk/status/mode")
        hsmd.create_dataset("dpuio", (enc,), dtype=np.uint8)
        hsmd.create_dataset("op", (enc,), dtype=np.uint32)

        hsmt = l0b_fd.create_group("/hk/status/motor")
        hsmt.create_dataset("bb1", (enc,), dtype=np.uint32)
        hsmt.create_dataset("bb2", (enc,), dtype=np.uint32)

        hsmtl = l0b_fd.create_group("/hk/status/motor/last")
        hsmtl.create_dataset("register", (enc,), dtype=np.uint8)
        hsmtl.create_dataset("value", (enc,), dtype=np.uint32)

        hsmt.create_dataset("mode", (enc,), dtype=np.uint32)
        hsmt.create_dataset("position", (enc, 5), dtype=np.uint32)
        hsmt.create_dataset("pstate", (enc,), dtype=np.uint8)
        hsmt.create_dataset("rate", (enc, 5), dtype=np.uint32)
        hsmt.create_dataset("sun_safe", (enc,), dtype=np.uint32)
        hsmt.create_dataset("time", (enc, 5), dtype=np.float64)
        hsmt.create_dataset("wait", (enc,), dtype=np.uint8)

        bbt = hs.create_dataset("temperature", (enc, 2, enr), dtype=np.uint16)
        bb_time = hs.create_dataset("time", (enc,), dtype=np.float64)
        bb_fsw = hs.create_dataset("time_fsw", (enc,), dtype=np.float64)

        # Copy ATT/EPH into HK data set
        att[:, :] = aq[:, :]
        pos[:, :] = ep[:, :] / 0.3048
        vel[:, :] = ev[:, :] / 0.3048
        for i in range(aqc):
            att_time[i] = Time.time_j2000(at[i]).gps
        for i in range(epc):
            att_fsw[i] = Time.time_j2000(et[i]).gps

        #  ****  convert Kelvin to DN  ****
        for i in range(enc):
            for j in range(enr):
                bbt[i, 0, j] = self.kelvin2DN(kc[j, :], r2k[i, j])
                bbt[i, 1, j] = self.kelvin2DN(kh[j, :], r3k[i, j])
                # print("ENC=%d ENR=%d R2K=%f R3K=%f BB2=%d BB3=%d" %(enr,enc,r2k[i,j],r3k[i,j],bbt[i,0,j],bbt[i,1,j]))

        eng_time = l1e["/rtdBlackbodyGradients/time_j2000"]
        for i in range(enc):
            bb_time[i] = Time.time_j2000(eng_time[i, 0]).gps
            bb_fsw[i] = Time.time_j2000(eng_time[i, 1]).gps
        att_fd.close()
        l1e.close()
        l0b_fd.flush()

        # create FLEX packet
        flex_g = l0b_fd.create_group("/flex")
        # create packet dataset template
        bip = flex_g.create_dataset(
            "bip",
            shape=(1, FPPPKT, PPFP, BANDS),
            maxshape=(None, FPPPKT, PPFP, BANDS),
            dtype="uint16",
        )
        lid = flex_g.create_dataset(
            "id_line", shape=(1, FPPPKT), maxshape=(None, FPPPKT), dtype="uint32"
        )
        pid = flex_g.create_dataset(
            "id_packet", shape=(1,), maxshape=(None,), dtype="uint32"
        )
        flex_st = flex_g.create_dataset(
            "state", shape=(1,), maxshape=(None,), dtype="uint32"
        )
        fswt = flex_g.create_dataset(
            "time_fsw", shape=(1,), maxshape=(None,), dtype="float64"
        )
        fpie_sync = flex_g.create_dataset(
            "time_sync_fpie", shape=(1,), maxshape=(None,), dtype="uint64"
        )
        fsw_sync = flex_g.create_dataset(
            "time_sync_fsw", shape=(1,), maxshape=(None,), dtype="uint64"
        )

        # running count of packets
        tot_pkt = 0
        # running count of image lines
        tot_lines = 0
        # *** packet ID adjust for missing packets ***
        pkt_id = 0

        # working array including PIX and BB, and 1 packet
        bufsiz = FPB3 + FPPPKT
        pix_buf = np.zeros((PPFP, bufsiz, BANDS), dtype=np.uint16)
        ev_buf = np.zeros(bufsiz, dtype=np.uint32)
        evc = np.zeros((2, FPB3), dtype=np.uint32)

        for i in range(2):  # generate EVs for both mirror phases
            for j in range(BBLEN):  # BB pixels
                evc[i, j + ev0] = int(ev_codes[0, i * 2] + j * FP_EV + 0.5) % MAX_FPIE
                evc[i, j + ev1] = int(ev_codes[1, i * 2] + j * FP_EV + 0.5) % MAX_FPIE
            for j in range(FPPSC):  # image pixels
                evc[i, j + ev2] = int(ev_codes[2, i * 2] + j * FP_EV + 0.5) % MAX_FPIE

        p0 = 0
        prev = 0
        evp = 0
        t0 = 0
        pix_dat = [b for b in range(BANDS)]
        b295 = [b for b in range(BANDS)]
        b325 = [b for b in range(BANDS)]
        ### angnadir = 180.0

        # process scenes make sure to do it in order
        total_scenes = len(self.scene_files)
        for v, scn in enumerate(self.scene_files):
            scene, l1a_raw_pix_fname, l1a_bb_fname = scn

            # open raw pixel data file
            pix_fd = h5py.File(l1a_raw_pix_fname, "r", driver="core")

            # Also get simulated black body data
            bb_fd = h5py.File(l1a_bb_fname, "r", driver="core")

            # link to pixel and bb datsasets
            for b in range(BANDS):
                pix_dat[b] = pix_fd["/UncalibratedPixels/pixel_data_%d" % (b + 1)]
                b295[b] = bb_fd["/BlackBodyPixels/b%d_blackbody_295" % (b + 1)]
                b325[b] = bb_fd["/BlackBodyPixels/b%d_blackbody_325" % (b + 1)]

            pix_2k = pix_fd["/Time/line_start_time_j2000"]

            # lines and pix per scene (assume all BANDS are the same)
            lines, pix = pix_dat[0].shape
            tot_lines = tot_lines + lines
            line = 0
            # pkts for scene
            tot_pkt = int((FPB3 * tot_lines / PPFP + FPPPKT - 1) / FPPPKT)
            # extend packet dataset to new total
            bip.resize(tot_pkt, 0)
            lid.resize(tot_pkt, 0)
            pid.resize(tot_pkt, 0)
            flex_st.resize(tot_pkt, 0)
            fswt.resize(tot_pkt, 0)
            fpie_sync.resize(tot_pkt, 0)
            fsw_sync.resize(tot_pkt, 0)
            print(
                "\n===  Scene=%d %s TOTAL=%d P0=%d tot_lines=%d tot_pkt=%d"
                % (v, l1a_raw_pix_fname, total_scenes, p0, tot_lines, tot_pkt)
            )

            # Iterate through data lines in current scene 256 lines at a time
            ## scan = 0
            while line < lines:
                # pix_buf and ev_buf offsets
                ps0 = p0 + ev0
                pe0 = ps0 + BBLEN  # HBB first
                ps1 = p0 + ev1
                pe1 = ps1 + BBLEN  # then CBB
                ps2 = p0 + ev2
                pe2 = ps2 + FPPSC  # then IMG

                # assemble pix and bb data into buffer, with offset from previous buffer
                for b in range(BANDS):
                    pix_buf[:, ps0:pe0, b] = b325[b][line : line + PPFP, :]
                    pix_buf[:, ps1:pe1, b] = b295[b][line : line + PPFP, :]
                    pix_buf[:, ps2:pe2, b] = pix_dat[b][line : line + PPFP, :]

                ## ev_buf[ps2:pe2] = env[scan,:] # Use provided EVs for IMG
                ## for i in range(BBLEN): # calculate EVs for BBs
                ##   ev_buf[ps1+i] = (ev_buf[ps2] + int( (i-BBLEN)*FP_EV+0.5 ))%MAX_FPIE
                ##   ev_buf[ps0+i] = (ev_buf[ps1+i] - int( BBLEN*FP_EV+0.5 ))%MAX_FPIE
                ## scan += 1

                ev_buf[ps0:pe0] = evc[evp, ev0 : ev0 + BBLEN]  # use generated EVs
                ev_buf[ps1:pe1] = evc[evp, ev1 : ev1 + BBLEN]
                ev_buf[ps2:pe2] = evc[evp, ev2 : ev2 + FPPSC]

                # step through buffer in packet steps (FPPPKT) starting from 0
                bts = 0
                bte = p0 + FPB3
                t2k = pix_2k[line]
                if p0 > 0:
                    t2k += FP_DUR * float(FPPPKT - p0)  # for next packet
                ### angnadir = 180.0 - angnadir
                print("====  ", datetime.now(), "  ====")
                print(
                    "L=%d PKT=%d GPT=%f GPP=%f T0=%f EVP=%d BTE=%d P0=%d PS0=%d PS1=%d PS2=%d PE2=%d"
                    % (
                        line,
                        pkt_id,
                        Time.time_j2000(t2k).gps,
                        Time.time_j2000(pix_2k[line]).gps,
                        Time.time_j2000(t0).gps,
                        evp,
                        bte,
                        p0,
                        ps0,
                        ps1,
                        ps2,
                        pe2,
                    )
                )
                while bts < bte:
                    # see where current buffer pointer is
                    pte = bts + FPPPKT
                    # print("SCENE=%s PKT_ID=%d BTS=%d BTE=%d" %(scene, pkt_id,  bts, bte))
                    # write a packet if sufficient data
                    if pte <= bte:
                        # write next packet ancillary data
                        pid[pkt_id] = pkt_id + 1
                        " *** add FPIE sync clock and FPIE 1st pix to FSWT offset (1MHz)"
                        b = bts - p0
                        if b >= ev0 and b < ev1:
                            t = dt3
                        elif b >= ev1 and b < ev2:
                            t = dt2
                        else:
                            t = 0
                        if prev == 0:
                            fswt[pkt_id] = Time.time_j2000(t2k - t).gps
                            if t == 0 and b >= 0:
                                t2k += PKT_DUR
                        else:
                            fswt[pkt_id] = Time.time_j2000(t0).gps
                        print(
                            "SCENE=%s Pkt %d GPT=%f T0=%f BTS=%d PTE=%d BTE=%d PREV=%d EV0=%d B=%d"
                            % (
                                scene,
                                pkt_id,
                                Time.time_j2000(t2k - t).gps,
                                Time.time_j2000(t0).gps,
                                bts,
                                pte,
                                bte,
                                prev,
                                ev_buf[bts],
                                b,
                            )
                        )

                        # write packet data
                        lid[pkt_id, :] = ev_buf[bts:pte]
                        for b in range(BANDS):
                            bip[pkt_id, :, :, b] = pix_buf[
                                :, bts:pte, bo[b]
                            ].transpose()
                        # next point in pix_buf
                        bts = pte
                        # next packet
                        pkt_id += 1
                        prev = 0

                        if bts == bte:  # reached end of valid data in current pix_buf
                            # reset offset into next pix_buf
                            p0 = 0
                            print(
                                "End PIX_BUF SCENE=%d BTS=%d PKT_ID=%d"
                                % (v, bts, pkt_id)
                            )
                            evp = 1 - evp  #  swap EV arrays

                    else:  # at the remainder of current pix_buf
                        # set offset to next pix_buf
                        p0 = bte - bts
                        prev = p0
                        t0 = t2k  # save FSWT from end of current scan for next packet
                        print(
                            "Remainder SCENE=%d BTE=%d BTS=%d PKT_ID=%d T0=%f"
                            % (v, bte, bts, pkt_id, Time.time_j2000(t0).gps)
                        )
                        # move remainder data to front of pix_buf
                        pix_buf[:, :p0, :] = pix_buf[:, bts:bte, :]
                        ev_buf[:p0] = ev_buf[bts:bte]
                        evp = 1 - evp  #  swap EV arrays
                        # escape bts while loop to go to next scene
                        if v + 1 < total_scenes or line + PPFP < lines:
                            bts = bte
                        else:  # last runt packet of last scene< fill remaining with dummy
                            bts = 0
                            bte = FPPPKT
                            print("Final runt packet: %d" % p0)
                            pix_buf[0:PPFP, p0:FPPPKT, :] = 0xFFFF
                            # ev_buf[ p0:FPPPKT ] = 0xffffffff
                            ev_buf[p0:FPPPKT] = ev_buf[p0]
                    # end writing current packet

                # next line in scene
                line += PPFP
                # end copying current pix_buf to packets

            # close current raw pix and bb files
            pix_fd.close()
            bb_fd.close()
            print("End SCENE=%s time=%s" % (scene, str(datetime.now())))
            l0b_fd.flush()
            # end writing packets for current scene file
        # *** take care of runt packet of last scene ***
        print("End all scenes, TOT_LINES=%d runt P0=%d" % (tot_lines, p0))
        # end scene files loop

        # Write L0B metadata
        print("Writing L0BMetadata to L0B file %s" % self.l0b_fname)
        l0b_mg = l0b_fd["L0BMetadata"]
        # l0b_pl = l0b_mg.create_dataset("PacketList", shape=(tot_pkt,), dtype="uint32")
        # l0b_ps = l0b_mg.create_dataset("PacketStatus", shape=(tot_pkt,), dtype="uint16")
        # for i in range( tot_pkt ): l0b_pl[i] = i
        # l0b_ps[:] = 0
        # l0b_ps.attrs["PacketPercentage"] = "1.00000000"
        st = h5py.special_dtype(vlen=str)
        l0b_ifl = l0b_mg.create_dataset(
            "InputFileList", shape=(len(2 * self.scene_files),), dtype=st
        )
        for v in range(len(self.scene_files)):
            l0b_ifl[v * 2] = self.scene_files[v][1]
            l0b_ifl[v * 2 + 1] = self.scene_files[v][2]
        l0b_fd.flush()

        # done...close L0B file
        l0b_fd.close()
        print("====  End time  ", datetime.now(), "  ====")
