This is a small amount of support for creating the conda environment that we are deliverying
to. We have this separate, because this is needed *before* we can do the normal configure/make
for the rest of the system (e.g., we don't have the compilers installed yet).

There is a small Makefile to handle creating this environment. You can create a 
Makefile.local file to override any of the Makefile content.

Note if you aren't a JPL developer, you can use the released versions of these
environments, see [afids conda package](https://github.com/Cartography-jpl/afids-conda-package).
