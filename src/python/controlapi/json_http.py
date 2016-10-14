import urllib2
import json
import requests

import logging

logger = logging.getLogger(__name__)

def handleException(r, e):
	raise e

def get(url, data=None):
	r = None
	try:
		logger.info(url)
		r = requests.get(url, params=data)
		return r.json()
	except Exception as e:
		handleException(r, e)

def post(url, data=None):
	r = None
	try:
		logger.info(url)
		r = requests.post(url, json=data)
		return r.json()
	except Exception as e:
		handleException(r, e)

def patch(url, data=None):
	r = None
	try:
		logger.info(url)
		r = requests.patch(url, json=data)
		return r.json()
	except Exception as e:
		handleException(r, e)

def delete(url, data=None):
	r = None
	try:
		logger.info(url)
		r = requests.delete(url, json=data)
		return r.json()
	except Exception as e:
		handleException(r, e)

