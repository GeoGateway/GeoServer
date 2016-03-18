
import sys
import socket
from flask import Flask
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


if __name__ == "__main__":

    hostname = socket.gethostname()
    if "MacBook-Air" in hostname:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0')
