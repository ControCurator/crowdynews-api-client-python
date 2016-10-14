import controlapi.client as client
import logging
import json

logger = logging.getLogger(__name__)

def get_control(contract_id, client_id, client_secret):
	from frigg.frigg import Frigg
	frigg = Frigg({
		"symbol":"EXT_CONTROCURATOR",
		"clientId":client_id,
		"clientSecret":client_secret,
		"authServerDomain": "https://auth.crowdynews.com",
		"authServerVersion": "v1"
	})
	contract_id = contract_id

	control = client.Control('https://api.crowdynews.com/v1/', frigg, contract_id)
	return control

def get_name(item):
	if item.name() and 'collectionId' in item.data:
		return ' : '.join([item.path,item.data['collectionId'], item.name(), item.id()])
	if item.name():
		return ' : '.join([item.path, item.name(), item.id()])
	else:
		return ' : '.join([item.path, '__no_name__', item.id()])

def print_list(factory):
	names = sorted([get_name(item) for item in factory.list()])
	for name in names:
		print name

def print_collection_inputs(collection, inputs):
	inputs = filter_inputs(collection, inputs)
	for item in inputs:
		print collection.name() + ':' + item.name()

def get_input_uuid(item):
	return ':'.join([item.data['collectionId'], item.name()])

def input_names(collection_id,services,keywords):
	return [
		input_name(collection_id, service, services[service], keyword)
		for keyword in keywords
		for service in services
	]

def input_name(collection_id, service,type,q):
	return ':'.join([collection_id,service,type,q])

def filter_inputs(collection, inputs):
	return [item for item in inputs	if collection.id() == item.data['collectionId']]

def remove_old_inputs(collection, inputs, services, keywords):
	inputs = filter_inputs(collection, inputs)
	names = input_names(collection.id(), services, keywords)
	for item in inputs:
		uuid = get_input_uuid(item)
		if uuid not in names:
			logger.warn('Deleting %s from %s' % (item.name(), collection.id()))
			item.delete()

def create_new_inputs(collection, inputs, services, keywords):
	inputs = filter_inputs(collection, inputs)
	names = [get_input_uuid(item) for item in inputs]
	for keyword in keywords:
		for service in services:
			uuid = input_name(collection.id(), service, services[service], keyword)
			if uuid not in names:
				collection.add_input(service, services[service], keyword)

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser(description='Update topics.')
	parser.add_argument('contract_id', help='The contract identifier')
	parser.add_argument('client_id', help='The auth client identifier')
	parser.add_argument('client_secret', help='The auth client secret')
	parser.add_argument('topics_file', help='The configuration file')

	args = parser.parse_args()
	control = get_control(args.contract_id, args.client_id, args.client_secret)

	ccf = client.CollectionFactory(control)
	cif = client.InputFactory(control)
	flf = client.FilterListFactory(control)
	fsf = client.FilterSetFactory(control)
	fcf = client.FilterChainFactory(control)
	ppf = client.PublicationFactory(control)
	pcf = client.CustomizationFactory(control)

	logger.setLevel(logging.WARN)

	with open(args.topics_file) as f:
		config = json.load(f)

	topics = config['topics']
	services = config['services']
	for topic in topics:
		collection = ccf.find(topic)
		if not collection:
			collection = ccf.create(topic)
		keywords = topics[topic]
		remove_old_inputs(collection, cif.list(), services, keywords)
		create_new_inputs(collection, cif.list(), services, keywords)

	print_list(cif)
	for collection in ccf.list():
		print_collection_inputs(collection, cif.list())
		print collection.data['contentUri']
