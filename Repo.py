import os
import sys
from shutil import copyfile
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
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
    def test(self, module =None, tests = [], time_limit = sys.maxint):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        test_cmd = self.generate_mvn_test_cmd(module=inspected_module, tests=tests)
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
                ans.append(TestObjects.TestClassReport(os.path.join(path_to_reports, filename), inspected_module))
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
    def generate_mvn_test_cmd(self, tests, module = None):
        mvn_names = list(map(lambda t: t.mvn_name,tests))
        if module ==None or module == self.repo_dir:
            ans = 'mvn test -fn'
        else:
            ans = 'mvn -pl :{} -am test -fn'.format(
                os.path.basename(module))
        # ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
        ans += ' -DfailIfNoTests=false'
        if len(mvn_names)>0:
            ans+=' -Dtest='
            for mvn_name in mvn_names:
                if not ans.endswith('='):
                    ans += ','
                ans += mvn_name
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

    # Add tags to the pom. xquey is a string written in xpath aka xquery convention
    # Behaviour is unknown if the xquery doesn't refer to a single tag
    def set_pom_tag(self, xquery, value , module = '', create_if_not_exist = False):
        pom = self.get_pom(module)
        root = ET.parse(pom).getroot()
        xmlns, _ = mvn.tag_uri_and_name(root)
        if not xmlns == '':
            tmp_tags_1 = xquery.split('/')
            tmp_tags_2 = list(map(lambda t: self.add_xmlns_prefix(xmlns, t), tmp_tags_1))
            tags = list(map(lambda t: self.clean_query_string(t), tmp_tags_2))
        tag = self.get_tag(root, tags[1:], create_if_not_exist = create_if_not_exist)
        tag.text = value
        self.rewrite_pom(root=root, module=module)

    # Gets the tag specified in the xquery
    def get_pom_tag(self, xquery, module = ''):
        pom = self.get_pom(module)
        root = ET.parse(pom).getroot()
        xmlns, _ = mvn.tag_uri_and_name(root)
        if not xmlns == '':
            tmp_tags_1 = xquery.split('/')
            tmp_tags_2 = list(map(lambda t: self.add_xmlns_prefix(xmlns, t), tmp_tags_1))
            tags = list(map(lambda t: self.clean_query_string(t), tmp_tags_2))
        return self.get_tag(root, tags[1:])

    # Recursively add element to tag
    def get_tag(self, root_tag ,subtags_path_array, create_if_not_exist = False):
        if len(subtags_path_array) ==0:
            return root_tag
        next_tag_list = root_tag.findall(subtags_path_array[0])
        if len(next_tag_list) == 0:
            if create_if_not_exist:
                condition = ''
                [tag_name, condition] = subtags_path_array[0].replace(']','').split('[')
                new_tag = ET.SubElement(root_tag, tag_name)
                if not condition == '':
                    [elem_name, val] = condition.split('=')
                    new_tag_attr = ET.SubElement(new_tag, elem_name)
                    new_tag_attr.text = val
                return self.get_tag(root_tag=new_tag, subtags_path_array=subtags_path_array[1:], create_if_not_exist=create_if_not_exist)
            else:
                return None
        if len(next_tag_list) >1:
            return None
        next_tag = next_tag_list[0]
        return self.get_tag(root_tag=next_tag, subtags_path_array=subtags_path_array[1:],
                            create_if_not_exist=create_if_not_exist)


    def rewrite_pom(self, root, module =''):
        pom = os.path.join(module, 'pom.xml')
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

    # Returns the dictionary that map testcase string to its traces strings
    def get_traces(self, testcase_name = ''):
        ans = {}
        debugger_tests_dir  = os.path.relpath(os.path.join(self.repo_dir,r'../../DebuggerTests'))
        if not os.path.isdir(debugger_tests_dir ):
            return ans
        for filename in os.listdir(debugger_tests_dir ):
            if (filename.startswith('Trace_') or filename.endswith(".txt")) and testcase_name.replace('#', '@') in filename:
                with open(os.path.join(debugger_tests_dir,filename),'r') as file:
                    key = filename.replace('.txt','')
                    ans[key] = []
                    tmp = file.readlines()
                    for trace in tmp:
                        function_name = trace.replace('@', '#').replace('\n','').split(' ')[-1]
                        if not function_name in ans[key]:
                            ans[key].append(str(function_name))
        return ans

    # Returns the dictionary that map testcase string to its traces strings
    def get_trace(self, testcase_name):
        ans = []
        dict = self.get_traces(testcase_name = testcase_name)
        if not len(dict) == 1:
            return ans
        ans = dict[dict.keys()[0]]
        return ans

    # Returns the pom path associated with the given module
    def get_pom(self, module):
        if module == '':
            module = self.repo_dir
        pom_singelton = list(
            filter(lambda f: f =='pom.xml', os.listdir(module))
        )
        if not len(pom_singelton) == 1:
            return ''
        else:
            return os.path.join(module,pom_singelton[0])

    #Adds the xmlns prefix to the tag
    def add_xmlns_prefix(self, xmlns, tag):
        prefix = '{'+xmlns+'}'
        with_prefix = ''
        if tag =='.':
            return tag
        if tag.startswith(prefix):
            with_prefix =  tag
        else:
            with_prefix = prefix + tag
        if with_prefix.find('[') < with_prefix.find(']'):
            [tag_name,condition] = with_prefix.split('[')
            condition = condition.replace(']','')
            [elem_name, val] = condition.split('=')
            elem_with_prefix = self.add_xmlns_prefix(xmlns, elem_name)
            with_prefix = tag_name+'['+elem_with_prefix+'='+val+']'
        return with_prefix

    # Removes redundant chars from the given query to validate it
    def clean_query_string(self, xquery):
        ans = xquery
        while ' = ' in ans or ' =' in ans or '= ' in ans:
            ans = ans.replace(' = ', '=')
            ans = ans.replace(' =', '=')
            ans = ans.replace('= ', '=')
        return ans





