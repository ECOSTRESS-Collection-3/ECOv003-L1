from geocal import *
orb = read_shelve("orbit.xml")
tt = read_shelve("time_table.xml")
cam = read_shelve("camera.xml")
def fname(band):
        return "/data/smyth/AsterMosiac/calnorm_b%d.img" % band
sdata = [VicarLiteRasterImage(fname(aster_band)) for aster_band in [14, 14, 12, 11, 10, 4]]
band = 0
ipi = Ipi(orb, cam, band, tt.min_time, tt.max_time, tt)
dem = SrtmDem("",False)
igc = IpiImageGroundConnection(ipi, dem, None)
number_integration_step = 1
max_height = 10e3
raycast_resolution = 100
rcast = IgcRayCaster(igc, 0, igc.number_line, number_integration_step, 
                     raycast_resolution,
                     max_height, 0, igc.number_sample)
f = VicarRasterImage("temp.img", "HALF", igc.number_line, igc.number_sample)
f.close()
f = mmap_file("temp.img", mode="r+")
while(not rcast.last_position):
    r = rcast.next_radiance(sdata[5])
    f[rcast.current_position,:] = r[0,:]
    if(rcast.current_position % 100 == 0):
        print("Done with %d" % rcast.current_position)
