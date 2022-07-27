#!/usr/bin/env python

from app import app as application

from gevent import monkey
monkey.patch_all()

import sys
import site

# site.addsitedir("/var/www/sso-instrumentation/lib/python3.6/site-packages")
# sys.path.insert(0, "/var/www/sso-instrumentation")

