from __future__ import annotations
from .l1b_proj import L1bProj
import geocal  # type: ignore
from .pickle_method import *
import shutil
import os
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from .l1b_geo_qa_file import L1bGeoQaFile
    from multiprocessing.pool import Pool


class L1bTpCollect(object):
    """This is used to collect tiepoints between the ecostress data and
    our Landsat orthobase."""

    def __init__(
        self,
        igccol: geocal.IgcCollection,
        ortho_base: list[geocal.RasterImage],
        qa_file: L1bGeoQaFile | None = None,
        fftsize: int = 256,
        magnify: float = 4.0,
        magmin: float = 2.0,
        toler: float = 1.5,
        redo: int = 36,
        ffthalf: int = 2,
        seed: int = 562,
        num_x: int = 10,
        num_y: int = 10,
        proj_number_subpixel: int = 2,
        min_tp_per_scene: int = 20,
        min_number_good_scan: int = 41,
        pass_number: int = 1,
    ) -> None:
        self.igccol = igccol
        self.ortho_base = ortho_base
        self.qa_file = qa_file
        self.num_x = num_x
        self.num_y = num_y
        self.pass_number = pass_number
        self.proj_fname = [
            f"proj_initial_{i + 1}_pass_{self.pass_number}.img"
            for i in range(self.igccol.number_image)
        ]
        self.ref_fname = [
            f"ref_{i + 1}_pass_{self.pass_number}.img"
            for i in range(self.igccol.number_image)
        ]
        self.log_file = [
            f"tpmatch_{i + 1}_pass_{self.pass_number}.log"
            for i in range(self.igccol.number_image)
        ]
        self.run_dir_name = [
            f"tpmatch_{i + 1}_pass_{self.pass_number}"
            for i in range(self.igccol.number_image)
        ]
        self.p = L1bProj(
            self.igccol,
            self.proj_fname,
            self.ref_fname,
            self.ortho_base,
            qa_file=self.qa_file,
            min_number_good_scan=min_number_good_scan,
            number_subpixel=proj_number_subpixel,
            pass_through_error=True,
        )
        # Tom has empirically come up with a set of things to try to
        # get a better matching results. We go ahead and collect these
        # into a series of trials, trying each in turn if the previous
        # one doesn't get enough matches.
        #
        # Note the log and run directory gets updated before use, so it
        # is ok they have the same name here (these are just placeholders)
        self.tpcollect = []
        # Original try
        self.tpcollect.append(
            geocal.TiePointCollectPicmtch(
                self.igccol,
                self.proj_fname,
                image_index1=0,
                ref_image_fname=self.ref_fname[0],
                fftsize=fftsize,
                magnify=magnify,
                magmin=magmin,
                toler=toler,
                redo=redo,
                ffthalf=2,
                seed=562,
                log_file=self.log_file[0],
                run_dir_name=self.run_dir_name[0],
            )
        )
        # Increase mag, and change seed
        self.tpcollect.append(
            geocal.TiePointCollectPicmtch(
                self.igccol,
                self.proj_fname,
                image_index1=0,
                ref_image_fname=self.ref_fname[0],
                fftsize=fftsize,
                magnify=magnify + 0.5,
                magmin=magmin,
                toler=toler,
                redo=redo,
                ffthalf=2,
                seed=19364793,
                log_file=self.log_file[0],
                run_dir_name=self.run_dir_name[0],
            )
        )
        # Decrease mag, increase tolerance, change seed
        self.tpcollect.append(
            geocal.TiePointCollectPicmtch(
                self.igccol,
                self.proj_fname,
                image_index1=0,
                ref_image_fname=self.ref_fname[0],
                fftsize=fftsize,
                magnify=magnify - 0.5,
                magmin=magmin,
                toler=toler + 1.0,
                redo=redo,
                ffthalf=2,
                seed=578,
                log_file=self.log_file[0],
                run_dir_name=self.run_dir_name[0],
            )
        )
        # Decrease mag, increase tolerance, change seed
        self.tpcollect.append(
            geocal.TiePointCollectPicmtch(
                self.igccol,
                self.proj_fname,
                image_index1=0,
                ref_image_fname=self.ref_fname[0],
                fftsize=fftsize,
                magnify=magnify - 1.0,
                magmin=magmin,
                toler=toler + 1.0,
                redo=redo,
                ffthalf=2,
                seed=700,
                log_file=self.log_file[0],
                run_dir_name=self.run_dir_name[0],
            )
        )
        # Increase mag, increase tolerance, change seed
        self.tpcollect.append(
            geocal.TiePointCollectPicmtch(
                self.igccol,
                self.proj_fname,
                image_index1=0,
                ref_image_fname=self.ref_fname[0],
                fftsize=fftsize,
                magnify=magnify + 2.5,
                magmin=magmin,
                toler=toler + 3.0,
                redo=redo,
                ffthalf=2,
                seed=800,
                log_file=self.log_file[0],
                run_dir_name=self.run_dir_name[0],
            )
        )

        self.min_tp_per_scene = min_tp_per_scene

    def tp(
        self, i: int
    ) -> tuple[geocal.TiePointCollection, geocal.Time, geocal.Time, int, int, int, int]:
        """Get tiepoints for the given scene number"""
        ntpoint_initial = 0  # Initial value, so an exception below doesn't
        # result in "local variable referenced before
        # assignment" exception
        ntpoint_removed = 0
        ntpoint_final = 0
        number_match_try = 0
        try:
            with logger.catch(reraise=True):
                igc = self.igccol.image_ground_connection(i)
                if hasattr(igc, "time_table"):
                    tt = igc.time_table
                else:
                    tt = igc.sub_time_table
                for i2, tpcol in enumerate(self.tpcollect):
                    tpcol.image_index1 = i
                    tpcol.ref_image_fname = self.ref_fname[i]
                    tpcol.log_file = self.log_file[i] + "_%d" % i2
                    tpcol.run_dir_name = self.run_dir_name[i] + "_%d" % i2
                    shutil.rmtree(tpcol.run_dir_name, ignore_errors=True)
                    logger.info(
                        "Collecting tp for %s try %d" % (self.igccol.title(i), i2 + 1)
                    )
                    res = tpcol.tie_point_grid(self.num_x, self.num_y)
                    # Try this, and see how it works
                    ntpoint_initial = len(res)
                    ntpoint_removed = 0
                    if len(res) >= self.min_tp_per_scene:
                        len1 = len(res)
                        res = geocal.outlier_reject_ransac(
                            res,
                            ref_image=geocal.VicarLiteRasterImage(self.ref_fname[i]),
                            igccol=self.igccol,
                            threshold=3,
                        )
                        ntpoint_removed = len1 - len(res)
                        logger.info(
                            "Removed %d tie-points using RANSAC for %s"
                            % (len1 - len(res), self.igccol.title(i))
                        )
                    if len(res) >= self.min_tp_per_scene:
                        break
                number_match_try = i2 + 1
                if len(res) < self.min_tp_per_scene:
                    logger.info(
                        "Too few tie-point found. Found %d, and require at least %d. Rejecting tie-points for %s"
                        % (len(res), self.min_tp_per_scene, self.igccol.title(i))
                    )
                    res = []
                else:
                    logger.info(
                        "Found %d tie-points for %s try %d"
                        % (len(res), self.igccol.title(i), number_match_try)
                    )
                logger.info("Done collecting tp for %s" % self.igccol.title(i))
        except Exception:
            logger.warning(
                f"Exception occurred when collecting tie-points for {self.igccol.title(i)}"
            )
            logger.info("Skipping tie-points for this scene and continuing processing")
            if self.qa_file is not None:
                self.qa_file.encountered_exception = True
            res = []
        ntpoint_final = len(res)
        return (
            res,
            tt.min_time,
            tt.max_time,
            ntpoint_initial,
            ntpoint_removed,
            ntpoint_final,
            number_match_try,
        )

    def tpcol(
        self, pool: Pool | None = None
    ) -> tuple[geocal.TiePointCollection, list[tuple[geocal.Time, geocal.Time]]]:
        """Return tiepoints collected. We also return the time ranges for the
        ImageGroundConnection that we got good tiepoint for. This
        can be used by the calling program to determine such things
        as the breakpoints on the orbit model
        """

        # First project all the data.
        proj_res = self.p.proj(pool=pool)
        # TODO I think this is where we want to put in the cloud mask, but for
        # now we do this further down stream
        it = []
        for i in range(self.igccol.number_image):
            if proj_res[i]:
                it.append(i)
        if pool is None:
            tpcollist = list(map(self.tp, it))
        else:
            tpcollist = pool.map(self.tp, it)
        res = geocal.TiePointCollection()
        time_range_tp = []
        for i in range(self.igccol.number_image):
            for i2 in range(len(self.tpcollect)):
                lf = self.log_file[i] + "_%d" % i2
                if os.path.exists(lf) and self.qa_file is not None:
                    self.qa_file.add_tp_log(
                        self.pass_number, self.igccol.title(i) + "_%d" % i2, lf
                    )
        j = 0
        for i in range(self.igccol.number_image):
            if proj_res[i]:
                (
                    tpcol,
                    tmin,
                    tmax,
                    ntpoint_initial,
                    ntpoint_removed,
                    ntpoint_final,
                    number_match_try,
                ) = tpcollist[j]
                if self.qa_file is not None:
                    self.qa_file.add_tp_single_scene(
                        self.pass_number,
                        i,
                        self.igccol,
                        tpcol,
                        ntpoint_initial,
                        ntpoint_removed,
                        ntpoint_final,
                        number_match_try,
                    )
                if len(tpcol) > 0:
                    res.extend(tpcol)
                    time_range_tp.append((tmin, tmax))
                j += 1
            else:
                if self.qa_file is not None:
                    self.qa_file.add_tp_single_scene(
                        self.pass_number, i, self.igccol, [], 0, 0, 0, 0
                    )
        for i in range(len(res)):
            res[i].id = i + 1
        return res, time_range_tp
