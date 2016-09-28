
"""
	SLDservice:
		extractminmax
"""

import os, sys, time, math,json

# gdal import
import gdal
from gdalconst import *

def getimagelocation(image):
	"""return image location"""

	#for testing
	image_location = os.path.expanduser('~')+"/gisdata/" +image + ".tiff"

	return image_location

def maptopixel( x, y, geotransform ):
    '''Convert map coordinates to pixel coordinates.

    @param x              Input map X coordinate (double)
    @param y              Input map Y coordinate (double)
    @param geotransform    Input geotransform (six doubles)
    @return pX, pY         Output coordinates (two doubles)
    
    assume rotation is 0

    '''
     
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    
    xOffset = int((x - originX) / pixelWidth)
    yOffset = int((y - originY) / pixelHeight)

    return [xOffset, yOffset]  

def area_stats(image, area):
    '''minmax count in a area

    @param image    image (string)
    @param area     [xmin,xmax,ymin,ymax]

    @return     [min, max]
    '''

    # get geotransform
    # get geotransform
    dataset = gdal.Open(image, GA_ReadOnly)
    if dataset is None:
        sys.exit("the open failed: " + image)
    max_x, max_y = dataset.RasterXSize, dataset.RasterYSize
    geotransform = dataset.GetGeoTransform()

    x1,y1 = maptopixel(area[0],area[3],geotransform)
    x2,y2 = maptopixel(area[1],area[2],geotransform)
    #make sure it is in bounds
    if x1<=0:
    	x1 =1
    if y1<=0:
    	y1=0
    if x2>max_x:
    	x2=max_x
    if y2>max_y:
    	y2=max_y

    xsize = x2 - x1
    ysize = y2 - y1
    print ("x1,x2:", x1,x2)
    print ("y1,y2:", y1,y2)
    print ("xsize, ysize:", xsize,ysize)

    # get first band
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray(x1,y1,xsize,ysize)

    minv, maxv = data.min(),data.max()

    print ("minv,maxv:",minv,maxv)

    # close properly the dataset
    data = None
    band = None
    dataset = None

    return [minv,maxv]

def extractminmax(image,extent):
	"""extract minmax in an area"""

	# just for testing
	geotiff = getimagelocation(image)
	#extent passed from Google Map
	#LatLngBounds(southWest,northEast);
	#((30.513851813412785, -127.25), (43.88905749882538, -104.75))
	#bbox[xmin,xmax,ymin,ymax]
	tmpstr = extent.replace("(",'').replace(')','')
	y1,x1,y2,x2 = map(float,tmpstr.split(','))
	bbox=[x1,x2,y1,y2]
	minv,maxv = area_stats(geotiff,bbox)
	mind,maxd = sorted([-1.897155*minv,-1.897155*maxv])
	result = dict(min=str(minv),max=str(maxv),mind=str(mind),maxd=str(maxd))

	return result

def main():
    """ testing """

    image = "uid258_unw"
    extent = "((32.6324815596378, -116.03364562988281), (32.85425614716256, -115.68208312988281))"
    print(extractminmax(image,extent))
    
if __name__ == '__main__':
	main()
