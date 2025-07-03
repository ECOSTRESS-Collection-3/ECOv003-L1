import numpy as np
import h5py  # type: ignore
from .write_standard_metadata import WriteStandardMetadata


class L1aBbSimulate(object):
    """This is used to generate L1A_BB simulated data. Right now, this is just
    dummy data."""

    def __init__(self, l1a_pix_fname: str) -> None:
        """Create a L1APixSimulate to process the given L1A_PIX file."""
        self.l1a_pix = h5py.File(l1a_pix_fname, "r")
        # We can calculate with these values by doing something like:
        # b_295 = np.array([VicarLiteRasterImage("BlackbodyRadiance/b%d_295.rel" % (b+1)).read_double(10,10,1,1)[0,0] for b in range(6)])
        # b_325 = np.array([VicarLiteRasterImage("BlackbodyRadiance/b%d_325.rel" % (b+1)).read_double(10,10,1,1)[0,0] for b in range(6)])
        # off = (b_325 * bb_295_mean - b_295 * bb_325_mean) / (bb_295_mean - bb_325_mean)
        # gain = (b_295 - b_325) / (bb_295_mean - bb_325_mean)
        #
        # Nominal values from Tom, adjusted to offset is negative value (which
        # is better for our simulations, since DN < 0 is marked as bad,
        # radiance values < offset get marked as bad when we push through our
        # simulation
        self.bb_325_mean = [6, 2456, 2532, 2603, 2845, 2845]
        self.bb_325_sigma = [0, 0, 0, 0, 0, 0]
        # Played with these values until we got a slightly negative offset
        self.bb_295_mean = [4, 849 + 580, 925 + 590, 996 + 590, 1238 + 610, 1238 + 710]
        self.bb_295_sigma = [0, 0, 0, 0, 0, 0]

    def copy_metadata(self, field: str) -> None:
        self.m.set(field, self.l1a_pix["/StandardMetadata/" + field][()])

    def gaussian_data(self, mean: float, sigma: float) -> np.ndarray:
        """Return random data of the right length for the given mean and sigma.
        Tom uses the vicar function gausnois. We could use that, but since
        numpy already has this function and we don't need to then generate
        and read a separate file, it is cleaner just to do this in python.

        Can revisit this if it ends up mattering.
        """
        # Special handling for 0
        len = 256
        if sigma <= 0:
            r = np.empty((len, 1), dtype=np.uint16)
            r[:] = mean
        else:
            r = np.round(np.random.normal(mean, sigma, (len, 1))).astype(np.uint16)
        # Repeat the data so it is the full size (64 is number of samples,
        # 44 is number of scans in a scene
        return np.repeat(np.repeat(r, 64, axis=1), 44, axis=0)

    def create_file(self, l1a_bb_fname: str) -> None:
        fout = h5py.File(l1a_bb_fname, "w")
        g = fout.create_group("BlackBodyPixels")
        for b in range(6):
            t = g.create_dataset(
                "b%d_blackbody_325" % (b + 1),
                data=self.gaussian_data(self.bb_325_mean[b], self.bb_325_sigma[b]),
            )
            t.attrs["Units"] = "dimensionless"
            t = g.create_dataset(
                "b%d_blackbody_295" % (b + 1),
                data=self.gaussian_data(self.bb_295_mean[b], self.bb_295_sigma[b]),
            )
            t.attrs["Units"] = "dimensionless"
        self.m = WriteStandardMetadata(
            fout, product_specfic_group="L1A_BBMetadata", pge_name="L1A_RAW_PGE"
        )
        self.copy_metadata("RangeBeginningDate")
        self.copy_metadata("RangeBeginningTime")
        self.copy_metadata("RangeEndingDate")
        self.copy_metadata("RangeEndingTime")
        self.m.write()
        fout.close()


__all__ = ["L1aBbSimulate"]
