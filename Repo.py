import os
import sys
from shutil import copyfile
from xml.dom.minidom import parse
import TestObjects
import mvn

class Repo(object):
    def __init__(self, repo_dir):
        self._repo_dir = repo_dir

    @property
    def repo_dir(self):
        return self._repo_dir

    # Executes mvn test
    def install(self, module=None, testcases=[], time_limit=sys.maxint):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        install_cmd = self.generate_mvn_install_cmd(module=inspected_module, testcases=testcases)
        build_report = mvn.wrap_mvn_cmd(install_cmd, time_limit=time_limit)
        return build_report

    # Executes mvn test
    def test(self, module =None, testcases = [], time_limit = sys.maxint):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        test_cmd = self.generate_mvn_test_cmd(module=inspected_module, testcases=testcases)
        build_report = mvn.wrap_mvn_cmd(test_cmd, time_limit=time_limit)
        return build_report

    # Executes mvn clean
    def clean(self, module =None):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        test_cmd = self.generate_mvn_clean_cmd(inspected_module)
        build_report = mvn.wrap_mvn_cmd(test_cmd)
        return build_report

    # Executes mvn compile
    def test_compile(self, module =None):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        test_cmd = self.generate_mvn_test_compile_cmd(inspected_module)
        build_report = mvn.wrap_mvn_cmd(test_cmd)
        return build_report

    # Returns tests reports objects currently exists in this repo in path_to_reports
    def parse_tests_reports(self, path_to_reports, module =None):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        ans = []
        for filename in os.listdir(path_to_reports):
            if filename.endswith(".xml"):
                ans.append(TestObjects.TestClass(os.path.join(path_to_reports, filename), inspected_module))
        return ans

    # Gets path to tests object in repo, or in a cpsecifc module if specified
    def get_tests(self, module = None):
        ans = []
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        if os.path.isdir(inspected_module + '\\src\\test'):
            if os.path.isdir(inspected_module + '\\src\\test\\java'):
                ans.extend(mvn.parse_tests(inspected_module + '\\src\\test\\java'))
            else:
                ans.extend(parse_tests(inspected_module + '\\src\\test'))
        for filename in os.listdir(inspected_module):
            file_abs_path = os.path.join(inspected_module, filename)
            if os.path.isdir(file_abs_path):
                if not (filename == 'src' or filename == '.git'):
                    ans.extend(self.get_tests(file_abs_path))
        return ans


    # Gets all the reports in the given module if given, else in the given module
    def get_tests_reports(self, module = None):
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
    def setup_tracer(self, target = None):
        agent_path_src = os.path.join(mvn.tracer_dir,r'target\uber-tracer-1.0.1-SNAPSHOT.jar')
        if not os.path.isfile(agent_path_src):
				os.system('mvn install -f {}'.format(mvn.tracer_dir))
        agent_path_dst = os.path.join(self.repo_dir, 'agent.jar')
        paths_path= os.path.join(self.repo_dir, 'paths.txt')
        copyfile(agent_path_src, agent_path_dst)
        with open(paths_path, 'w+') as paths:
            paths.write(os.path.join(os.environ['USERPROFILE'],'.m2\\repository')+'\n')
            paths.write(self.repo_dir)
        self.add_argline_to_surefire('-javaagent:{}={}'.format(agent_path_dst, paths_path))


    # Changes all the pom files in a module recursively
    def get_all_pom_paths(self, module = None):
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
    def change_surefire_ver(self ,version, module =None):
        ans = []
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        poms = self.get_all_pom_paths(inspected_module)
        new_file_lines = []
        for pom in poms:
            xmlFile = parse(pom)
            tmp_build_list = xmlFile.getElementsByTagName('build')
            build_list = list(filter(lambda b: not b.parentNode == None and b.parentNode.localName=='project' ,tmp_build_list))
            if len(build_list) == 0:
                continue
            assert len(build_list) == 1
            plugins_tags = build_list[0].getElementsByTagName('plugins')
            if len(plugins_tags) ==0:
                continue
            for plugins_tag in plugins_tags:
                if plugins_tag.parentNode.localName =='build' :
                    artifacts_ids = list(map(lambda a: str(a.firstChild.data), plugins_tag.getElementsByTagName('artifactId')))
                    if not any( a_id == 'maven-surefire-plugin' for a_id in artifacts_ids):
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
                mvn.change_plugin_version_if_exists(plugins_tag,'maven-surefire-plugin', version)
            os.remove(pom)
            with open(pom, 'w+') as f:
                tmp_str = xmlFile.toprettyxml()
                copy_tmp_str = ''
                for char in tmp_str[::]:
                    if 125 < ord(char):
                        copy_tmp_str += 'X'
                    else:
                        copy_tmp_str += char
                lines = list(filter(lambda line: len(line)>0,copy_tmp_str.split('\n')))
                for line in lines:
                    if not (all(c == ' ' for c in line) or all(c == '\t' for c in line)):
                        f.write(line+'\n')

    # Changes surefire version in a pom
    def add_argline_to_surefire(self, content):
        ans = []
        inspected_module = self.repo_dir
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

    # Returns mvn command string that runns the given tests in the given module
    def generate_mvn_test_cmd(self, testcases, module = None):
        testclasses = []
        for testcase in testcases:
            if not testcase.parent in testclasses:
                testclasses.append(testcase.parent)
        if module ==None or module == self.repo_dir:
            ans = 'mvn test -fn'
        else:
            ans = 'mvn -pl :{} -am test -fn'.format(
                os.path.basename(module))
        # ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
        ans += ' -DfailIfNoTests=false'
        if len(testcases)>0:
            ans+=' -Dtest='
            for testclass in testclasses:
                if not ans.endswith('='):
                    ans += ','
                ans += testclass.mvn_name
        ans += ' -f ' + self.repo_dir
        return ans

    # Returns mvn command string that runns the given tests in the given module
    def generate_mvn_install_cmd(self, testcases, module=None):
        testclasses = []
        for testcase in testcases:
            if not testcase.parent in testclasses:
                testclasses.append(testcase.parent)
        if module == None or module == self.repo_dir:
            ans = 'mvn install -fn'
        else:
            ans = 'mvn -pl :{} -am install -fn'.format(
                os.path.basename(module))
        # ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
        ans += ' -DfailIfNoTests=false'
        if len(testcases) > 0:
            ans += ' -Dtest='
            for testclass in testclasses:
                if not ans.endswith('='):
                    ans += ','
                ans += testclass.mvn_name
        ans += ' -f ' + self.repo_dir
        return ans

    # Returns mvn command string that compiles the given the given module
    def generate_mvn_test_compile_cmd(self, module):
        if module == self.repo_dir:
            ans = 'mvn test-compile -fn '
        else:
            ans = 'mvn -pl :{} -am test-compile -fn'.format(
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

    # Add tags to the pom. The oo stands for 'object oriented', and it stands for
    # the form of the string 'oo_element_str' which is from the form 'project.build.plugins.'
    def oo_add_to_pom(self, oo_element_str, pom ,create_parents_if_not_exist):
        tags = oo_element_str.split('.')
        xmlFile = parse(pom)
        tag_singelton = xmlFile.getElementsByTagName(tags[0])
        if not len(tag_singelton) == 1:
            raise mvn.MVNError(
                msg='Couldn\'t determine what tag is related to the root tag \'{}\'. There are {} options for these tag'.format(tags[0], str(len(tag_singelton)))
            )

    # Recursively add element to tag
    def add_to_tag(self, tag, sub_tags, data ,create_parents_if_not_exist):
		pass
        # if len(sub_tags) == 0:
            # if tag.firstChild == None:
                # text_node = tag.ownerDocument.createTextNode('')
                # tag.appendChild(text_node)
            # tag.firstChild.data = data
            # return
        # TODO find solution for the tags from the form plugins.plugin...
        # if '[' in tag.locaName and ']' in tag.locaName and tag.locaName in mvn.dict_super_sub_tags.keys():
            # child = mvn.find_child()
            # next_tag = None
            # sub_tags_local_name = mvn.dict_super_sub_tags[tag.locaName]
            # child_tags = mvn.get_first_degree_child_elements_by_name(tag=tag, name=sub_tags_local_name)
            # for c_tag in child_tags:
                # artifactId = mvn.get_first_degree_child_elements_by_name(tag=c_tag, name='artifactID')
                # if artifactId ==None:
                    # break
            # if new_tag ==None:
                # for c_tag in child_tags:
                    # name = mvn.get_first_degree_child_elements_by_name(tag=c_tag, name='name')
                    # if name ==None:
                        # break
            # if new_tag ==None:

        # else:
            # sub_tag_list = mvn.get_first_degree_child_elements_by_name(tag=tag, name=sub_tags[0])
            # if len(sub_tag_list) == 1:
                # self.add_to_tag(tag=sub_tag_list[0], sub_tags=sub_tags[1:], data=data,
                                # create_parents_if_not_exist=create_parents_if_not_exist)
            # elif len(sub_tag_list) == 0:
                # if create_parents_if_not_exist:
                    # new_tag = tag.ownerDocument.createElement(tagName=sub_tags[0])
                    # tag.appendChild(new_tag)
                    # self.add_to_tag(tag=sub_tag_list[0], sub_tags=sub_tags[1:], data=data,
                                    # create_parents_if_not_exist=create_parents_if_not_exist)
                # else:
                    # raise mvn.MVNError(msg='{} not exist in the tag a tag in {}'.format(sub_tags[0], tag.locaName))
            # else:
                # raise mvn.MVNError(
                    # msg='Couldn\'t determine what tag is related to the tag \'{}\'. There are {} options for these tag'.format(
                        # sub_tags[0], str(len(sub_tag_list)))
                # )

    # Returns the dictionary that map testcase string to its traces strings
    def get_traces(self, test_name = ''):
        ans = {}
        debugger_tests_dir  = os.path.relpath(os.path.join(self.repo_dir,r'../../DebuggerTests'))
        for filename in os.listdir(debugger_tests_dir ):
            if (filename.startswith('Trace_') or filename.endswith(".txt")) and test_name in filename:
                with open(os.path.join(debugger_tests_dir,filename),'r') as file:
                    key = filename.replace('.txt','')
                    ans[key] = []
                    tmp = file.readlines()
                    for trace in tmp:
                        function_name = trace.replace('@', '#').replace('\n','').split(' ')[-1]
                        ans[key].append(function_name)

        return ans





