ECOSTRESS Level 1
=================

This is the ECOSTRESS Level 1 Radiance, Attitude, & Geolocation Product 
Generating Code (NTR-53468).

The ECOSTRESS collection 3 level 1 radiance data product is the
pre-cursor to the [Surface Biology and Geology (SBG) collection 1 level 1 brightness temperature data product algorithm](https://github.com/sbg-tir/SBG-TIR-L1).

One step build
=====================

If you just want to build the software, you can:

1. Check if you have pixi installed by trying to use it.

    pixi --help
	
2. If pixi isn't installed, follow the directions in [Use pixi](#use-pixi) below. This
   only needs to be done once.
   
3. Check out the code if not already available:

   mkdir -p \<working directory\>
   cd \<working directory\>
   git clone git@github.jpl.nasa.gov:ecostress/ecostress-level1.git
   
4. Optional - if you want to redirect any of the defaults create a 
   ecostress-level1/env/Makefile.local file as described in [Create the pixi environment](#create-the-pixi-environment)
   
5. Run 
   
   cd ecostress-level1/env && make full-build

   This creates the pixi environment (downloading and installing conda packages) and then
   does a full configure/build/install of the C++ and python code. Expect this to take
   somewhere around 15-20 minutes, depending on network speed and how much is already
   cached.
	
6. Set the pixi shell for running:

   pixi shell --manifest-path /project/sandbox/$(USER)/ecostress-build/build
   
   Replace the path after --manifest-path with the actual ENV_DIR if you changed this
   location. Note that "pixi shell" needs to be run from an interactive terminal - if you
   are calling this from a script, use "pixi run --manifest-path \<dir\> \<command\>" to run
   a single command in the environment instead.
   
7. Run a sample

   l1a_raw_process --help

   Note: the first time you run any of the newly built executables, it can take a minute
   or two to start up (this can look like it has hung, but it hasn't) - this seems to be
   the cost of reading the shared libraries over the network for the first time. Later
   runs only take a few seconds.

Building the software
=====================

One step build is described above, 

We use [pixi](https://pixi.prefix.dev/latest/) for creating our environment, and then
do a standard configure/make install of the software.

The installation is done in 2 steps, plus an optional 3rd.

1. Create the pixi environment with all the dependencies
2. Build and install the ecostress environment
3. (Optionally) install the python code in edit mode.

Use pixi
--------
We use [pixi](https://pixi.sh/latest/) for handling the conda environment. You should
have [installed](https://pixi.sh/latest/#installation) before using the Makefile.

   ```
   curl -fsSL https://pixi.sh/install.sh | sh
   source ~/.bashrc
   ```

Note this is a one time thing, once you have pixi installed you do not need to reinstall
it. You can update to the latest pixi version by

    pixi self-update
	
Create the pixi environment
---------------------------

To create the pixi environment, first:

    cd env

Look at the [Makefile](../Makefile), and read the top portion. If you want to make any
modifications, create a "Makefile.local" with your changes. We use a separate file rather
than directly modifying the Makefile so that you can update the repository (and possibly
the Makefile) without losing your changes.

Note that "Makefile.local" should just contain changes, it isn't a
copy or "Makefile" or anything like that. It gets included by Makefile
to override values.  In particular, you may want to modify the
location that things go to. So an example Makefile.local might be:

```
ENV_DIR=/project/sandbox/$(USER)/ecostress-build/build
ECOSTRESS_OSP_DIR=/project/test/ASTER/EndToEndTest/latest/l1_osp_dir
CONDA_PACKAGE_DIR=/project/sandbox/smyth/afids-conda-package/afids-conda-channel/
```

Note the Makefile default for CONDA_PACKAGE_DIR currently points at Mike Smyth's personal
sandbox directory. This works if you are on the JPL network and have read access to that
path, but if you don't (e.g., you aren't a JPL developer, or that directory is ever removed)
you will need to override CONDA_PACKAGE_DIR in your Makefile.local. See the note in
[env/README.md](env/README.md) about building your own channel from the
[afids conda package](https://github.com/Cartography-jpl/afids-conda-package) repository.

Once this is set up, you can create the environment with:

    make create-env
	
If you need to to recreate the environment from scratch:

    make recreate-env

This deletes the existing environment and creates it.

Note that you need to create the environment infrequently, just when there is
a new version of geocal or other top level changes.

Build and install the ecostress environment
-------------------------------------------

The pixi environment was set up in the directory you pointed to. cd to that 
directory, e.g. 

    cd /project/sandbox/$USER/ecostress-build/build
	
The actual environment is in the hidden directory .pixi, you can look into that for
anything you might want to find. But you don't normally directly use that directory.
Instead, you activate the pixi environment by:

    pixi shell
	
Next you need to run the standard configure/make cycle used with linux software. Because
it is common, we have supplied a canned pixi tasks for doing the configure and make. You
can use these unless you need to do something special (e.g., a different option for
configure).

    pixi run configure
    pixi run build

(Optionally) install the python code in edit mode
-------------------------------------------------

The default install copies our python code into the enviroment. This is what we need to
do for deliveries, our delivery can't depend on having the source directory available.

However it is extremely common for people to be developing python code, and wanting to
run the updated code. This can certainly be done by do a make install each time the code
has changed. However because this is so common python has support for [editable](https://setuptools.pypa.io/en/latest/userguide/development_mode.html#development-mode-a-k-a-editable-installs).
This sets up a special pointer so python know to look back in the source tree for code.

With this, the source tree *is* the install. So whatever you change there is immediately in
your build.

To use this option, do

    pixi run install-editmode

Developing
----------

You can now edit your python code and test changes.

Make sure you are working in a pixi environment:

    cd /project/sandbox/$USER/ecostress-build/build
	pixi shell
	
	

