#!/usr/bin/python
"""
Run a handful of client commands.
"""

from empire import Empire

import sys

appkey = sys.argv[1]
secrets_yaml = "empire_service_secrets.yaml"

empire = Empire(appkey=appkey, enduser="enduser handle", secrets_yaml=secrets_yaml)

empire.walkthrough()
