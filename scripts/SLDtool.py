
"""tools to generate UAVSAR color theme and legends
    -- generate color themes by linear and histogram methods
    -- generate GeoServer SLD
    -- generate legends in KML
"""

import sys
import os
import argparse
import zipfile
import json
from osgeo import gdal
from osgeo import gdalconst as const
import matplotlib as mpl
import matplotlib.pyplot as plt
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

        # bound may be in the wrong side
        if high_value < 0:
            high_value = vmax * 0.9

        if low_value > 0:
            low_value = vmin * 0.9

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


def plotcolorbar(legendname, colortheme, vminmax, vminmax_disp):
    """plotcolorbar"""

    # Make a figure and axes with dimensions as desired.
    fig = plt.figure(figsize=(2.5, 0.6))
    ax = plt.subplot(111)
    fig.patch.set_alpha(0.85)
    fig.subplots_adjust(left=0.05, bottom=0.25, top=0.7, right=0.95)
    ax.set_title("Displacement (cm)", fontsize=9)
    cmap = plt.get_cmap(colortheme)
    norm = mpl.colors.Normalize(vmin=-1, vmax=1)
    cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
                                norm=norm,
                                ticks=[-1, -0.5,0, 0.5,1],
                                orientation='horizontal')
    vmin,vmax = vminmax
    vmin_disp, vmax_disp = vminmax_disp
    tick_text = ["{:.2f}".format(vmin_disp),"{:.2f}".format(0.5*vmin_disp),0, "{:.2f}".format(0.5*vmax_disp),"{:.2f}".format(vmax_disp)]
    cb.ax.set_xticklabels(tick_text, fontsize=9)
    plt.savefig(legendname + ".png", format="PNG", bbox_inches='tight',pad_inches = 0.05, aspect="auto", transparent=False)

    # close fig to release memory
    plt.close(fig)

    # generate legend KML
    kmlfile = legendname + ".kml"
    kmzfile = legendname + ".kmz"

    kmlstr = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://earth.google.com/kml/2.2">
        <ScreenOverlay>
          <name>%s</name>
          <visibility>1</visibility>
          <Icon>
            <href>%s</href>
          </Icon>
          <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
          <screenXY x="0" y="40" xunits="pixels" yunits="pixels"/>
          <rotationXY x="0" y="0" xunits="fraction" yunits="fraction"/>
          <size x="0" y="0" xunits="fraction" yunits="fraction"/>
        </ScreenOverlay>
    </kml>"""

    kmlstr = kmlstr % (legendname, legendname + ".png")

    # write out kml file
    with open(kmlfile, "w") as f:
        f.write(kmlstr)

    # write out kmz file
    with zipfile.ZipFile(kmzfile, 'w', zipfile.ZIP_DEFLATED) as myzip:
        myzip.write(kmlfile)
        myzip.write(legendname + ".png")
    myzip.close()


def colormapping(geotiffs, method="linear", colortheme="RdYlGn_r"):
    """generate color mapping
        para: geotiff -- list of geotiffs
    """

    # single image mode
    crossflag = False
    if len(geotiffs) > 1:
        crossflag = True

    # color theme name
    if colortheme == "RdYlGn_r":
        colortheme_type = "default"
    else:
        colortheme_type = colortheme

    if method == "linear":
        boundmethod = "percentage"
        alllowbounds = []
        allhighbounds = []
        for geotiff in geotiffs:
            bound = imageinfo(geotiff, boundmethod)[boundmethod]
            alllowbounds.append(bound[0])
            allhighbounds.append(bound[1])
    vmin, vmax = min(alllowbounds), max(allhighbounds)
    print(vmin, vmax)

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
    print(vmin_disp, vmax_disp)

    if crossflag:
        # write out meta data for cross image colormapping
        # shall use a class?
        crossmeta = {}
        # need to generate an unique id
        crossmeta['cross_id'] = "a8349"
        crossmeta['bound'] = [vmin, vmax]
        crossmeta['image_list'] = [os.path.basename(x) for x in geotiffs]

        crossname = "cross_" + crossmeta['cross_id']
        crossmeta['sld'] = crossname + "_" + colortheme_type
        crossmeta['legend'] = crossname + "_" + colortheme_type

        with open(crossname + ".json", "w") as outfile:
            outfile.write(json.dumps(crossmeta, sort_keys=True, indent=4))

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
        rgba = (1.0, 1.0, 1.0, 1.0)
        colorlist.append([0.0, color_to_hex(rgba)])

        for entry in posvalues[1:]:
            # map it to 0.0 ~ 0.5 in reversed direction
            val_scaled = 0.5 * (vmax - entry) / (vmax - 0.0)
            rgba = cmap(val_scaled)
            colorlist.append([entry, color_to_hex(rgba)])

    if phasesign == 1:
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
    if crossflag:
        SLDname = crossmeta['sld']
    else:
        SLDname = os.path.basename(geotiff).split(".")[0]
        SLDname += "_" + colortheme_type

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


def main():
    """testing"""

    parser = argparse.ArgumentParser()
    # add support input of multiple geotiffs
    parser.add_argument("geotiffs", nargs='+', help="geotiff images")
    parser.add_argument("-m", "--method", choices=["linear", "histogram"], default="linear", help="choose an color mapping method")

    args = parser.parse_args()

    colormapping(args.geotiffs, args.method)

if __name__ == '__main__':
    main()
