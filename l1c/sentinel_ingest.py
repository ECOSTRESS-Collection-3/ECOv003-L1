# Short program to create a shape file we can use to find
# the tiles covering an area.
import pandas as pd
import geocal
import osgeo.ogr as ogr
import osgeo.osr as osr

df = pd.read_csv("S2_TilingSystem2-1.txt", sep=r'\s+')
with geocal.ShapeFile("sentinel_tile.shp", "w") as sf:
    lay = sf.add_layer("tile", ogr.wkbPolygon, [["tile_id", ogr.OFTString, 100],
                                                ["epsg", ogr.OFTInteger],
                                                ["xstart", ogr.OFTReal],
                                                ["ystart", ogr.OFTReal]])
    print(f"Doing {len(df)} rows")
    i = 0
    for row in df.itertuples():
        i += 1
        if(i % 100 == 0):
            print(f"Doing {i}")
        lay.add_feature({"tile_id" : row.TilID,
                         "epsg" : row.EPSG,
                         "xstart" : row.Xstart,
                         "ystart" : row.Ystart,
                         "Geometry" :
                         geocal.ShapeLayer.polygon_2d([(row.MinLon, row.MaxLat),
                                                       (row.MaxLon, row.MaxLat),
                                                       (row.MaxLon, row.MinLat),
                                                       (row.MinLon, row.MinLat)])
                         })

