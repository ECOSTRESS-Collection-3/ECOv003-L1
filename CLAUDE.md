# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

ECOSTRESS Level 1 Radiance, Attitude, & Geolocation Product Generating Executive (PGE) code (NTR-53468).
It's a hybrid C++/Python geospatial processing system built on the JPL AFIDS/GeoCal libraries, producing
the ECOSTRESS Collection 3 Level 1 data products (precursor to the SBG-TIR L1 algorithm).

## Build

This is a non-recursive GNU autotools project (single top-level `Makefile.am` including per-directory
`*.am` files, per Peter Miller's "Recursive Make Considered Harmful") layered on top of a
[pixi](https://pixi.sh/latest/) conda environment that provides the AFIDS/GeoCal dependencies and compilers.

One-step build (creates the pixi env, then configures/builds/installs):

```
cd env && make full-build
pixi shell --manifest-path <ENV_DIR>   # default ENV_DIR: /project/sandbox/$USER/ecostress-build/build
```

On this machine, a working dev build environment already exists at
`/home/smyth/Local/ecostress-build/build-pixi` — use that as `<ENV_DIR>`/`--manifest-path` for build and test
commands below rather than recreating one, unless told otherwise.

Manual steps, once the pixi env exists and you've `pixi shell`'d into `$ENV_DIR`:

```
pixi run configure          # ./configure --prefix=$CONDA_PREFIX ...
pixi run build              # make -j 10 all && make install
pixi run install-editmode   # cd python && pip install -e .  (source tree becomes the install)
```

Environment location and dependency paths (`ECOSTRESS_OSP_DIR`, `CONDA_PACKAGE_DIR`, ancillary data roots,
etc.) are set in `env/Makefile` — override by creating `env/Makefile.local` rather than editing the Makefile
directly. `configure.ac` looks up AFIDS/GeoCal, SWIG, doxygen (required if generating SWIG bindings), and
`h5diff`/`parallel` on PATH.

On this machine, `ECOSTRESS_OSP_DIR` (the operational static parameters dir — calibration/config data the
PGEs read at runtime, e.g. camera model XML, time tables) is already set in the pixi env to a local checkout
at `/home/smyth/Local/ecostress-test-data/latest/l1_osp_dir`.

`--without-swig` speeds up iterative C++-only development by skipping SWIG wrapper regeneration.

## Tests

**C++ unit tests** use Boost.Test (not gtest, despite the binary name). All tests link into one binary,
`ecostress_test_all` (built from `lib/test_all.cc` + each `lib/*_test.cc`):

```
make check                 # builds and runs everything, C++ side
make ecostress-check       # faster: just build/run the C++ unit tests (lib/test_all.sh), skip python
```

You can restrict to a subset via Boost's test selection, e.g. `run_test=ecostress_camera make ecostress-check`.
See `lib/test_all.sh` for `valgrind=1` / `gdb=1` support.

**Python tests** live in `python/tests/` (subdirs: `unit/`, `simulate/`, `interpolate/`, `fixtures/`) and run
with pytest-xdist:

```
cd python && make check    # pytest -n 10 tests
pytest tests/unit/some_test.py::test_name   # single test, from python/
pytest --run-long tests    # also run tests marked long_test (skipped by default)
```

Shared fixtures are registered as plugins in `python/tests/conftest.py` (`fixtures.dir_fixture`,
`fixtures.igc_fixture`, `fixtures.misc_fixture`). A `capture_test` marker exists for tests that regenerate
reference data for other tests — not run in normal test runs.

**End-to-end test**: `make end-to-end-check` (defined in `ecostress.am`) runs the full L1A_RAW → L1A_CAL →
L1B_RAD → L1B_GEO → L1C pipeline on reference orbit data and diffs the HDF5 output against known-good
results with `h5diff` (with specific paths excluded where run-to-run numerical noise is expected — see
`H5DIFF_FLAG` in `ecostress.am`).

## Lint / format / typing

`ruff check` / `ruff format` (config in `python/pyproject.toml`) and `mypy --disallow-untyped-defs ecostress`
(needs `PYTHONPATH=$(PWD)`, see `python/Makefile`) are available via `cd python && make lint` / `make format`
/ `make mypy`. Per `python/README_developer.md`, none of these are treated as build-blocking errors: ruff
warnings are silenced per-file in `pyproject.toml` rather than fixed when they're noise, and type hints are
used only as informal documentation, not enforced/complete static typing — don't add strict typing
requirements or treat lint/mypy failures as build failures.

## Architecture

**Directory layout mirrors ECOSTRESS product levels**, each processed in this pipeline order (see
`include.am`): `l1a_raw` → `l1a_cal` → `l1b_rad` → `l1b_geo` → `l1c` → `l2t`. Each level directory follows
the same pattern:

- `<LEVEL>.am` — automake fragment installing the level's scripts (included from top-level `include.am`)
- `<LEVEL>_PGE` — bash wrapper script (the actual PGE entry point invoked in production, parses a
  `RunConfig` XML and calls the process script)
- `<level>_process` — Python CLI script (`#!/usr/bin/env python`, docopt-style usage) that imports `geocal`
  and `ecostress` and does the real work by calling into `python/ecostress/<level>_*.py`

The actual processing logic lives in the installed **`python/ecostress`** package (e.g.
`l1b_geo_process.py`, `l1b_geo_strategy.py`, `l1b_geo_strategy_3pass.py`, `l1b_rad_generate.py`,
`l1a_raw_pix_generate.py`). The `*_PGE` / `*_process` scripts are thin entry points; when changing behavior,
the real edits are almost always in `python/ecostress`.

**Core geolocation/radiometry C++ library** is in `lib/`: one class per `.cc`/`.h` pair (camera model,
orbit, time table, scan mirror, image-ground-connection, radiance apply/average, band-to-band registration,
resampler, HDF-EOS grid/filehandle helpers). Each class that needs a Python binding has a matching `.i` SWIG
interface file listed in `lib/lib.am`; SWIG-generated wrappers get compiled into the same `libecostress.la`
and exposed to Python. If you add or change a C++ class's public interface, the `.i` file usually needs a
matching update. `ecostress_igc_fixture.h` / `global_fixture.h` set up shared C++ test fixtures (backed by
AFIDS test data via `ECOSTRESS_TEST_DATA`).

This C++ library and the Python package both depend heavily on **AFIDS/GeoCal**
(`github.jpl.nasa.gov:Cartography/{afids,geocal}`), a separate JPL geospatial toolkit that provides the base
orbit/camera/image-ground-connection classes this repo's `Ecostress*` classes subclass or compose. Reading
GeoCal headers/Python is often necessary to understand what this repo's classes actually do.

A checkout of the GeoCal source is available locally at `/home/smyth/Local/geocal-repo` (it has its own
CLAUDE.md) — refer to it when a question is really about GeoCal's own classes/behavior rather than
ECOSTRESS's use of them. Note that ECOSTRESS builds against a conda-packaged GeoCal, so this checkout may be
slightly ahead of or behind the exact version in the pixi env; the two are usually close but not guaranteed
identical.

**Ecostress-specific IGC**: `EcostressImageGroundConnection` (`lib/ecostress_image_ground_connection.*`) and
`EcostressIgcCollection` (`lib/ecostress_igc_collection.*`) are the central geometric model classes tying
camera + orbit + time table together to map instrument pixels to ground coordinates; most L1B_GEO logic
flows through these.

## Other notable locations

- `tools/` — standalone calibration/analysis scripts, not installed, run in place from the source tree.
- `end_to_end_testing/` — scripts/notebooks for generating simulated end-to-end test data (distinct from the
  `make end-to-end-check` regression test, which runs against pre-existing reference data).
- `notebooks/` — exploratory Jupyter notebooks.
- `docker-env/`, `env/` — pixi/conda + Docker environment setup, separate from the autotools build itself.
