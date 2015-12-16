
"""batch register tiff with sytle
"""

import json
import os
import subprocess
import urllib.request


def main():
    """generate copy list"""

    # geojson output from UAVSAR search API
    jsonfile = "uavsar_ca.geojson"

    with open(jsonfile, "r") as f:
        data = json.loads(f.read())

    datafolder1 = "/mnt/SGG/password_production/geotiff/"
    datafolder2 = "/mnt/SGG/NAS/password/insar/geotiff/"
    datafolder3 = "/home/geogateway/geotiff/"
    for item in data:
        uid = item['uid']

        tiff = ""
        if int(uid) >= 1000:
            datadir = datafolder1
        else:
            if int(uid) <= 117:
                datadir = datafolder3
            else:
                datadir = datafolder2

        tiff += "uid_" + uid + "/" + "uid" + uid + "_unw.tiff"
        if int(uid) <= 117:
            tiff = "uid" + uid + "_unw.tiff"
        layername = "uid" + uid + "_unw"

        print("register", tiff)

        geoserver = "http://127.0.0.1:8080/geoserver/InSAR/wms?version=1.1.1&request=DescribeLayer&outputFormat=application/json&exceptions=application/json"
        queryurl = geoserver + "&layers="+"InSAR:"+layername
        with urllib.request.urlopen(queryurl) as x:
                rawtext = x.read().decode('utf8')
        x.close
        # response = urllib2.urlopen(queryurl)
        # json_output = response.read()
        json_output = rawtext

        if "exceptions" in json_output:
            # not registered
            tiff = datadir + tiff
            coverage = layername
            print(tiff, coverage)
            cmd = "curl -u admin:password -v -XPOST -H 'Content-type: application/xml' -d '<coverageStore> <name>" + coverage + "</name><workspace>InSAR</workspace><enabled>true</enabled><type>GeoTIFF</type></coverageStore>' \"http://127.0.0.1:8080/geoserver/rest/workspaces/InSAR/coveragestores\""
            #print(cmd)
            subprocess.call(cmd, shell=True)
            cmd = "curl -u admin:password -v -XPUT -H 'Content-type: text/plain' -d 'file:" + tiff + "' \"http://127.0.0.1:8080/geoserver/rest/workspaces/InSAR/coveragestores/" + coverage + "/external.geotiff?configure=first\&coverageName=" + coverage + "\""
            #print(cmd)
            subprocess.call(cmd, shell=True)

            # change defualt style
            defaultstyle = layername + "_default"
            cmd = 'curl -v -u admin:password -XPUT -H "Content-type: text/xml" -d "<layer><defaultStyle><name>InSAR:%s</name></defaultStyle></layer>" http://127.0.0.1:8080/geoserver/rest/layers/InSAR:%s'
            cmd = cmd % (defaultstyle, coverage)
            #print(cmd)
            subprocess.call(cmd, shell=True)
        else:
            print("already registered: ", uid)
            continue


if __name__ == '__main__':
    main()
