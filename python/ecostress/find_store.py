from __future__ import annotations
from pathlib import Path
from collections.abc import Iterator
import os
import re
from typing import NamedTuple

# Code for finding files in /ops/store*, which we tend to do a lot


def walk_store(
    product: str, fix_dir: str | os.PathLike[str] | None = None, extension: str = ".h5"
) -> Iterator[Path]:
    """Simple iterator that steps through the product directories in
    all /ops/store* and returns files with an extension (default .h5).
    Because this can take a while to run, you can test it giving a fix directory
    and we only step through that (e.g., "/ops/store24")"""
    if fix_dir is None:
        dirlist: Iterator[Path] | list[Path] = Path("/ops").glob("store*")
    else:
        dirlist = [
            Path(fix_dir),
        ]
    for dirbase in dirlist:
        for root, _, files in (dirbase / "PRODUCTS" / product).walk():
            for file in files:
                if file.endswith(extension):
                    yield root / file


class ParseProductFile(NamedTuple):
    file_name: Path
    product: str
    orbit: int
    scene: int | None
    build_and_ver: str
    build: int | None
    ver: int


def walk_store_parse(
    product: str, fix_dir: str | os.PathLike[str] | None = None, extension: str = ".h5"
) -> Iterator[ParseProductFile]:
    """Variation of walk store that also parses the file name, because this is pretty common"""
    if fix_dir is None:
        dirlist: Iterator[Path] | list[Path] = Path("/ops").glob("store*")
    else:
        dirlist = [
            Path(fix_dir),
        ]
    for dirbase in dirlist:
        for root, _, files in (dirbase / "PRODUCTS" / product).walk():
            for file in files:
                if file.endswith(extension):
                    fname = root / file
                    m = re.match(
                        r"(ECOv00[23]_)?(?P<product>.*)_(?P<orbit>\d{5})_((?P<scene>\d{3})_)?\d+T\d+_(?P<build_and_ver>((?P<build>\d{4})_)?(?P<ver>\d\d))\.h5",
                        file,
                    )
                    if m:
                        yield ParseProductFile(
                            file_name=fname,
                            product=m["product"],
                            orbit=int(m["orbit"]),
                            scene=int(m["scene"]) if m["scene"] is not None else None,
                            build_and_ver=m["build_and_ver"],
                            build=int(m["build"]) if m["build"] is not None else None,
                            ver=int(m["ver"]),
                        )


__all__ = ["walk_store", "walk_store_parse", "ParseProductFile"]
