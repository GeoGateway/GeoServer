"""
	wsgi.py
		-- run as flask wrapper as wsgi application
		-- run as non-root user: ~/miniconda3/bin/mod_wsgi-express start-server wsgi.py &
"""

from server_debug import app as application
