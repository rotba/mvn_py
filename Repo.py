import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from shutil import copyfile
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
import re
import TestObjects
import mvn
from jcov_parser import JcovParser
from jcov_tracer import JcovTracer
from junitparser.junitparser import Error, Failure
from plugins.evosuite.evosuite import EvosuiteFactory, TestGenerationStrategy, EVOSUITE_SUREFIRE_VERSION, EVOSUITE_JAVA_VER
from pom_file import Pom


class TestResult(object):
	def __init__(self, junit_test):
		self.junit_test = junit_test
		self.classname = junit_test.classname
		self.name = junit_test.name
		self.full_name = "{classname}.{name}".format(classname=self.classname, name=self.name).lower()
		result = 'pass'
		if type(junit_test.result) is Error:
			result = 'error'
		if type(junit_test.result) is Failure:
			result = 'failure'
		self.outcome = result

	def __repr__(self):
		return "{full_name}: {outcome}".format(full_name=self.full_name, outcome=self.outcome)

	def is_passed(self):
		return self.outcome == 'pass'

	def get_observation(self):
		return 0 if self.is_passed() else 1

	def as_dict(self):
		return {'_tast_name': self.full_name, '_outcome': self.outcome}


class Repo(object):

	def __init__(self, repo_dir):
		self._repo_dir = repo_dir
		self.DEFAULT_ES_VERSION = '1.0.6'
		self.DEFAULT_SUREFIRE_VERSION = '2.17'
		self.DEFAULT_JUNIT_VERSION = '4.12'
		self.DEFAULT_XERCES_VERSION = '2.11.0'
		self.MAVEN_COMPILER_SOURCE = None

	@property
	def repo_dir(self):
		return self._repo_dir

	# Executes mvn test
	def install(self, module=None, testcases=[], time_limit=sys.maxint, debug=False):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		install_cmd = self.generate_mvn_install_cmd(module=inspected_module, testcases=testcases, debug=debug)
		build_report = mvn.wrap_mvn_cmd(install_cmd, time_limit=time_limit, dir=self._repo_dir)
		return build_report

	# Executes mvn test
	def test(self, module=None, tests=[], time_limit=sys.maxint):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		test_cmd = self.generate_mvn_test_cmd(module=inspected_module, tests=tests)
		build_report = mvn.wrap_mvn_cmd(test_cmd, time_limit=time_limit)
		return build_report

	# Generates tests. As for now implemented with evosuite
	def generate_tests(self, module=None, classes=[], time_limit=sys.maxint, strategy=TestGenerationStrategy.MAVEN):
		return EvosuiteFactory.create(self, strategy).generate(module, classes, time_limit)

	# Executes mvn clean
	def clean(self, module=None):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		test_cmd = self.generate_mvn_clean_cmd(inspected_module)
		build_report = mvn.wrap_mvn_cmd(test_cmd)
		return build_report

	# Executes mvn compile
	def test_compile(self, module=None):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		test_cmd = self.generate_mvn_test_compile_cmd(inspected_module)
		build_report = mvn.wrap_mvn_cmd(test_cmd)
		return build_report

	# Executes mvn compile
	def compile(self, module=None):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		test_cmd = self.generate_mvn_compile_cmd(inspected_module)
		build_report = mvn.wrap_mvn_cmd(test_cmd)
		return build_report

	def config_for_evosuite(self, module):
		self.change_surefire_ver(EVOSUITE_SUREFIRE_VERSION)
		self.config_compiler_java_home(java_home=mvn.get_jdk_dir(java_ver=EVOSUITE_JAVA_VER),module=module, java_ver=EVOSUITE_JAVA_VER)

	def config(self, module=None):
		inspected_module = module if module is not None else self.repo_dir
		self.config_compiler(inspected_module)

	def config_compiler(self, module):
		java_home = self.infer_java_home_dir(module)
		if java_home == None:
			return
		self.config_compiler_java_home(java_home, module)

	def config_compiler_java_home(self, java_home, module, java_ver= None):
		self.set_pom_tag(
			xquery=reduce(lambda acc, curr: acc + '/' + curr, ['.', 'properties', 'JAVA_HOME']),
			create_if_not_exist=True, module=module, value=java_home
		)
		self.add_plugin(
			artifactId='maven-compiler-plugin', groupId='org.apache.maven.plugins', version='3.1', module=module
		)
		compiler_configuration_query = reduce(
			lambda acc, curr: acc + '/' + curr,
			['.', 'build', 'plugins', "plugin[artifactId = '{}']".format('maven-compiler-plugin'), 'configuration']
		)
		self.set_pom_tag(
			xquery='/'.join([compiler_configuration_query, 'verbose']), create_if_not_exist=True, module=module,
			value='true'
		)
		self.set_pom_tag(
			xquery='/'.join([compiler_configuration_query, 'fork']), create_if_not_exist=True, module=module,
			value='true'
		)
		self.set_pom_tag(
			xquery='/'.join([compiler_configuration_query, 'executable']), create_if_not_exist=True, module=module,
			value='${JAVA_HOME}/bin/javac'
		)
		self.set_pom_tag(
			xquery='/'.join([compiler_configuration_query, 'compilerVersion']), create_if_not_exist=True, module=module,
			value='1.3'
		)
		self.set_pom_tag(
			xquery='/'.join([compiler_configuration_query, 'source']), create_if_not_exist=True, module=module,
			value=self.evaluate_compiler_source(module=module) if java_ver is None else java_ver
		)
		self.set_pom_tag(
			xquery='/'.join([compiler_configuration_query, 'target']), create_if_not_exist=True, module=module,
			value=self.evaluate_compiler_source(module=module) if java_ver is None else java_ver
		)

	def infer_java_home_dir(self, module):
		if self.evaluate_compiler_source(module=module) == '1.8': return  None
		return mvn.get_jdk_dir(
			java_ver=self.evaluate_compiler_source(module=module)
		)

	def evaluate_compiler_source(self, module):
		if self.MAVEN_COMPILER_SOURCE != None: return  self.MAVEN_COMPILER_SOURCE
		self.MAVEN_COMPILER_SOURCE=self.help_evaluate(expression='maven.compiler.source', module=module)
		if self.MAVEN_COMPILER_SOURCE != 'null object or invalid expression': return self.MAVEN_COMPILER_SOURCE
		self.MAVEN_COMPILER_SOURCE = self.help_evaluate(expression='maven.compile.source', module=module)
		return self.MAVEN_COMPILER_SOURCE

	def help_evaluate(self, expression, module):
		cmd = self.generate_mvn_help_evaluate_cmd(expression=expression, module=module)
		return mvn.wrap_mvn_cmd(cmd).strip('\n')

	# Executes mvn evosuite_clean
	def evosuite_clean(self, module=None):
		inspected_module = self.repo_dir if module == None else module
		clean_cmd = self.generate_mvn_evosuite_clean_cmd(inspected_module)
		build_report = mvn.wrap_mvn_cmd(clean_cmd)
		return build_report

	def get_test_results(self):
		from junitparser import JUnitXml
		from junitparser.junitparser import Error, Failure
		SURFIRE_DIR_NAME = 'surefire-reports'

		def get_surefire_files():
			surefire_files = []
			for root, _, files in os.walk(self._repo_dir):
				for name in files:
					if name.endswith('.xml') and os.path.basename(root) == SURFIRE_DIR_NAME:
						surefire_files.append(os.path.join(root, name))
			return surefire_files

	def too_much_testcases_to_generate_cmd(self, testcases, module):
		return len(self.generate_mvn_test_cmd(tests=testcases, module=module)) > mvn.CMD_MAX_LENGTH

	def has_weird_error_report(self, build_report):
		WEIRD_ERROR_STRING = 'was cached in the local repository, resolution will not be reattempted'
		WEIRD_ERROR_STRING_2 = 'Could not resolve dependencies for project'
		WEIRD_ERROR_PATTERN = 'Failure to find .* in http://repository.apache.org/snapshots'
		WEIRD_ERROR_PATTERN_2 = 'Could not find artifact .* in apache.snapshots (http://repository.apache.org/snapshots)'
		return WEIRD_ERROR_STRING in build_report or re.search(WEIRD_ERROR_PATTERN, build_report) != None or re.search(
			WEIRD_ERROR_PATTERN_2, build_report) != None or WEIRD_ERROR_STRING_2 in build_report

	def has_license_error_report(self, build_report):
		ERROR_STRING = 'Too many files with unapproved license:'
		return ERROR_STRING in build_report

		class Test(object):
			def __init__(self, junit_test):
				self.junit_test = junit_test
				self.classname = junit_test.classname
				self.name = junit_test.name
				self.full_name = "{classname}@{name}".format(classname=self.classname, name=self.name).lower()
				result = 'pass'
				if type(junit_test.result) is Error:
					result = 'error'
				if type(junit_test.result) is Failure:
					result = 'failure'
				self.outcome = result

			def __repr__(self):
				return "{full_name}: {outcome}".format(full_name=self.full_name, outcome=self.outcome)

			def is_passed(self):
				return self.outcome == 'pass'

			def get_observation(self):
				return 0 if self.is_passed() else 1

			def as_dict(self):
				return {'_tast_name': self.full_name, '_outcome': self.outcome}

		outcomes = {}
		for report in get_surefire_files():
			try:
				for case in JUnitXml.fromfile(report):
					test = Test(case)
					outcomes[test.full_name] = test
			except:
				pass
		return outcomes

	# Returns tests reports objects currently exists in this repo in path_to_reports
	def parse_tests_reports(self, path_to_reports, module=None):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		ans = []
		for filename in os.listdir(path_to_reports):
			if filename.endswith(".xml"):
				ans.append(TestObjects.TestClassReport(os.path.join(path_to_reports, filename), inspected_module))
		return ans

	# Gets path to tests object in repo, or in a cpsecifc module if specified
	def get_tests(self, module=None):
		ans = []
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		if os.path.isdir(inspected_module + '\\src\\test'):
			if os.path.isdir(inspected_module + '\\src\\test\\java'):
				ans.extend(mvn.parse_tests(inspected_module + '\\src\\test\\java'))
			else:
				ans.extend(mvn.parse_tests(inspected_module + '\\src\\test'))
		for filename in os.listdir(inspected_module):
			file_abs_path = os.path.join(inspected_module, filename)
			if os.path.isdir(file_abs_path):
				if not (filename == 'src' or filename == '.git'):
					ans.extend(self.get_tests(file_abs_path))
		return ans

	# Gets all the reports in the given module if given, else in the given module
	def get_tests_reports(self, module=None):
		ans = []
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		path_to_reports = os.path.join(inspected_module, 'target\\surefire-reports')
		if os.path.isdir(path_to_reports):
			ans.extend(self.parse_tests_reports(path_to_reports, inspected_module))
		for filename in os.listdir(inspected_module):
			file_abs_path = os.path.join(inspected_module, filename)
			if os.path.isdir(file_abs_path):
				if not (filename == 'src' or filename == '.git'):
					ans.extend(self.get_tests_reports(file_abs_path))
		return ans

	# Adds Tracer agent to surefire. Outpur of tracer goes to target
	def setup_tracer(self, target=None):
		agent_path_src = os.path.join(mvn.tracer_dir, r'target\uber-tracer-1.0.1-SNAPSHOT.jar')
		if not os.path.isfile(agent_path_src):
			os.system('mvn install -f {}'.format(mvn.tracer_dir))
		agent_path_dst = os.path.join(self.repo_dir, 'agent.jar')
		paths_path = os.path.join(self.repo_dir, 'paths.txt')
		copyfile(agent_path_src, agent_path_dst)
		with open(paths_path, 'w+') as paths:
			paths.write(Repo.get_mvn_repo() + '\n')
			paths.write(self.repo_dir)
		self.add_argline_to_surefire('-javaagent:{}={}'.format(agent_path_dst, paths_path))

	@staticmethod
	def get_mvn_repo():
		return os.path.join(os.environ['USERPROFILE'], '.m2\\repository')

	def setup_jcov_tracer(self, path_to_classes_file=None, path_to_out_template=None, target_dir=None, class_path=None,
	                      instrument_only_methods=True):
		result_file = "result.xml"
		if target_dir:
			result_file = os.path.join(target_dir, result_file)
		jcov = JcovTracer(self.repo_dir, path_to_out_template, path_to_classes_file, result_file, class_path=class_path,
		                  instrument_only_methods=instrument_only_methods)
		for pom_file in self.get_all_pom_paths(self._repo_dir):
			pom = Pom(pom_file)
			for value in jcov.get_values_to_add():
				pom.add_pom_value(value)
		return jcov

	def run_under_jcov(self, target_dir, debug=False, instrument_only_methods=True):
		self.test_compile()
		f, path_to_classes_file = tempfile.mkstemp()
		os.close(f)
		f, path_to_template = tempfile.mkstemp()
		os.close(f)
		os.remove(path_to_template)
		jcov = self.setup_jcov_tracer(path_to_classes_file, path_to_template, target_dir=target_dir,
		                              class_path=Repo.get_mvn_repo(), instrument_only_methods=instrument_only_methods)
		jcov.execute_jcov_process()
		self.install(debug=debug)
		jcov.stop_grabber()
		os.remove(path_to_classes_file)
		os.remove(path_to_template)
		return JcovParser(target_dir).parse()

	# Changes all the pom files in a module recursively
	def get_all_pom_paths(self, module=None):
		ans = []
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		if os.path.isfile(os.path.join(inspected_module, 'pom.xml')):
			ans.append(os.path.join(inspected_module, 'pom.xml'))
		for file in os.listdir(inspected_module):
			full_path = os.path.join(inspected_module, file)
			if os.path.isdir(full_path):
				ans.extend(self.get_all_pom_paths(full_path))
		return ans

	# Changes surefire version in a pom
	def change_surefire_ver(self, version, module=None):
		ans = []
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		poms = self.get_all_pom_paths(inspected_module)
		new_file_lines = []
		for pom in poms:
			xmlFile = parse(pom)
			tmp_build_list = xmlFile.getElementsByTagName('build')
			build_list = list(
				filter(lambda b: not b.parentNode == None and b.parentNode.localName == 'project', tmp_build_list))
			if len(build_list) == 0:
				continue
			assert len(build_list) == 1
			plugins_tags = build_list[0].getElementsByTagName('plugins')
			if len(plugins_tags) == 0:
				continue
			for plugins_tag in plugins_tags:
				if plugins_tag.parentNode.localName == 'build':
					artifacts_ids = list(
						map(lambda a: str(a.firstChild.data), plugins_tag.getElementsByTagName('artifactId')))
					if not any(a_id == 'maven-surefire-plugin' for a_id in artifacts_ids):
						new_plugin = plugins_tag.ownerDocument.createElement(tagName='plugin')
						new_group_id = new_plugin.ownerDocument.createElement(tagName='groupId')
						new_artifact_id = new_plugin.ownerDocument.createElement(tagName='artifactId')
						new_group_id_text = new_group_id.ownerDocument.createTextNode('org.apache.maven.plugins')
						new_artifact_id_text = new_artifact_id.ownerDocument.createTextNode('maven-surefire-plugin')
						new_group_id.appendChild(new_group_id_text)
						new_plugin.appendChild(new_group_id)
						new_artifact_id.appendChild(new_artifact_id_text)
						new_plugin.appendChild(new_artifact_id)
						plugins_tag.appendChild(new_plugin)
			for plugins_tag in plugins_tags:
				mvn.change_plugin_version_if_exists(plugins_tag, 'maven-surefire-plugin', version)
			os.remove(pom)
			with open(pom, 'w+') as f:
				tmp_str = xmlFile.toprettyxml()
				copy_tmp_str = ''
				for char in tmp_str[::]:
					if 125 < ord(char):
						copy_tmp_str += 'X'
					else:
						copy_tmp_str += char
				lines = list(filter(lambda line: len(line) > 0, copy_tmp_str.split('\n')))
				for line in lines:
					if not (all(c == ' ' for c in line) or all(c == '\t' for c in line)):
						f.write(line + '\n')

	# Changes surefire version in a pom
	def add_argline_to_surefire(self, content):
		inspected_module = self.repo_dir
		poms = self.get_all_pom_paths(inspected_module)
		for pom in poms:
			xmlFile = parse(pom)
			tmp_build_list = xmlFile.getElementsByTagName('build')
			build_list = list(
				filter(lambda b: not b.parentNode == None and b.parentNode.localName == 'project', tmp_build_list))
			if len(build_list) == 0:
				continue
			assert len(build_list) == 1
			plugins_tags = build_list[0].getElementsByTagName('plugins')
			if len(plugins_tags) == 0:
				continue
			for plugins_tag in plugins_tags:
				if plugins_tag.parentNode.localName == 'build':
					artifacts_ids = list(
						map(lambda a: str(a.firstChild.data), plugins_tag.getElementsByTagName('artifactId')))
					if not any(a_id == 'maven-surefire-plugin' for a_id in artifacts_ids):
						new_plugin = plugins_tag.ownerDocument.createElement(tagName='plugin')
						new_group_id = new_plugin.ownerDocument.createElement(tagName='groupId')
						new_artifact_id = new_plugin.ownerDocument.createElement(tagName='artifactId')
						new_group_id_text = new_group_id.ownerDocument.createTextNode('org.apache.maven.plugins')
						new_artifact_id_text = new_artifact_id.ownerDocument.createTextNode('maven-surefire-plugin')
						new_group_id.appendChild(new_group_id_text)
						new_plugin.appendChild(new_group_id)
						new_artifact_id.appendChild(new_artifact_id_text)
						new_plugin.appendChild(new_artifact_id)
						plugins_tag.appendChild(new_plugin)
			for plugins_tag in plugins_tags:
				mvn.add_plugin_configuration_argline(plugins_tag, 'maven-surefire-plugin', content=content)
			os.remove(pom)
			with open(pom, 'w+') as f:
				tmp_str = xmlFile.toprettyxml()
				copy_tmp_str = ''
				for char in tmp_str[::]:
					if 125 < ord(char):
						copy_tmp_str += 'X'
					else:
						copy_tmp_str += char
				lines = list(filter(lambda line: len(line) > 0, copy_tmp_str.split('\n')))
				for line in lines:
					if not (all(c == ' ' for c in line) or all(c == '\t' for c in line)):
						f.write(line + '\n')

	def add_element_to_pom(self, pom_path, path, path_filter, element_name, element_value, add_new_element=True):
		"""
		add element to pom file, used to modify the surefire plugin
		:param pom_path: the path to the pom.xml to modify
		:param path: the path to the element in the pom.xml (list of strings)
		:param element_name: name of the element to add
		:param element_value: the value to add
		:param add_new_element: if True add new element, else append to existing element
		"""
		xml.etree.ElementTree.register_namespace('', "http://maven.apache.org/POM/4.0.0")
		xml.etree.ElementTree.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")

		def get_children_by_name(element, name):
			return filter(lambda e: e.tag.endswith(name), element.getchildren())

		def get_or_create_child(element, name):
			child = get_children_by_name(element, name)
			if len(child) == 0:
				return xml.etree.ElementTree.SubElement(element, name)
			else:
				return child[0]

		et = xml.etree.ElementTree.parse(pom_path)
		path = ['build', 'plugins', 'plugin']
		elements = et.getroot()
		for name in path:
			elements = reduce(list.__add__, map(lambda elem: get_children_by_name(elem, name), elements), [])
		surfire_plugins = filter(lambda plugin: filter(lambda x: x.text == "maven-surefire-plugin",
		                                               get_children_by_name(plugin, "artifactId")),
		                         filter(lambda e: e.tag.endswith('plugin'), et.getroot().iter()))

		pass

	def run_function_on_poms_by_filter(self, pom_filter, function, *args, **kwargs):
		map(lambda pom: function(pom, *args, **kwargs), filter(pom_filter, self.get_all_pom_paths(self._repo_dir)))

	# Returns mvn command string that runns the given tests in the given module
	def generate_mvn_test_cmd(self, tests, module=None):
		mvn_names = list(map(lambda t: t.mvn_name, tests))
		if module == None or module == self.repo_dir:
			ans = 'mvn test -fn'
		else:
			ans = 'mvn -pl :{} -am test -fn'.format(
				os.path.basename(module))
		# ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
		ans += ' -DfailIfNoTests=false -Drat.skip=true'
		if len(mvn_names) > 0:
			ans += ' -Dtest='
			for mvn_name in mvn_names:
				if not ans.endswith('='):
					ans += ','
				ans += mvn_name
		ans += ' -f ' + self.repo_dir
		return ans

	# Returns mvn command string that runns the given tests in the given module
	def generate_mvn_install_cmd(self, testcases, module=None, debug=False):
		testclasses = []
		for testcase in testcases:
			if not testcase.parent in testclasses:
				testclasses.append(testcase.parent)
		if module == None or module == self.repo_dir:
			ans = 'mvn install -fn -Drat.skip=true -Drat.ignoreErrors=true -Drat.numUnapprovedLicenses=10000 -Djacoco.skip=true  -DfailIfNoTests=false'
		else:
			ans = 'mvn -pl :{} -am install -Drat.skip=true -Drat.ignoreErrors=true -Drat.numUnapprovedLicenses=10000 -Djacoco.skip=true -fn'.format(
				os.path.basename(module))
		# ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
		ans += ' -DfailIfNoTests=false'
		if debug:
			ans += ' -Dmaven.surefire.debug="-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=y,address=8000 -Xnoagent -Djava.compiler=NONE"'
		if len(testcases) > 0:
			ans += ' -Dtest='
			for testclass in testclasses:
				if not ans.endswith('='):
					ans += ','
				ans += testclass.mvn_name
		# ans += ' -f ' + self.repo_dir
		return ans

	# Returns mvn command string that compiles the given the given module
	def generate_mvn_test_compile_cmd(self, module):
		if module == self.repo_dir:
			ans = 'mvn test-compile -fn  -Drat.skip=true -Drat.ignoreErrors=true -Drat.numUnapprovedLicenses=10000'
		else:
			ans = 'mvn -pl :{} -am test-compile -fn  -Drat.skip=true -Drat.ignoreErrors=true -Drat.numUnapprovedLicenses=10000'.format(
				os.path.basename(module))
		ans += ' -f ' + self.repo_dir
		return ans

	# Returns mvn command string that cleans the given the given module
	def generate_mvn_clean_cmd(self, module):
		if module == self.repo_dir:
			ans = 'mvn clean '
		else:
			ans = 'mvn -pl :{} -am clean -fn'.format(
				os.path.basename(module))
		ans += ' -f ' + self.repo_dir
		return ans

	# Returns mvn command string that cleans the given the given module
	def generate_mvn_evosuite_clean_cmd(self, module):
		ans = 'mvn evosuite:clean '
		if module == self.repo_dir:
			ans += ' -f ' + self.repo_dir
		else:
			ans += ' -f ' + module

		return ans

	# Returns mvn command string that prints evosuite help material
	def generate_mvn_evosuite_help_cmd(self, module):
		if module == self.repo_dir:
			ans = 'mvn evosuite:help '
		else:
			ans = 'mvn -pl :{} -am evosuite:help -fn'.format(
				os.path.basename(module))
		ans += ' -f ' + self.repo_dir
		return ans

	# Returns mvn command string that prints evosuite help material
	def generate_mvn_help_evaluate_cmd(self, expression, module):
		if module == self.repo_dir:
			ans = 'mvn help:evaluate -Dexpression={}'.format(expression)
		else:
			ans = 'mvn -pl :{} -am help:evaluate -Dexpression={} -fn'.format(
				os.path.basename(module), expression)
		ans += ' -f ' + self.repo_dir
		ans += r' | findstr /R ^^[^^\[INFO\]]'
		return ans

	# Add tags to the pom. xquey is a string written in xpath aka xquery convention
	# Behaviour is unknown if the xquery doesn't refer to a single tag
	def set_pom_tag(self, xquery, value, module='', create_if_not_exist=False):
		pom = self.get_pom(module)
		root = ET.parse(pom).getroot()
		xmlns, _ = mvn.tag_uri_and_name(root)
		# if not xmlns == '':
		tmp_tags_1 = xquery.split('/')
		tmp_tags_2 = list(map(lambda t: self.add_xmlns_prefix(xmlns, t), tmp_tags_1))
		tags = list(map(lambda t: self.clean_query_string(t), tmp_tags_2))
		tag = self.get_tag(root, tags[1:], create_if_not_exist=create_if_not_exist)
		tag.text = value
		self.rewrite_pom(root=root, module=module)

	# Gets the tag specified in the xquery
	def get_pom_tag(self, xquery, module=''):
		pom = self.get_pom(module)
		root = ET.parse(pom).getroot()
		xmlns, _ = mvn.tag_uri_and_name(root)
		if not xmlns == '':
			tmp_tags_1 = xquery.split('/')
			tmp_tags_2 = list(map(lambda t: self.add_xmlns_prefix(xmlns, t), tmp_tags_1))
			tags = list(map(lambda t: self.clean_query_string(t), tmp_tags_2))
		return self.get_tag(root, tags[1:])

	# Recursively add element to tag
	def get_tag(self, root_tag, subtags_path_array, create_if_not_exist=False):
		if len(subtags_path_array) == 0:
			return root_tag
		next_tag_list = root_tag.findall(subtags_path_array[0])
		if len(next_tag_list) == 0:
			if create_if_not_exist:
				condition = ''
				tag_and_cond = subtags_path_array[0].replace(']', '').split('[')
				tag_name = tag_and_cond[0]
				if len(tag_and_cond) > 1:
					condition = tag_and_cond[1]
				new_tag = ET.SubElement(root_tag, tag_name)
				if not condition == '':
					[elem_name, val] = condition.split('=')
					new_tag_attr = ET.SubElement(new_tag, elem_name)
					new_tag_attr.text = val.strip('\'')
				return self.get_tag(root_tag=new_tag, subtags_path_array=subtags_path_array[1:],
				                    create_if_not_exist=create_if_not_exist)
			else:
				return None
		if len(next_tag_list) > 1:
			return None
		next_tag = next_tag_list[0]
		return self.get_tag(root_tag=next_tag, subtags_path_array=subtags_path_array[1:],
		                    create_if_not_exist=create_if_not_exist)

	def rewrite_pom(self, root, module=''):
		pom = self.get_pom(module=module)
		rough_string = ET.tostring(root, 'utf-8')
		reparsed = parseString(rough_string).toprettyxml().replace('</ns0:', '</').replace('<ns0:', '<')
		os.remove(pom)
		with open(pom, 'w+') as f:
			tmp_str = reparsed
			copy_tmp_str = ''
			for char in tmp_str[::]:
				if 125 < ord(char):
					copy_tmp_str += 'X'
				else:
					copy_tmp_str += char
			lines = list(filter(lambda line: len(line) > 0, copy_tmp_str.split('\n')))
			for line in lines:
				if not (all(c == ' ' for c in line) or all(c == '\t' for c in line)):
					f.write(line + '\n')

	def observe_tests(self):
		from junitparser import JUnitXml
		outcomes = {}
		for report in self.get_surefire_files():
			try:
				for case in JUnitXml.fromfile(report):
					test = TestResult(case)
					outcomes[test.full_name] = test
			except Exception as e:
				pass
		return outcomes

	def get_surefire_files(self):
		SURFIRE_DIR_NAME = 'surefire-reports'
		surefire_files = []
		for root, _, files in os.walk(self.repo_dir):
			for name in files:
				if name.endswith('.xml') and os.path.basename(root) == SURFIRE_DIR_NAME:
					surefire_files.append(os.path.join(root, name))
		return surefire_files

	# Returns the dictionary that map testcase string to its traces strings
	def get_traces(self, testcase_name=''):
		ans = {}
		debugger_tests_dir = os.path.relpath(os.path.join(self.repo_dir, r'../../DebuggerTests'))
		if not os.path.isdir(debugger_tests_dir):
			return ans
		for filename in os.listdir(debugger_tests_dir):
			if (filename.startswith('Trace_') or filename.endswith(".txt")) and testcase_name.replace('#',
			                                                                                          '@') in filename:
				with open(os.path.join(debugger_tests_dir, filename), 'r') as file:
					key = filename.replace('.txt', '')
					ans[key] = []
					tmp = file.readlines()
					for trace in tmp:
						function_name = trace.replace('@', '#').replace('\n', '').split(' ')[-1]
						if not function_name in ans[key]:
							ans[key].append(str(function_name))
		return ans

	# Returns the dictionary that map testcase string to its traces strings
	def get_trace(self, testcase_name):
		ans = []
		dict = self.get_traces(testcase_name=testcase_name)
		if not len(dict) == 1:
			return ans
		ans = dict[dict.keys()[0]]
		return ans

	# Returns the pom path associated with the given module
	def get_pom(self, module):
		if module == '':
			module = self.repo_dir
		pom_singelton = list(
			filter(lambda f: f == 'pom.xml' or f == 'project.xml', os.listdir(module))
		)
		if not len(pom_singelton) == 1:
			return ''
		else:
			return os.path.join(module, pom_singelton[0])

	# Adds the xmlns prefix to the tag
	def add_xmlns_prefix(self, xmlns, tag):
		prefix = '{' + xmlns + '}'
		with_prefix = ''
		if tag == '.':
			return tag
		if tag.startswith(prefix):
			with_prefix = tag
		else:
			with_prefix = prefix + tag
		if with_prefix.find('[') < with_prefix.find(']'):
			[tag_name, condition] = with_prefix.split('[')
			condition = condition.replace(']', '')
			[elem_name, val] = condition.split('=')
			elem_with_prefix = self.add_xmlns_prefix(xmlns, elem_name)
			with_prefix = tag_name + '[' + elem_with_prefix + '=' + val + ']'
		return with_prefix

	# Removes redundant chars from the given query to validate it
	def clean_query_string(self, xquery):
		ans = xquery
		while ' = ' in ans or ' =' in ans or '= ' in ans:
			ans = ans.replace(' = ', '=')
			ans = ans.replace(' =', '=')
			ans = ans.replace('= ', '=')
		return ans

	def get_generated_testcases(self, module=None):
		generated_tests_dir = self.get_generated_testcases_dir(module=module)
		if not os.path.isdir(generated_tests_dir):
			return self.find_all_evosuite_tests(module)
		generated_test_classes = mvn.parse_tests(generated_tests_dir)
		generated_test_classes_mvn_names = map(lambda x: x.mvn_name, generated_test_classes)
		all_tests = self.get_tests()
		exported_tests = filter(lambda x: x.mvn_name in generated_test_classes_mvn_names, all_tests)
		return mvn.get_testcases(test_classes=exported_tests)

	def find_all_evosuite_tests(self, module):
		all_testcases = mvn.get_testcases(self.get_tests(module))
		return filter(lambda x: TestObjects.is_evosuite_test_class(x.parent.src_path), all_testcases)

	def get_generated_testcases_dir(self, module=None):
		module_path = self.repo_dir if module == None else module
		return os.path.join(module_path, os.path.join('.evosuite', 'best-tests'))

	def is_generated_test(self, test):
		return TestObjects.is_evosuite_test_class(test.src_path)

	def add_plugin(self, artifactId, groupId, version, module):
		plugin_xpath = r"./build/plugins/plugin[artifactId = '{}']".format(artifactId)
		set_groupId_xquery = '/'.join([plugin_xpath, "groupId"])
		set_version_xquery = '/'.join([plugin_xpath, "version"])
		self.set_pom_tag(xquery=set_groupId_xquery, create_if_not_exist=True, module=module, value=groupId)
		self.set_pom_tag(xquery=set_version_xquery, create_if_not_exist=True, module=module, value=version)

	def add_dependency(self, artifactId, groupId, version, module):
		dependency_xpath = r"./dependencies/dependency[artifactId = '{}']".format(artifactId)
		set_groupId_xquery = '/'.join([dependency_xpath, "groupId"])
		set_version_xquery = '/'.join([dependency_xpath, "version"])
		self.set_pom_tag(xquery=set_groupId_xquery, create_if_not_exist=True, module=module, value=groupId)
		self.set_pom_tag(xquery=set_version_xquery, create_if_not_exist=True, module=module, value=version)

	def copy_depenedencies(self, module=None):
		inspected_module = self.repo_dir
		if not module == None:
			inspected_module = module
		test_cmd = self.generate_mvn_copy_depenedencies_cmd(inspected_module)
		build_report = mvn.wrap_mvn_cmd(test_cmd)
		return build_report

	def generate_mvn_copy_depenedencies_cmd(self, module):
		if module == self.repo_dir:
			ans = 'mvn dependency:copy-dependencies -fn'
		else:
			ans = 'mvn -pl :{} -am dependency:copy-dependencies -fn'.format(
				os.path.basename(module))
		ans += ' -f ' + self.repo_dir
		return ans

	def generate_mvn_compile_cmd(self, module):
		if module == self.repo_dir:
			ans = 'mvn compile -fn  -Drat.skip=true -Drat.ignoreErrors=true -Drat.numUnapprovedLicenses=10000'
		else:
			ans = 'mvn -pl :{} -am compile -fn  -Drat.skip=true -Drat.ignoreErrors=true -Drat.numUnapprovedLicenses=10000'.format(
				os.path.basename(module))
		ans += ' -f ' + self.repo_dir
		return ans

	def setup_tests_generator(self, module):
		EvosuiteFactory.create(repo=self).setup_tests_generator(module)

	if __name__ == "__main__":
		# repo = Repo(r"C:\amirelm\projects_minors\JEXL\version_to_test_trace\repo")
		# obs = repo.observe_tests()
		# pass
		# traces = JcovParser(r"C:\temp\traces").parse()
		import time

		start = time.time()
		print "start time:", start
		repo = Repo(r"C:\Temp\tika")
		repo.run_under_jcov(r"C:\temp\traces", False, instrument_only_methods=True)
		print "end time:", time.time() - start
