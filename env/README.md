This is a small amount of support for creating a pixi environment for development. 
We have this separate, because this is needed *before* we can do the normal configure/make
for the rest of the system (e.g., we don't have the compilers installed yet).

This repository doesn't require using pixi/conda, you just need to have the various 
requirements installed. But pixi is a simple way to handle this, so it is what we
usually do.

The pixi environment has a simple "configure" task that can be used after the environment
is created. This is just a convenience, you can also just directly run configure.

There is a small Makefile to handle creating this environment. You can create a 
Makefile.local file to override any of the Makefile content.

Note if you aren't a JPL developer, you can use the released versions of these
environments, see [afids conda package](https://github.com/Cartography-jpl/afids-conda-package).

You should already have [pixi installed](https://pixi.sh/latest/#installation), the makefile
assumes this is available.
