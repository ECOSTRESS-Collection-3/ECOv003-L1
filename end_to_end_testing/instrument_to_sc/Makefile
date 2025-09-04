orb_list := $(shell cat orb_list.txt)

orbit_%/result.log:
	python improve_fit.py $*

all_new: $(foreach t,$(orb_list),orbit_$t/result.log)
	python combine.py

all:
	-rm -r orbit_38*
	$(MAKE) all_new
one:
	rm -r orbit_38184/result.log
	$(MAKE) orbit_38184/result.log

