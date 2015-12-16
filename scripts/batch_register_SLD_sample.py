
"""batch register a folder of SLDs
"""

import os

SLDfolder = "/home/geogateway/SLDs/"
sytlesfolder = "/home/geogateway/geoserver-2.8.1/data_dir/workspaces/InSAR/styles"

for sld in os.listdir(SLDfolder):
    if sld[-3:] == "sld":
        # copy it to style folder
        cmd = "cp " + SLDfolder + sld + " " + sytlesfolder
        print(cmd)
        # os.system(cmd)
        cmd = 'curl -v -u admin:password -XPOST -H "Content-type: text/xml" -d "<style><name>%s</name><workspace>InSAR</workspace><filename>%s</filename></style>" http://127.0.0.1:8080/geoserver/rest/styles'
        cmd = cmd % (sld[:-4], sld)
        print(cmd)
        # os.system(cmd)
