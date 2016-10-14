import logging
import json
import urllib

import controlapi.json_http as http

logger = logging.getLogger(__name__)

base_url = 'https://api.crowdynews.com/v1/'

def slugify(s):
	return urllib.quote(s)


class Control(object):
	def __init__(self, base_url, frigg, contract_id):
		self._base_url = base_url
		self._frigg = frigg
		self._contract_id = contract_id

	def token(self):
		return self._frigg.token()

	def contract_id(self):
		return self._contract_id

	def url(self, path, i=None):
		url = self._base_url + path
		if i:
			url += '/' + i
		url += '?access_token=' + self.token() + '&contract_id=' + self._contract_id
		return url

	def get(self, path):
		url = self.url(path)
		logger.info('url  %s' % url)
		resp = http.get(url)
		logger.debug('resp %s' % json.dumps(resp, indent=2))
		return resp

	def post(self, path, data):
		url = self.url(path)
		logger.info('url  %s' % url)
		logger.debug('data %s' % json.dumps(data, indent=2))
		resp = http.post(url, data)
		logger.debug('resp %s' % json.dumps(resp, indent=2))
		return resp

	def patch(self, path, data):
		url = self.url(path)
		logger.info('url  %s' % url)
		logger.debug('data %s' % json.dumps(data, indent=2))
		resp = http.patch(url, data)
		logger.debug('resp %s' % json.dumps(resp, indent=2))
		return resp

	def delete(self, path, data):
		url = self.url(path)
		logger.info('url  %s' % url)
		logger.debug('data %s' % json.dumps(data, indent=2))
		try:
			resp = http.delete(url, data)
		except ValueError as e:
			return data

#		logger.debug('resp %s' % json.dumps(resp, indent=2))
#		return resp

	def list(self, path, cp):
		resp = self.get(path)
		ret = []
		for item in resp:
			ret.append(cp(self, item))
		return ret


class Factory(object):
	def __init__(self, path, klass, control):
		self.control = control
		self.path = path
		self.klass = klass

	def list(self):
		return self.control.list(self.path, self.klass)

	def find(self, name):
		for item in self.list():
			if item.name() == name:
				return item
		return None

	def delete_by_name(self, name):
		item = self.find(name)
		if item:
			item.delete()
		return item

	def create(self, data):
		return self.klass(self.control, self.control.post(self.path, data))

	def create_list(self, data):
		ret = []
		for item in data:
			ret.append(self.klass(self.control, self.control.post(self.path, data)))
		return ret


class ControlableObject(object):
	def __init__(self, path, control, data):
		self.control = control
		self.data = data
		self.path = path

	def id(self):
		return self.data['_id']

	def name(self):
		if 'name' in self.data:
			return self.data['name']
		return None

	def get(self):
		self.data = self.control.get(self.path + '/' + self.id())
		return self.data

	def patch(self):
		return self.control.patch(self.path + '/' + self.id(), self.data)

	def delete(self):
		data = {'ids':[self.id()]}
		return self.control.delete(self.path, data)





class CollectionFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'collection/collections', Collection, control)

	def create(self, name):
		data = {
			"name":name,
			"slug":slugify(name),
			"type": "breakingburner",
			"contractId":self.control.contract_id(),
#			"queueDataUri":"http://queue.crowdynews.com/some/content/location",
#			"queueModerateUri":"http://queue.crowdynews.com/some/moderation/location",
#			"contentUri":"http://queue.crowdynews.com/some/content/location",
			"active": True
		}
	#		"filterId":filter_id,
		return super(CollectionFactory, self).create(data)


class InputFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'collection/inputs', Input, control)

	def create(self, collection, service, type, input):
		data = {
			"collectionId": collection.id(),
			"contractId": self.control.contract_id(),
			"service": service,
			"type": type,
			"input": input,
			"display": True,
			"active": True
		}
		return super(InputFactory, self).create(data)


class PublicationFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'publication/publications', Publication, control)

	def create(self, collection, name, definition_id):
		data = {
			"contractId": self.control.contract_id(),
			"name": name,
			"description": name,
			"definitionId": definition_id,
			"properties": {
				"width": "200px",
				"height": "200px"
			},
			"output":
			[
				{
					"collectionId": collection.id(),
					"label": name,
					"preCondition": "function () { return true }",
					"urlParameters": {
						"type": "image",
						"service": "twitter"
					},
					"active": True
				}
			]
		}
		return super(PublicationFactory, self).create(data)


class CustomizationFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'publication/customizations', Customization, control)

	def create(self, name, script):
		data = {
			"contractId": self.control.contract_id(),
			"name": name,
			"description": name,
			"version": 1,
			"type": "js",
			"data": script
		}
		return super(CustomizationFactory, self).create(data)


class FilterChainFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'filter/chains', FilterChain, control)

	def create(self, name, sets):
		data = {
			"name": name,
			"contractId": self.control.contract_id(),
			"sets": [],
			"active": True
		}
		data['sets'] = [i.id() for i in sets]
		return super(FilterChainFactory, self).create(data)


class FilterListFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'filter/lists', FilterList, control)

	def create(self, name, items, type='strings'):
		data = {
			"name": name,
			"contractId": self.control.contract_id(),
			"type": type,
			"entries": [items],
			"active": True
		}
		return super(FilterListFactory, self).create(data)


class FilterSetFactory(Factory):
	def __init__(self, control):
		Factory.__init__(self, 'filter/sets', FilterSet, control)

	def create_raw(self, data):
#		for item in data:
#			item['contractId'] = self.control.contract_id(),
		return super(FilterSetFactory, self).create_list(data)

	def create(self, name, precondition, rules):
		data = [
			{
				"name": name,
				"contractId": self.control.contract_id(),
				"preCondition": precondition,
				"rules": rules,
				"active": True
			}
		]
		return super(FilterSetFactory, self).create_list(data)

	def create_condition(self, field, operator, value, negate=False):
		return {
			"operator": operator,
			"field": field,
			"value": value,
			"not": negate
		}
'''
class Operator(Enum):
	eq: 'equals'
	pattern: 'pattern'
	gt: 'gt'
	gte: 'gte'
	lt: 'lt'
	lte: 'lte'
	in: 'in'
	patternin: 'patternin',
	datediff: 'datediff'
'''



class Collection(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'collection/collections', control, data)

	def set_filter(filter):
		self.data['filterId'] = filter.id()
		self.patch()

	def add_input(self, service, taip, query):
		return InputFactory(self.control).create(self, service, taip, query)

	def create_publication(self, name, description):
		return PublicationFactory(self.control).create(self, name)


class Input(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'collection/inputs', control, data)

	def name(self):
		d = self.data
		return d['service'] + ':' + d['type'] + ':' + d['input']

class Publication(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'publication/publications', control, data)


class Customization(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'publication/customizations', control, data)


class FilterChain(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'filter/chains', control, data)


class FilterSet(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'filter/sets', control, data)


class FilterList(ControlableObject):
	def __init__(self, control, data):
		ControlableObject.__init__(self, 'filter/lists', control, data)

	def add(self, string):
		self.data['entries'].append(string)
		self.patch()
