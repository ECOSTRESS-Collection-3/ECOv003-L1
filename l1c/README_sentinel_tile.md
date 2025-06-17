The sentinel tile scheme is described at https://hls.gsfc.nasa.gov/products-description/tiling-system/.

There is a file with the corners and UTM information for each tile at
https://hls.gsfc.nasa.gov/wp-content/uploads/2016/10/S2_TilingSystem2-1.txt

Note there is a typo in the file name, the second column should be MinLat and MaxLat.
We editted the file to fix this.

The tiles are exactly 109800 m square. Since 70m doesn't divide exactly, although
60m pixels does - so we miss a small amount with our 70m pixel sentinel tiles. We
may switch to 60, just to fit better.

Note there is some overlap between the tiles, so a given pixel may show up
in more than one.

We ingest the data in and generate a shapefile, which is a quicker way to determine
the tiles we need.
