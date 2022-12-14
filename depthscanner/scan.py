# First import the libraries
import compas
import pyrealsense2 as pyrs
import numpy as np
from scipy.interpolate import griddata
from timeit import default_timer as timer

# Start the scanner here
# Declare RealSense pipeline, encapsulating the actual device and sensors

_pipe = None
_pipe = pyrs.pipeline()

def get_pipe():
    global _pipe
    return _pipe

def dfScan():

    ### send param
    #def dfScan(some_param):
    #print(some_param)

    ## Timer Setup:
    start = timer()
    print('Scanning..')

    # set the resolution
    xres = 1280
    yres = 720
    
    # Declare pointcloud object, for calculating pointclouds and texture mappings
    pc = pyrs.pointcloud()
    # We want the points object to be persistent so we can display the last cloud when a frame drops
    points = pyrs.points()
    pipe = get_pipe()
    # Create a config and configure the pipeline to stream
    config = pyrs.config()
    #set resolution
    #config.enable_stream(pyrs.stream.depth, xres, yres, pyrs.format.z16, 30)
    #Start streaming 
    
    profile = pipe.start()
    #profile = pipe.start(config)

    ## to figure out the depth scale, normally 0.001
    #depth_sensor = profile.get_device().first_depth_sensor()
    #print depth_sensor.get_depth_scale()

    try:
        # Wait for the next set of frames from the camera
        frames = pipe.wait_for_frames()
        # Fetch depth frames
        depth = frames.get_depth_frame()
        # calc pointcloud
        points = pc.calculate(depth)
        #w = depth.get_width()
        #h = depth.get_height()
        
        # get point coordinates
        pts = np.asanyarray(points.get_vertices())

        print('Points aquired..')

        ## numpy nonzero 
        ptss = []
        for i in pts:
            if i[0] != 0:
                ptss.append(i)
    
        ## make x,y,z lists
        x = []
        y = []
        z = []
        for i in ptss:
            x.append(i[0])
            y.append(i[1])
            z.append(i[2])

        print("NUMBER OF POINTS:")
        print(len(z))
        
        #bounding box of scan
        x_min = -0.5 #min(x)
        x_max = 0.5 #max(x)
        y_min = -0.30 #min(y)
        y_max = 0.30 #max(y)

        #target grid to interpolate to
        xi = np.arange(x_min,x_max,0.004)
        yi = np.arange(y_min,y_max,0.004)
        xi,yi = np.meshgrid(xi,yi)
             
        # interpolate
        zi = griddata((x,y),z,(xi,yi),method='linear',fill_value=1)
    	#zi = np.nan_to_num(zi,copy=False)

        print('Points interpolated.')

        # set mask
        #mask = (xi > 0.5) & (xi < 0.6) & (yi > 0.5) & (yi < 0.6)
        #zi[mask] = np.nan

        # flip, reverse, scale and move data (in the case where the sensor is looking top-down)
        zi = zi * -1000 
        
        # ADJUST Z-LEVEL
        zi += 860

        zi_oriented = np.flipud(zi)
        #zi_rot = np.rot180(zi_oriented) 
        # zi_rot = np.rot90(zi_oriented, 3)
        
        # reformat z data to docofossor (single list of z values)
        lz = [j for i in zi_oriented for j in i]
      
        # construct docofossor dimension list
        nc = 250 #len(zi[0]) >>> see target grid in scangrid
        nr = 150 #len(zi) >>> see target grid in scangrid
        ox = -515
        oy = -805
        cx = 4 #1*n
        cy = 4 #1*n
        gx = ox
        gy = oy
        dim = [nc,nr,ox,oy,cx,cy,0,0,gx,gy]
        
        # construct df list
        df = dim + lz

        # values to return to rhino
        return df

    finally:  ### dont stop it
        pipe.stop()
        print("Scan Completed")

def pcScan(): 

    # Declare pointcloud object, for calculating pointclouds and texture mappings
    pc = pyrs.pointcloud()
    # We want the points object to be persistent so we can display the last cloud when a frame drops
    points = pyrs.points()
    # Declare RealSense pipeline, encapsulating the actual device and sensors
    pipe = pyrs.pipeline()
    #Start streaming 
    profile = pipe.start()

    try:
        # Wait for the next set of frames from the camera
        frames = pipe.wait_for_frames()
        # Fetch depth frames
        depth = frames.get_depth_frame()
        # calculate point cloud
        points = pc.calculate(depth)
        # get vertices
        pts = np.asanyarray(points.get_vertices())
        ## take only values that are not zero (removes about 2/3 of the points)
        ptss = []
        for pt in pts:
            if pt[0] != 0:
                r = [i * 1000 for i in pt] #scale by 1000
                ptss.append(r)
        #return the list of vertices to rhino
        print(pts[0])
        #print(ptss[0])
        return ptss
       
    finally:
        pipe.start()
        pipe.stop()

if __name__ == "__main__":
    s = pcScan()
