import os

from enum import Enum

from mvnpy import mvn

EVOSUITE_SUREFIRE_VERSION = '2.17'
EVOSUITE_JAVA_VER = '1.8'
EVOSUITE_VER = '1.6'


class EvosuiteFactory(object):
	@classmethod
	def create(cls, repo, strategy=None, regression_repo=None):
		if strategy == None:
			return Evosuite(repo=repo)
		if strategy == TestGenerationStrategy.MAVEN:
			return MAVENEvosuite(repo=repo)
		if strategy == TestGenerationStrategy.CMD:
			return CMDEvosuite(repo=repo)
		if strategy == TestGenerationStrategy.CMD_BM:
			return CMDEvosuite(repo=repo, ver='BM')
		if strategy == TestGenerationStrategy.EVOSUITER:
			return Evosuiter(repo=repo, regression_repo=regression_repo)


class Evosuite(object):

	def __init__(self, repo):
		self.repo = repo

	def generate(self):
		pass

	def export(self):
		pass

	def is_tests_generator_setup(self, module):
		mvn_help_cmd = self.generate_mvn_evosuite_help_cmd(module)
		EVOUSUITE_CONFIGURED_INDICATION = 'evosuite:generate'
		with os.popen(mvn_help_cmd) as proc:
			return any(list(map(lambda l: EVOUSUITE_CONFIGURED_INDICATION in l, proc.readlines())))

	# Returns mvn command string that prints evosuite help material
	def generate_mvn_evosuite_help_cmd(self, module):
		if module == self.repo.repo_dir:
			ans = 'mvn evosuite:help '
		else:
			ans = 'mvn -pl :{} -am evosuite:help -fn'.format(
				os.path.basename(module))
		ans += ' -f ' + self.repo.repo_dir
		return ans

	def setup_tests_generator(self, inspected_module):
		module = self.repo.repo_dir if inspected_module == None else inspected_module
		evousuite_version_property_xquery = '/'.join(['.', 'properties', 'evosuiteVersion'])
		self.repo.set_pom_tag(xquery=evousuite_version_property_xquery, create_if_not_exist=True, module=module,
		                      value=self.repo.DEFAULT_ES_VERSION)
		self.repo.add_plugin(artifactId='evosuite-maven-plugin', groupId='org.evosuite.plugins',
		                     version='${evosuiteVersion}', module=module)
		self.repo.add_plugin(artifactId='maven-surefire-plugin', groupId='org.apache.maven.plugins',
		                     version=self.repo.DEFAULT_SUREFIRE_VERSION, module=module)
		self.repo.add_dependency(artifactId='evosuite-standalone-runtime', groupId='org.evosuite',
		                         version='${evosuiteVersion}', module=module)
		self.repo.add_dependency(artifactId='junit', groupId='junit',
		                         version=self.repo.DEFAULT_JUNIT_VERSION, module=module)
		self.repo.add_dependency(artifactId='xercesImpl', groupId='xerces',
		                         version=self.repo.DEFAULT_XERCES_VERSION, module=module)
		evousuite_xpath = r"./build/plugins/plugin[artifactId = 'evosuite-maven-plugin']"
		surefire_xpath = r"./build/plugins/plugin[artifactId = 'maven-surefire-plugin']"
		execution_xpath = "executions/execution"
		prepare_goal_xquery = '/'.join([evousuite_xpath, execution_xpath, "goals/goal"])
		phase_xquery = '/'.join([evousuite_xpath, execution_xpath, "phase"])
		listener_name_xquery = '/'.join([surefire_xpath, 'configuration', 'properties', 'property', 'name'])
		listener_value_xquery = '/'.join([surefire_xpath, 'configuration', 'properties', 'property', 'value'])
		self.repo.set_pom_tag(xquery=prepare_goal_xquery, create_if_not_exist=True, module=module, value='prepare')
		self.repo.set_pom_tag(xquery=phase_xquery, create_if_not_exist=True, module=module,
		                      value='process-test-classes')
		self.repo.set_pom_tag(xquery=listener_name_xquery, create_if_not_exist=True, module=module, value='listener')
		self.repo.set_pom_tag(xquery=listener_value_xquery, create_if_not_exist=True, module=module,
		                      value='org.evosuite.runtime.InitializingListener')

	def get_dependecy_dir(self, module):
		return reduce(lambda acc, curr: os.path.join(acc, curr), ['target', 'dependency'], module)

	# Returns mvn command string that generates tests for the given module
	def generate_generate_tests_export_cmd(self, classes, module=None):
		inspeced_module = self.repo.repo_dir if module == None else module
		if module == None or module == self.repo.repo_dir:
			ans = 'mvn evosuite:export -fn'
		else:
			ans = 'mvn -pl :{} -am evosuite:export -fn'.format(
				os.path.basename(module))
		if len(classes) > 0:
			path_to_cutsfile = os.path.join(self.repo.repo_dir, "cutsFile.txt")
			with open(path_to_cutsfile, "w+") as tmp_file:
				tmp_file.write(' ,'.join(classes))
				ans += ' '
				ans += ' -DcutsFile="{}"'.format(path_to_cutsfile)
		ans += ' -f ' + inspeced_module
		return ans

	def gen_cuts_file(self, classes, path):
		with open(path, "w+") as tmp_file:
			tmp_file.write(' ,'.join(classes))

	def generated_no_test(self, build_report):
		return '[INFO] WARN: failed to generate tests for' in build_report

	def handle_post_generate(self, build_report, cmd, time_limit):
		if self.repo.has_weird_error_report(build_report):
			self.repo.install()
			build_report = mvn.wrap_mvn_cmd(cmd, time_limit=time_limit)
		if self.repo.has_license_error_report(build_report):
			build_report = mvn.wrap_mvn_cmd(cmd + ' -Drat.skip=true', time_limit=time_limit)
		if self.generated_no_test(build_report):
			for i in range(0, 5):
				if not self.generated_no_test(build_report):
					break
				build_report = mvn.wrap_mvn_cmd(cmd + ' -X', time_limit=time_limit)
		return build_report


class CMDEvosuite(Evosuite):

	def __init__(self, repo, ver=EVOSUITE_VER):
		super(CMDEvosuite, self).__init__(repo=repo)
		self.ver = ver

	def generate(self, module=None, classes=[], seed=None, time_limit=mvn.MVN_MAX_PROCCESS_TIME_IN_SEC):
		inspected_module = self.repo.repo_dir if module is None else module
		build_report = self.prepare_repo(self.repo, module)
		for cut in classes:
			test_cmd = self.generate_tests_generation_cmd(module=inspected_module, cut=cut, seed=seed)
			build_report += '\ncmd = {}\n\n'.format(test_cmd)
			build_report += mvn.wrap_mvn_cmd(test_cmd, time_limit=time_limit, dir=self.repo.repo_dir)
			build_report += self.handle_post_generate(build_report, test_cmd, time_limit)
		export_cmd = self.generate_generate_tests_export_cmd(module=inspected_module, classes=classes)
		build_report += mvn.wrap_mvn_cmd(export_cmd, time_limit=time_limit)
		if os.path.exists(os.path.join(self.repo.repo_dir, 'cutsFile.txt')):
			os.remove(os.path.join(self.repo.repo_dir, 'cutsFile.txt'))
		return build_report

	def prepare_repo(self, repo, module=None):
		inspected_module = repo.repo_dir if module is None else module
		if not self.is_tests_generator_setup(inspected_module):
			self.setup_tests_generator(inspected_module)
		build_report = repo.compile(inspected_module)
		if mvn.has_compilation_error(build_report):
			raise mvn.MVNError(msg='Project didnt compile before tests generation', report=build_report)
		build_report += repo.copy_depenedencies(inspected_module)
		build_report += repo.unpack_depenedencies(inspected_module)
		return build_report

	def export(self):
		pass

	def generate_tests_generation_cmd(self, module, cut, seed=None):
		return '{} -projectCP {} -class {} {}'.format(
			self.generate_evosuite_run_cmd(),
			self.generate_project_classpath(module),
			self.generate_target_class_mvn_names(cut),
			self.generate_configuration_params(module, seed)
		)

	def generate_evosuite_run_cmd(self):
		return r'java -jar "{}"'.format(mvn.get_evosuite_path(evosuite_ver=self.ver))

	def generate_target_classes_binaries_path(self, module):
		return os.path.relpath(
			reduce(lambda acc, curr: os.path.join(acc, curr), [module, 'target', 'classes'])
			, self.repo.repo_dir)

	def generate_dependency_path(self, module):
		return os.path.relpath(
			reduce(
				lambda acc, curr: os.path.join(acc, curr),
				[module, 'target', 'dependency']
			),
			self.repo.repo_dir
		)

	def generate_target_class_mvn_names(self, cut):
		return cut

	def generate_configuration_params(self, module, seed=None):
		return reduce(
			lambda acc, curr: acc + " " + curr,
			[
				"-Dassertion_strategy=ALL",
				"-criterion BRANCH:EXCEPTION:METHOD",
				"-Dtest_dir={}".format(self.get_gen_test_dir(module)),
				"-seed={}".format(str(seed)) if seed is not None else ""
			]
		)

	def generate_project_classpath(self, module):
		return '{};{}'.format(
			self.generate_target_classes_binaries_path(module),
			self.generate_dependency_path(module)
		)

	def get_gen_test_dir(self, module):
		return reduce(
			lambda acc, curr: os.path.join(acc, curr),
			[module, '.evosuite', 'best-tests']
		)


class Evosuiter(CMDEvosuite):
	def __init__(self, repo, regression_repo):
		super(Evosuiter, self).__init__(repo=repo)
		self.reg_repo = regression_repo

	def generate(self, module=None, classes=[], seed=None, time_limit=mvn.MVN_MAX_PROCCESS_TIME_IN_SEC):
		inspected_module = self.reg_repo.repo_dir if module is None else self.map_to_reg(module)
		build_report = self.prepare_repo(self.reg_repo, inspected_module)
		build_report += super(Evosuiter, self).generate(
			module=module, classes=classes, seed=seed, time_limit=time_limit
		)
		return build_report

	def generate_tests_generation_cmd(self, module, cut, seed=None):
		return super(Evosuiter, self).generate_tests_generation_cmd(
			module=module, cut=cut, seed=seed
		) + ' -regressionSuite -Dregressioncp={} -Dregression_fitness={}'.format(
			self.generate_project_classpath(self.map_to_reg(module)),
			self.pick_regression_fitness()
		)
	def generate_target_classes_binaries_path(self, module):
		return reduce(
			lambda acc, curr: os.path.join(acc, curr),
			[module, 'target', 'classes']
		)

	def generate_dependency_path(self, module):
		return reduce(
			lambda acc, curr: os.path.join(acc, curr),
			[module, 'target', 'dependency']
		)

	def map_to_reg(self, module):
		return os.path.realpath(
			os.path.join(
				self.reg_repo.repo_dir,
				os.path.relpath(module, self.repo.repo_dir)
			)
		)

	def pick_regression_fitness(self):
		return 'ALL_MEASURES'


class MAVENEvosuite(Evosuite):

	def __init__(self, repo):
		super(MAVENEvosuite, self).__init__(repo=repo)

	def generate(self, module=None, classes=[], seed=None, time_limit=mvn.MVN_MAX_PROCCESS_TIME_IN_SEC):
		inspected_module = self.repo.repo_dir if module == None else module
		if not self.is_tests_generator_setup(inspected_module):
			self.setup_tests_generator(inspected_module)
		test_cmd = self.generate_tests_generation_cmd(module=inspected_module, classes=classes)
		build_report = mvn.wrap_mvn_cmd(test_cmd, time_limit=time_limit)
		build_report = self.handle_post_generate(build_report, test_cmd, time_limit)
		if os.path.exists(os.path.join(self.repo.repo_dir, 'cutsFile.txt')):
			os.remove(os.path.join(self.repo.repo_dir, 'cutsFile.txt'))
		return build_report

	def export(self):
		pass

	def generate_tests_generation_cmd(self, module, classes):
		inspeced_module = self.repo.repo_dir if module == None else module
		if module == None or module == self.repo.repo_dir:
			ans = 'mvn evosuite:generate evosuite:export -fn'
		else:
			ans = 'mvn -pl :{} -am evosuite:generate evosuite:export -fn'.format(
				os.path.basename(module))
		if len(classes) > 0:
			path_to_cutsfile = os.path.join(self.repo.repo_dir, "cutsFile.txt")
			self.gen_cuts_file(classes, path_to_cutsfile)
			ans += ' '
			ans += ' -Drat.skip=true -Dossindex.fail=false -Denforcer.skip=true -DcutsFile="{}"'.format(
				path_to_cutsfile)
		ans += ' -f ' + inspeced_module
		return ans


class TestGenerationStrategy(Enum):
	MAVEN = 1
	CMD = 2
	CMD_BM = 3
	EVOSUITER = 4


class TestsGenerationError(mvn.MVNError):
	def __init__(self, msg='', report='', trace=''):
		super(TestsGenerationError, self).__init__(msg=msg, report=report, trace=trace)
