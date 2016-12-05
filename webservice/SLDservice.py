
"""
    SLDservice:
        extractminmax
"""

import os, sys, time, math,json
import socket
import numpy as np
import matplotlib.cm as cm



# gdal import
import gdal
from gdalconst import *

from SLDtool import color_to_hex, plotcolorbar

def getimagelocation(image):
    """return image location"""

    #for debug on vm
    if os.environ.get("FLASK_DEBUG") == "1":
        tiff = os.path.expanduser('~')+"/gisdata/" +image + ".tiff"
        return tiff


    datafolder1 = "/mnt/SGG/quakesim_production/geotiff/"
    datafolder2 = "/mnt/SGG/NAS/QuakeSim/insar/geotiff/"

    #uidxxx_unw
    uid = image.split("_")[0].replace("uid","")
    if int(uid) >= 1000:
        datadir = datafolder1
    else:
        datadir = datafolder2

    tiff = datadir + "uid_" + uid + "/" + "uid" + uid + "_unw.tiff"

    return tiff

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

    @return     [min, max, im_min, im_max]
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
    # get image min max
    # need to be store as file
    stat = band.ComputeStatistics(False)  # set bApproxOk=0
    band.SetStatistics(stat[0], stat[1], stat[2], stat[3])  # useless

    im_min = band.GetMinimum()
    im_max = band.GetMaximum()

    data = band.ReadAsArray(x1,y1,xsize,ysize)

    minv, maxv = data.min(),data.max()

    print ("minv,maxv:",minv,maxv)
    print ("im_minv,im_maxv",im_min,im_max)

    # close properly the dataset
    data = None
    band = None
    dataset = None

    return [minv,maxv, im_min, im_max]

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
    minv,maxv, im_minv, im_maxv = area_stats(geotiff,bbox)
    # area displacement
    vfactor = -1.897155
    mind,maxd = sorted([vfactor*minv,vfactor*maxv])
    minv_s,maxv_s,mind_s,maxd_s= ['{:.3f}'.format(x) for x in [minv,maxv,mind,maxd]]
    # image displacement
    im_mind,im_maxd = sorted([vfactor*im_minv,vfactor*im_maxv])
    im_minv_s,im_maxv_s,im_mind_s,im_maxd_s= ['{:.3f}'.format(x) for x in [im_minv,im_maxv,im_mind,im_maxd]]

    result = dict(min=minv_s,max=maxv_s,mind=mind_s,maxd=maxd_s)
    result.update(dict(image_min=im_minv_s,image_max=im_maxv_s,image_mind=im_mind_s,image_maxd=im_maxd_s))
    result.update(dict(v2dfactor=vfactor))
    result.update(dict(image=image))

    return result

def SLDwriter(image,minmax,theme):
    """write a new SLD based on minmax"""

    vmin,vmax = minmax
    if theme == "default" or theme == "":
        colortheme = "viridis"
    else:
        # e.g. RdYlGn_r
        colortheme = theme

    # need to convert vmin, vmax to real displacement
    # obs = phasesign*phase*waveln/(4.*numpy.pi)
    # wavelength in cm
    wavelength = 23.840355
    # for most data set, phase sign = -1
    phasesign = -1

    disp_1 = phasesign * wavelength * vmin / (4.0 * np.pi)
    disp_2 = phasesign * wavelength * vmax / (4.0 * np.pi)

    vmin_disp = min(disp_1, disp_2)
    vmax_disp = max(disp_1, disp_2)
    # color mapping
    valuestep = 20

    # negative side
    negvalues = np.linspace(vmin, 0.0, valuestep)
    posvalues = np.linspace(0.0, vmax, valuestep)

    # rgb to hex
    cmap = cm.get_cmap(colortheme)

    colorlist = []

    # reversed direction
    if phasesign == -1:
        for entry in negvalues[:-1]:
            # map it to 0.5 ~ 1 in reversed direction
            val_scaled = 0.5 + 0.5 * (abs(entry) - 0.0) / (abs(vmin) - 0.0)
            rgba = cmap(val_scaled)
            colorlist.append([entry, color_to_hex(rgba)])

        # for 0.0 to white
        # may not necessary
        rgba = (1.0, 1.0, 1.0, 1.0)
        # 0.0 is at the middle
        rgba = cmap(0.5)
        colorlist.append([0.0, color_to_hex(rgba)])

        for entry in posvalues[1:]:
            # map it to 0.0 ~ 0.5 in reversed direction
            val_scaled = 0.5 * (vmax - entry) / (vmax - 0.0)
            rgba = cmap(val_scaled)
            colorlist.append([entry, color_to_hex(rgba)])
    
    SLDname = image + "_test"

    sldheader = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <StyledLayerDescriptor version="1.0.0"
        xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
        xmlns="http://www.opengis.net/sld"
        xmlns:ogc="http://www.opengis.net/ogc"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <NamedLayer>
        <Name>Gradient</Name>
        <UserStyle>
          <Title>%s</Title>
          <FeatureTypeStyle>
            <Rule>
              <RasterSymbolizer>
              <ColorMap>"""

    sldfooter = """              </ColorMap>
              </RasterSymbolizer>
            </Rule>
          </FeatureTypeStyle>
        </UserStyle>
      </NamedLayer>
    </StyledLayerDescriptor>"""

    sldheader = sldheader % (SLDname)
    colormapentry = '<ColorMapEntry quantity="%s" color="%s"/>'
    with open(SLDname + ".sld", "w") as f:
        f.write(sldheader + "\n")
        for entry in colorlist:
            value, color = entry
            # <ColorMapEntry quantity="-7.1672" color="#2b83ba"/>
            colorentry = colormapentry % (str(value), color)
            f.write("\t\t" + colorentry + "\n")
        f.write(sldfooter)

    plotcolorbar(SLDname, colortheme, [vmin, vmax], [vmin_disp, vmax_disp])

    # in debug mode, don't copy anything
    if os.environ.get("FLASK_DEBUG") == "1":
        pass
    else:
        cmd = "cp " + image +"* /var/www/html/userslds"
        os.system(cmd)

    # use upload sld directly to geoserver, styles=url is not working at this time
    adminpass =  os.environ.get("Geoserver_Pass")
    # register a style
    cmd = 'curl -v -u admin:%s -XPOST -H "Content-type: text/xml" -d "<style><name>%s</name><filename>%s.sld</filename></style>" http://gw88.iu.xsede.org/geoserver/rest/styles'
    cmd = cmd % (adminpass,SLDname,SLDname)
    os.system(cmd)
    # upload sld file
    cmd ='curl -v -u admin:%s -X PUT -H "Content-type: application/vnd.ogc.sld+xml" -d @%s.sld http://gw88.iu.xsede.org/geoserver/rest/styles/%s'
    cmd = cmd % (adminpass,SLDname,SLDname)
    os.system(cmd)


    result=dict()
    hostname = socket.gethostname()
    result['sld']="http://"+ hostname+ "/userslds/" + SLDname +  ".sld"
    result['kmz']="http://"+ hostname+ "/userslds/" + SLDname +  ".kmz"
    result['style'] = SLDname
    result['image'] = image
    
    return result

def main():
    """ testing """

    image = "uid258_unw"
    extent = "((32.6324815596378, -116.03364562988281), (32.85425614716256, -115.68208312988281))"
    print(extractminmax(image,extent))

    minmax = [-12.4,5.7]
    # an good example (-12.341,5.646)
    SLDwriter(image,minmax,theme="RdYlGn_r")
    
if __name__ == '__main__':
    main()
