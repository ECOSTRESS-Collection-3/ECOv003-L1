# We may make a more complicated makefile/automake at some point, but
# for now this should be sufficient

LIST = grid_design.png

all: $(LIST)

%.dotcpp: %.dot grid_design.inp
	cpp $< $@

%.png: %.dotcpp
	dot -Tpng -o $@ $<

%.svg: %.dotcpp
	dot -Tsvg -o $@ $<

%.display: %.png
	display $<
