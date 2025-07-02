from pathlib import Path
import geocal  # type: ignore
import numpy as np


class BrowseImage:
    """There is enough complication in creating the browse images for L1CG and L1CT that
    we wrap this in a class.

    We originally created the L1CT independently, so each tile created it own. It turns
    out that while this works fine most of the time, since we may have tiles with very little
    data in it we get occasionally weird stretches in the browse images. So instead, we
    produce one image and stretch it as part of the L1CG which is the full ECOSTRESS image.
    We then reproject and chop this to create the L1CT tile browse products.

    This does create a coupling between L1CG and L1CT. For now, this coupling is fine, we
    generate both of these anyways. We could rework this if needed.
    """

    def __init__(
        self, rad_data: list[np.ndarray], map_info: geocal.MapInfo, working_dir: Path
    ) -> None:
        """This takes the radiance data, with fill indicated as negative values or nans.
        The data should be in the false color order (so RGB of output image).

        We save the working files to the working_dir and produce a Gaussian stretch of the
        image.

        We then use this data in future steps for generating browse images.
        """
        pass
