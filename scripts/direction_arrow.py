"""generate heading and look icon and kml"""

import matplotlib.pyplot as plt
import math
import zipfile
import os


def generate_screenoverly_kml(overlay_image):
    """ generate and overlay kml """

    # upper right
    overlay_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
    <ScreenOverlay>
      <name>Radar Direction</name>
      <visibility>1</visibility>
      <Icon>
        <href>%s</href>
      </Icon>
      <overlayXY x="1" y="1" xunits="fraction" yunits="fraction"/>
      <screenXY x="5" y="15" xunits="insetPixels" yunits="insetPixels"/>
      <size x="100" y="100" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>
</kml>
    """
    # lower left
    overlay_kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
    <ScreenOverlay>
      <name>Radar Direction</name>
      <visibility>1</visibility>
      <Icon>
        <href>%s</href>
      </Icon>
      <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
      <screenXY x="260" y="40" xunits="pixels" yunits="pixels"/>
      <size x="100" y="100" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>
</kml>
    """

    kml_name = overlay_image.replace("png", "kml")
    overlay_kml = overlay_kml % overlay_image

    with open(kml_name, "w") as f:
        f.write(overlay_kml)
    f.close

    # generate kmz file
    kmz_name = kml_name[:-4]+".kmz"
    with zipfile.ZipFile(kmz_name, "w", zipfile.ZIP_DEFLATED) as myzip:
        myzip.write(kml_name)
        myzip.write(overlay_image)
    myzip.close


def arrow_plot(heading, radar_direction):
    """generate arrow plot by heading and rader_direction"""

    # assume heading is from north
    # center (0,0) radius = 0.5
    ax = plt.axes(aspect="equal")
    ax.set_ylim([-0.6, 0.6])
    ax.set_xlim([-0.6, 0.6])
    # testing code
    real_angle = math.radians(90 - heading)
    head_x = 0.5*math.cos(real_angle)
    head_y = 0.5*math.sin(real_angle)
    org_x = - head_x
    org_y = - head_y
    # draw heading arrow
    ax.arrow(org_x, org_y, 2*head_x, 2*head_y, width=0.01, head_width=0.06, head_length=0.06, fc='k', ec='k')

    # draw look arrow
    if radar_direction.lower() == "left":
        # print("left")
        look_x = 0.5*math.cos(math.pi/2.0 + real_angle)
        look_y = 0.5*math.sin(math.pi/2.0 + real_angle)
    else:
        # print("right")
        look_x = - 0.5*math.cos(math.pi/2.0 + real_angle)
        look_y = - 0.5*math.sin(math.pi/2.0 + real_angle)

    ax.arrow(0.0, 0.0, look_x, look_y, width=0.008, head_width=0.06, head_length=0.06, fc='k', ec='k')
    plt.axis("off")
    img_name = str(int(heading)) + "_" + radar_direction + ".png"
    plt.savefig(img_name, bbox_inches='tight', transparent=True)
    # plt.show()
    plt.close()

    generate_screenoverly_kml(img_name)


def main():
    """ testing programing """

    os.mkdir("direction_kml")
    os.chdir("direction_kml")
    for i in range(-179, 180):
        peg = i
        direction = "left"
        arrow_plot(peg, direction)

if __name__ == "__main__":
    main()
