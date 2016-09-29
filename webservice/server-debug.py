
"""
    simple test code, only for internal testing

    how to run:
        in miniconda: conda install flask

        $export FLASK_APP=server-debug.py
        $python35 -m flask run

        http://localhost:5000/test
"""

import sys
import socket
import json
from flask import Flask
from flask import request

#import functioning code
from SLDservice import extractminmax,SLDwriter


app = Flask(__name__)

@app.route("/")
def index():
    return socket.gethostname()

"""test service is running"""
@app.route("/test")
def test():
    info={}
    info["python"] = sys.version
    info["runningmode"] = app.debug
    return info["python"] + str(info["runningmode"])

"""insar tool set"""
@app.route("/insar")
def insar():
    info={}
    info['extracminmax'] = extractminmax.__doc__

    return info['extracminmax']

"""extract minmax services"""
@app.route("/insar/getminmax")
def getminmax():
    """extract minmax from a image defined by a bbox"""

    if 'extent' in request.args:
        extent = request.args['extent']
    else:
        return "extent is missing"

    if 'image' in request.args:
        image = request.args['image']
    else:
        return "image is missing"

    if 'callback' in request.args:
        callback = request.args['callback']
    
    result = extractminmax(image,extent)

    return callback + "("+json.dumps(result) +")"

"""generate a new SLD"""
@app.route("/insar/sldgenerator")
def sldgenerator():
    """generate a new SLD for image with min,max"""

    if 'image' in request.args:
        image = request.args['image']
    else:
        return "image is missing"

    if 'min' in request.args:
        minv = request.args['min']
    else:
        return "min is missing"

    if 'max' in request.args:
        maxv = request.args['max']
    else:
        return "max is missing"

    if 'callback' in request.args:
        callback = request.args['callback']

    result = SLDwriter(image,[float(minv),float(maxv)])

    return callback + "("+json.dumps(result) +")"

if __name__ == "__main__":

    hostname = socket.gethostname()
    if "MacBook-Air" in hostname:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0')
