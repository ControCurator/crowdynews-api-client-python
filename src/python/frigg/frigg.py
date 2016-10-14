 #!/usr/bin/env python

import requests
import urllib
import base64
import datetime
import logging
import copy

from dateutil.parser import parse

# pylint: disable=old-style-class
# pylint: disable=invalid-name

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)

class HTTPException(Exception):
	def __init__(self, status_code, uri, data=None, headers=None, response=None):
		Exception.__init__(self, str(status_code) + ' on ' + uri)
		self.status_code = status_code
		self.uri = uri
		self.data = data
		self.headers = headers
		self.response = response


class Frigg:

	# pylint: disable=too-many-instance-attributes
	# Eight is reasonable in this case.

	def __init__(self, configuration):
		"""
		Initialize frigg with credentials and the Authorization Server domain.

		Optionally the Authorization Server version, access token expiration
		offset and recursion limit safeguard can be provided.
		"""
		configuration = copy.deepcopy(configuration)
		_logger.warn(configuration)
		mandatory_keys = ['clientId', 'clientSecret', 'authServerDomain']
		missing_keys = list(set(mandatory_keys) - set(configuration.keys()))
		if missing_keys:
			raise Exception('Missing keys %s' % missing_keys)

		if not 'authServerVersion' in configuration:
			configuration['authServerVersion'] = 'v1'
		if not 'expirationOffset' in configuration:
			configuration['expirationOffset'] = datetime.timedelta(minutes=5)
		else:
			configuration['expirationOffset'] = datetime.timedelta(milliseconds=configuration['expirationOffset'])

		if not 'recursionLimit' in configuration:
			configuration['recursionLimit'] = 3

		self._client_id = configuration['clientId']
		self._client_secret = configuration['clientSecret']
		self._auth_server_uri = configuration['authServerDomain'] + '/' + configuration['authServerVersion']
		self._expiration_offset = configuration['expirationOffset']
		self._retry_limit = configuration['recursionLimit']

		self._access_token = None
		self._refresh_token = None
		self._expires = None


	def token(self):
		"""
		Obtains an access token on behalf of an OAuth Consumer identified by
		the previously initialized credentials.
		"""
		if not self._access_token:
			self._request()
		if not self._token_expires_within_offset():
			return self._access_token

		self._refresh()
		return self._access_token


	def ttl(self):
		"""
		Retrieves the time to live timestamp that denotes in how many
		milliseconds the access token will expire.
		"""
		if not self._expires:
			raise Exception('No expires set')
		return self._expires - datetime.datetime.now()


	def _request(self):
		"""
		Requests an access/refresh token pair from the Authorization Server via
		the request utility.
		"""
		result = self._token_post_request({
			'grant_type': 'client_credentials'
		})
		self._handle_token_response(result)


	def _refresh(self):
		"""
		Refreshes an access/refresh token pair from the Authorization Server via
		the request utility.
		 """
		options = {
			'grant_type': 'refresh_token',
			'refresh_token': self._refresh_token
		}
		try:
			result = self._token_post_request(options)
			self._handle_token_response(result)
		except HTTPException as e:
			_logger.exception(e)
			if e.status_code == 400:
				self._request()


	def _token_post_request(self, payload):
		"""
		Generates an http request, required when fetching and
		refreshing an access token.

		Note that these request options are specific for requesting/resfreshing
		tokens only. The request to fetch access token expiration info has
		unique request options.
		"""
		uri = self._auth_server_uri + '/oauth/token'
		headers = {
			'Authorization': 'Basic ' + self._encode_credentials()
		}
		response = requests.post(uri, data=payload, headers=headers)
		if response.status_code != 200:
			_logger.error(response)
			raise HTTPException(response.status_code, uri, data=payload, headers=headers, response=response)
		return response.json()


	def _handle_token_response(self, data):
		"""
		Returns an request handler that handles the http request made when
		requesting or refreshing tokens.

		Note that this handler is only used when requesting/refreshing tokens.
		"""
		if not data:
			raise Exception('no data provided')
		if not 'access_token' in data:
			raise Exception('Failed to get access token.')
		if not 'refresh_token' in data:
			raise Exception('Failed to get refresh token.')

		self._access_token = data['access_token']
		self._refresh_token = data['refresh_token']
		self._get_info()


	def _request_token_info(self):
		"""
		Requests the expiration info of an access token.
		"""
		uri = self._auth_server_uri + '/oauth/token/info'
		payload = {
			'access_token': self._access_token
		}
		headers = {
			'Authorization': 'Basic ' + self._encode_credentials()
		}
		try:
			response = requests.get(uri, data=payload, headers=headers)
		except requests.Timeout:
			raise Exception('Server timed out')
		if response.status_code != 200:
			_logger.error(response)
			raise Exception('Server did not respond as expected. HTTP status code %s' % response.status_code)
		return response.json()


	def _get_info(self):
		info = self._request_token_info()
		if not 'ttl' in info:
			raise Exception('Token has no ttl.')
		self._expires = datetime.datetime.now() + datetime.timedelta(milliseconds=info['ttl'])


	def _token_expires_within_offset(self):
		"""
		Determines if the access token expires within the specified expiration
		offset.
		"""
		return self.ttl() < self._expiration_offset


	def _encode_credentials(self):
		"""
		Encode the OAuth consumer credentials to generate an
		authorization header when fetching and refreshing
		tokens.

		return Object base64
		"""
		encoded = urllib.quote(self._client_id) + ':' + \
			urllib.quote(self._client_secret)

		return base64.b64encode(encoded)


	def __str__(self):
		return \
			'\nAccess:' + self._access_token + \
			'\nRefresh:' + self._refresh_token + \
			'\nExpires:' + str(self._expires)
