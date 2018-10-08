import os
import TestObjects
from xml.dom.minidom import parse
import mvn


class Repo(object):
    def __init__(self, repo_dir):
        self._repo_dir = repo_dir

    @property
    def repo_dir(self):
        return self._repo_dir

    # Executes mvn test
    def test(self, module =None, testcases = []):
        inspected_module = self.repo_dir
        if not module == None:
            inspected_module = module
        test_cmd = self.generate_mvn_test_cmd(module=inspected_module, testcases=testcases)
        build_report = mvn.wrap_mvn_cmd(test_cmd)
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
    def change_surefire_ver(self ,version, module = None):
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
                f.write(copy_tmp_str)

    # Returns mvn command string that runns the given tests in the given module
    def generate_mvn_test_cmd(self, testcases, module = None):
        testclasses = []
        for testcase in testcases:
            if not testcase.parent in testclasses:
                testclasses.append(testcase.parent)
        if module ==None or module == self.repo_dir:
            ans = 'mvn clean test -fn'
        else:
            ans = 'mvn -pl :{} -am clean test -fn'.format(
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

    # Returns mvn command string that compiles the given the given module
    def generate_mvn_test_compile_cmd(self, module):
        ans = 'mvn -pl :{} -am clean test-compile -fn'.format(
            os.path.basename(module))
        ans += ' -f ' + self.repo_dir
        return ans

    # Returns mvn command string that cleans the given the given module
    def generate_mvn_clean_cmd(self, module):
        ans = 'mvn -pl :{} -am clean -fn'.format(
            os.path.basename(module))
        ans += ' -f ' + self.repo_dir
        return ans
