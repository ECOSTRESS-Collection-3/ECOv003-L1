This is code used to simulate input data that we will use for end to end 
testing. This is purposely very rough initially, and we will modify/improve
this as we continue development.

The plans for this are described on the 
[wiki](https://wiki.jpl.nasa.gov/display/ecostress/Test+Data) and subpages.

The file iss_spice/iss_2015.bsp gives a SPICE kernel for 2015 for the ISS.

The program iss_orbit_determine.py is a one-off used to determine the times that
we have passes over our CA ASTER mosaic. This isn't something we are likely to need
again. It generates the intermediate file iss_time.json, which again isn't something
we are likely to use regularly.

The notebook "Create IGC.ipynb" is a scratch area where we worked out how to generate
data.

The program create_end_to_end_test_data.py actual creates the test data.
