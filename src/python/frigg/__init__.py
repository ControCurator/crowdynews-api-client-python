import os
from subprocess import check_output

def find_all(name, path):
	'''
	Finds all files in current path
	'''
	result = []
	for root, dirs, files in os.walk(path):
		if name in files:
			result.append(os.path.join(root, name))
	return result

def source_file(variables_file, project_folder):
	'''
	Python doesn't deal easily with bash source
	http://stackoverflow.com/questions/7040592/calling-the-source-command-from-subprocess-popen/22086176#22086176
	'''
	variables_file_path = find_all(variables_file, project_folder)
	assert len(variables_file_path) != 0, 'File {} could not be located'.format(variables_file)
	assert len(variables_file_path) == 1, 'Multiple {} files found - ambiguous'.format(variables_file)
	output = check_output('source {}; env -0'.format(variables_file_path[0]), shell=True, \
		executable='/bin/bash')
	os.environ.update(line.partition('=')[::2] for line in output.split('\0'))
	return os.environ

class ProjectVariables(object):
	'''
	Class that sets all the environment variables
	'''
	def source_var_folder(self):
		variables_file = 'project_variables.sh'
		#this is the root folder (<root folder>/src/python)
		project_folder = os.path.dirname('/'.join(os.path.realpath(__file__).split('/')[:-3]))
		return source_file(variables_file, project_folder)

	def __init__(self):
		environ = self.source_var_folder()
		self.name = environ['PROJECT_NAME']
		self.version = environ['VERSION']
		self.title = environ['PROJECT_NAME']
		self.description = 'Python OAuth package.'
		self.uri = 'http://crowdynews.com/'
		self.author = 'Crowdynews'
		self.email = 'developers@crowdynews.com'

#make some fields available directly
def __version__():
	localversion = ProjectVariables()
	return localversion.version
