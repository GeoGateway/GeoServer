
"""tools to generate UAVSAR color theme and legends
    -- generate color themes by linear and histogram methods
    -- generate GeoServer SLD
    -- generate legends in KML
"""

import sys
import os
import argparse
from osgeo import gdal
from osgeo import gdalconst as const
# import matplotlib as mpl
# import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


def imageinfo(image, info):
    """get image infor through gdal"""

    dataset = gdal.Open(image, const.GA_ReadOnly)
    if dataset is None:
        sys.exit("the open failed: " + image)

    # get band information
    band = dataset.GetRasterBand(1)
    # bApproxOk =1 default overview or subset of image is used in computing
    stat = band.ComputeStatistics(False)  # set bApproxOk=0
    band.SetStatistics(stat[0], stat[1], stat[2], stat[3])  # useless
    vmin = band.GetMinimum()
    vmax = band.GetMaximum()

    V = {}
    if info == "minmax":
        V[info] = [vmin, vmax]

    # get percentage on cumulative curve
    if info == "percentage":
        hist = band.GetDefaultHistogram(force=True)

        cnt = 0
        cumsum = 0
        sumtotal = 0
        nbucket = hist[2]
        valuelist = hist[3]
        increment = (vmax - vmin) / nbucket
        value = vmin
        cumhist = []
        # get total to normalize (below)
        sumtotal = sum(valuelist)
        for bucket in valuelist:
            cumsum += bucket
            nsum = cumsum / float(sumtotal)
            cumhist.append([cnt, value, bucket, nsum])
            cnt = cnt + 1
            value = value + increment

        lowbound = 0.002  # 0.5%
        highbound = 0.998  # 99.5%
        for i in range(nbucket):
            if cumhist[i][-1] >= lowbound:
                low_value = cumhist[i][1]
                break
        for i in range(nbucket-1, 0, -1):
            if cumhist[i][-1] <= highbound:
                high_value = cumhist[i][1]
                break

        V[info] = [low_value, high_value]

    # close properly the dataset
    band = None
    dataset = None

    return V


def color_to_hex(rgba):
    """rgba to hex color"""
    r, g, b, a = rgba
    r = int(255*r)
    g = int(255*g)
    b = int(255*b)

    return '#%02X%02X%02X' % (r, g, b)


def colormapping(geotiff, method, colortheme="RdYlGn_r"):
    """generate color mapping"""

    if method == "linear":
        boundmethod = "percentage"
        bound = imageinfo(geotiff, boundmethod)[boundmethod]
    # print(bound)
    vmin, vmax = bound
    # color mapping

    valuestep = 20

    # negative side
    negvalues = np.linspace(vmin, 0.0, valuestep)
    posvalues = np.linspace(0.0, vmax, valuestep)

    # rgb to hex
    cmap = cm.get_cmap(colortheme)

    colorlist = []

    for entry in negvalues[:-1]:
        # map it to 0 ~ 0.5
        val_scaled = 0.5 * (entry - vmin) / (0.0 - vmin)
        rgba = cmap(val_scaled)
        colorlist.append([entry, color_to_hex(rgba)])

    # for 0.0 to white
    rgba = (1.0, 1.0, 1.0, 1.0)
    colorlist.append([0.0, color_to_hex(rgba)])

    for entry in posvalues[1:]:
        # map it to 0.5 ~ 1
        val_scaled = 0.5 + 0.5 * (entry - 0.0) / (vmax - 0.0)
        rgba = cmap(val_scaled)
        colorlist.append([entry, color_to_hex(rgba)])

    # generate GeoServer SLD
    SLDname = os.path.basename(geotiff).split(".")[0]
    if colortheme == "RdYlGn_r":
        SLDname += "_default"
    else:
        SLDname += "_" + colortheme

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


def main():
    """testing"""

    parser = argparse.ArgumentParser()
    parser.add_argument("geotiff", help="geotiff image")
    parser.add_argument("-m", "--method", choices=["linear", "histogram"], default="linear", help="choose an color mapping method")

    args = parser.parse_args()

    colormapping(args.geotiff, args.method)

if __name__ == '__main__':
    main()
