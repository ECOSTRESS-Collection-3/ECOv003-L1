# Some code for EcostressImageGroundConnection that is easier to do in
# python.
import geocal
import ecostress_swig


def _overlap(self, sample=None, scan_number=1):
    """Calculate the number of lines overlap we have between different
    scans. This is a bit approximate, we just look at the first two scans.
    The overlap depends on the sample. The default is the middle of the
    image, which should be about the minimum overlap.

    We can't always calculate the overlap. As a convention, we just return -1
    if there isn't actually an overlap value rather than treating this as
    an error.

    Note that this in image line numbers, not FrameCoordinate line numbers. So
    if we have averaged the data the overlap would be 128 (not 256)
    for 100% overlap."""
    if sample is None:
        sample = self.number_sample / 2
    ic1 = geocal.ImageCoordinate(self.number_line_scan * (scan_number + 1) - 1, sample)
    ic2, success = self.image_coordinate_scan_index(
        self.ground_coordinate(ic1), scan_number + 1
    )
    if success:
        return ic2.line - ic1.line
    return -1


ecostress_swig.EcostressImageGroundConnection.overlap = _overlap


def _match_overlap(self, matcher, scan, sample):
    """Determine the middle of the overlap for the given scan and sample
    with scan+1, and use the matcher to match the data. Returns
    ImageCoordinate 1, ImageCoordinate 2 guess, ImageCoordinate 2 match,
    success flag, and diagnostic."""
    ic1 = geocal.ImageCoordinate(self.number_line_scan * (scan + 1) - 1, sample)
    ic2, success = self.image_coordinate_scan_index(
        self.ground_coordinate(ic1), scan + 1
    )
    if not success:
        return (ic1, ic2, ic2, False, geocal.CcorrMatcher.IMAGE_MASKED)
    overlap = ic2.line - ic1.line
    ic1.line -= round(overlap / 2)
    ic2, success = self.image_coordinate_scan_index(
        self.ground_coordinate(ic1), scan + 1
    )
    if not success:
        return (ic1, ic2, ic2, False, geocal.CcorrMatcher.IMAGE_MASKED)
    ras1 = geocal.SubRasterImage(
        self.image,
        self.number_line_scan * scan,
        0,
        self.number_line_scan,
        self.number_sample,
    )
    ras2 = geocal.SubRasterImage(
        self.image,
        self.number_line_scan * (scan + 1),
        0,
        self.number_line_scan,
        self.number_sample,
    )
    ic1.line -= ras1.start_line
    ic2.line -= ras2.start_line
    ic2_res, _, _, success, diag = matcher.match(ras1, ras2, ic1, ic2)
    ic1.line += ras1.start_line
    ic2.line += ras2.start_line
    ic2_res.line += ras2.start_line
    if not success:
        return (ic1, ic2, ic2, success, diag)
    return (ic1, ic2, ic2_res, success, diag)


ecostress_swig.EcostressImageGroundConnection.match_overlap = _match_overlap


def _match_all_overlap(self, min_corr=0.90, min_var=50.0, sample_step=100):
    """Use a reasonable image matcher, and step through the whole IGC looking
    for matches. Return an list of results, which is a set of 4 tuples of
    scan number, ic1 (in scan number), ic2 (in scan number + 1), ic2_match"""
    m = geocal.CcorrLsmMatcher(
        geocal.CcorrMatcher(15, 15, 9, 9, min_corr, min_var), geocal.LsmMatcher(11, 11)
    )
    res = []
    for s in range(self.number_scan - 1):
        for smp in range(0, self.number_sample, sample_step):
            ic1, ic2, ic2_match, success, diag = self.match_overlap(m, s, smp)
            if success:
                res.append((s, ic1, ic2, ic2_match))
    return res


ecostress_swig.EcostressImageGroundConnection.match_all_overlap = _match_all_overlap


__all__ = []
