import xml.etree.ElementTree as ET
import xml.sax as SAX
from xml.dom.minidom import parse
import re
import os
import javalang

proj_dir = ''

class TestClass:
    def __init__(self, file_path):
        self._path = os.path.realpath(file_path)
        self._module = self.find_module(self._path)
        self._mvn_name = self.generate_mvn_name()
        self._testcases = []
        self._report = None
        self._id = '#'.join([os.path.basename(self.module), self.mvn_name])
        with open(self._path, 'r') as src_file:
            try:
                self._tree = javalang.parse.parse(src_file.read())
            except UnicodeDecodeError as e:
                raise TestParserException('Java file parsing problem:'+'\n'+str(e))
        class_decls = [class_dec for _, class_dec in self.tree.filter(javalang.tree.ClassDeclaration)]
        for class_decl in class_decls:
            for method in class_decl.methods:
                if self.is_valid_testcase(method):
                    self._testcases.append(TestCase(method, class_decl, self))

    @property
    def mvn_name(self):
        return self._mvn_name

    @property
    def src_path(self):
        return self._path

    @property
    def testcases(self):
        return self._testcases

    @property
    def module(self):
        return self._module

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, report):
        self._report = report

    @property
    def tree(self):
        return self._tree

    @property
    def id(self):
        return self._id

    def parse_src_path(self):
        ans = self.module
        ans += '\\src\\test\\java'
        packages = self.name.split('.')
        for p in packages:
            ans += '\\' + p
        return ans + '.java'

    def get_report_path(self):
        return self.module + '\\target\\surefire-reports\\' + 'TEST-' + self.mvn_name + '.xml'

    def attach_report_to_testcase(self, testcase):
        try:
            testcase.report = self.report.get_testcase_report(testcase.mvn_name)
        except TestParserException as e:
            self.report = None
            raise e

    # Looking for report, and if finds one, attach it to the self and al it's testcases
    def look_for_report(self):
        try:
            self.report =  TestClassReport(self.get_report_path(), self.module)
            for t in self.testcases:
                self.attach_report_to_testcase(t)
        except TestParserException:
            pass

    def clear_report(self):
        self.report = None
        for t in self.testcases:
            t.clear_report()

    def find_module(self, file_path):
        parent_dir = os.path.abspath(os.path.join(file_path, os.pardir))
        is_root = False
        while not is_root:
            if os.path.isfile(parent_dir + '//pom.xml'):
                return parent_dir
            else:
                tmp = os.path.abspath(os.path.join(parent_dir, os.pardir))
                is_root =  tmp == parent_dir
                parent_dir = tmp
        raise TestParserException(file_path + ' is not part of a maven module')

    def is_valid_testcase(self, method):
        return method.name.lower() != 'setup' and method.name.lower() != 'teardown' and\
               len(method.parameters)==0 and method.return_type==None

    def generate_mvn_name(self):
        relpath = os.path.relpath(self.src_path, self.module + '\\src\\test\\java').replace('.java', '')
        if relpath.startswith('..\\'):
            relpath = relpath[3:]
        return relpath.replace('\\', '.')

    def __repr__(self):
        return str(self.src_path)

    def __eq__(self, other):
        if not isinstance(other, TestClass):
            return False
        else:
            return self.id == other.id


class TestCase(object):
    def __init__(self, method, class_decl, parent):
        self._parent = parent
        self._method = method
        self._mvn_name = self.parent.mvn_name + '#' + self.method.name
        self.class_decl = class_decl
        self._id = self.generate_id()
        self._report = None
        self._start_line = self.method.position[0]
        self._end_line = self.find_end_line(self._start_line)
        assert self._end_line != -1

    @property
    def mvn_name(self):
        return self._mvn_name

    @property
    def src_path(self):
        return self.parent.src_path

    @property
    def id(self):
        return self._id

    @property
    def module(self):
        return self.parent.module

    @property
    def method(self):
        return self._method

    @property
    def parent(self):
        return self._parent

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, report):
        self._report = report

    @property
    def start_line(self):
        return self._start_line

    @property
    def end_line(self):
        return self._end_line

    @property
    def passed(self):
        return self.report.passed

    @property
    def failed(self):
        return self.report.failed

    @property
    def has_error(self):
        return self.report.has_error

    def clear_report(self):
        self.report = None

    def get_error(self):
        return self.report.get_error()

    def has_the_same_code_as(self, other):
        if len(self.method.body)==len(other.method.body):
            i=0
            while i< len(self.method.body):
                if not self.method.body[i] == other.method.body[i]:
                    return False
            return True
        else:
            return False

    def generate_id(self):
        ret_type = str(self.method.return_type)
        if len(self.method.parameters) == 0:
            parameters = '()'
        else:
            parameters = '(' + self.method.parameters[0].type.name
            if len(self.method.parameters) > 1:
                param_iter = iter(self.method.parameters)
                next(param_iter)
                for param in param_iter:
                    parameters += ', ' + param.type.name
            parameters += ')'
        return self.parent.src_path + '#' + self.class_decl.name + '#' + ret_type + '_' + self.method.name + parameters


    def get_lines_range(self):
        lower_position = self.method.position[0]
        for annotation in self.method.annotations:
            if annotation.position[0] < lower_position:
                lower_position = annotation.position[0]
        return (lower_position, self.end_line)

    def contains_line(self, line):
        range = self.get_lines_range()
        return range[0] <= line <= range[1]

    def find_end_line(self, line_num):
        brackets_stack = []
        open_position = (-1, -1)
        with open(self.src_path, 'r') as j_file:
            lines = j_file.readlines()
        i = 1
        for line in lines:
            if i < line_num:
                i += 1
                continue
            j = 1
            for letter in line:
                if '{' == letter:
                    brackets_stack.append('{')
                    break
                else:
                    j += 1
            if len(brackets_stack) == 1:
                open_position = (i, j)
                break
            i+=1
        if open_position[0] == -1 or open_position[1] == -1:
            return -1
        i = 1
        for line in lines:
            if i < open_position[0]:
                i += 1
                continue
            j = 1
            for letter in line:
                if i == open_position[0] and j <= open_position[1]:
                    j += 1
                    continue
                if letter == '{':
                    brackets_stack.append('{')
                if letter == '}':
                    brackets_stack.pop()
                if len(brackets_stack) == 0:
                    return i
                j += 1
            i += 1

    def __repr__(self):
        return self.id

    def __eq__(self, other):
        if not isinstance(other, TestCase):
            return False
        else:
            return self.id == other.id


class TestClassReport:
    def __init__(self, xml_doc_path, modlue_path):
        if not os.path.isfile(xml_doc_path):
            raise TestParserException('No such report file :' + xml_doc_path)
        self.xml_path = xml_doc_path
        self.success_testcases = []
        self.failed_testcases = []
        self._testcases = []
        self._time = 0.0
        self.maven_multiModuleProjectDirectory = ''
        self._module_path = modlue_path
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        self._name = root.get('name')
        self._src_file_path = self.parse_src_path()
        for testcase in root.findall('testcase'):
            m_test = TestCaseReport(testcase, self)
            if m_test.passed:
                self.success_testcases.append(m_test)
            else:
                self.failed_testcases.append(m_test)
            self._testcases.append(m_test)
            self._time += m_test.time
        properties_root = root.find('properties')
        properties = properties_root.findall('property')
        for property in properties:
            if property.get('name') == 'maven.multiModuleProjectDirectory':
                self.maven_multiModuleProjectDirectory = property.get('value')

    @property
    def time(self):
        return self._time

    @property
    def name(self):
        return self._name

    @property
    def testcases(self):
        return self._testcases

    def passed(self):
        return len(self.failed_testcases) == 0

    @property
    def module(self):
        return self._module_path

    @property
    def src_path(self):
        return self._src_file_path

    # Returns true if the given test name is this test or it's one of its testcases
    def is_associated(self, test):
        if test == 'test' or test == 'TEST' or test == 'Test':
            return False
        if test in self.name:
            return True
        for testcase in self.testcases:
            if test in testcase.name:
                return True
        return False

    def __repr__(self):
        return str(self.name)

    def parse_src_path(self):
        test_name = os.path.basename(self.xml_path).replace('TEST-', '').replace('.java', '').replace('.xml', '')
        test_name = test_name.replace('.', '\\')
        test_name += '.java'
        return self.module + '\\src\\test\\java\\' + test_name

    def get_testcase_report(self, testcase_mvn_name):
        ans_singelton = list(filter(lambda t: testcase_mvn_name.endswith(t.name), self.testcases))
        if not len(ans_singelton) == 1:
            raise TestParserException(str(len(ans_singelton)) + ' possible testcases reports for ' + testcase_mvn_name)
        return ans_singelton[0]


class TestCaseReport(object):
    def __init__(self, testcase, parent):
        self._parent = parent
        self.testcase_tag = testcase
        self._name = self.parent.name + '#'+self.testcase_tag.get('name')
        self._time = float(re.sub('[,]', '', self.testcase_tag.get('time')))
        self._passed = False
        self._failed = False
        self._has_error = False
        failure = self.testcase_tag.find('failure')
        if not failure is None:
            self._failed = True
        self.error = self.testcase_tag.find('error')
        if not self.error is None:
            self._has_error = True
        self._passed = not self._failed and not self._has_error

    @property
    def time(self):
        return self._time

    @property
    def name(self):
        return  self._name

    @property
    def passed(self):
        return self._passed

    @property
    def failed(self):
        return self._failed

    @property
    def has_error(self):
        return self._has_error

    @property
    def src_path(self):
        return self.parent.src_path

    @property
    def module(self):
        return self.parent.module

    @property
    def parent(self):
        return self._parent

    def get_error(self):
        return self.error.text

    def __repr__(self):
        return str(self.name)


class CompilationErrorReport(object):
    def __init__(self, compilation_error_report_line):
        self._path = ''
        self._error_line = ''
        self._error_col = ''
        self.str = compilation_error_report_line
        parts = compilation_error_report_line.split(' ')
        path_and_error_address = parts[1].split(':')
        error_address = path_and_error_address[len(path_and_error_address) - 1]
        self._error_line = int(error_address.strip('[]').split(',')[0])
        self._error_col = int(error_address.strip('[]').split(',')[1])
        self._path = ':'.join(path_and_error_address[:-1])
        if self._path.startswith('/') or self._path.startswith('\\'):
            self._path = self._path[1:]
        self._path = os.path.realpath(self._path)

    @property
    def path(self):
        return self._path

    @property
    def line(self):
        return self._error_line

    @property
    def column(self):
        return self._error_col

    def __repr__(self):
        return self.str

    def __str__(self):
        return self.str

    def __eq__(self, object):
        if not isinstance(o, CompilationErrorReport):
            return False
        else:
            return self.path == o.path and self.line == o.line and self.column == o.column


# Return parsed tests of the reports dir
def parse_tests_reports(path_to_reports, project_dir):
    ans = []
    for filename in os.listdir(path_to_reports):
        if filename.endswith(".xml"):
            ans.append(TestClass(os.path.join(path_to_reports, filename), project_dir))
    return ans


# Gets path to maven project directory and returns parsed
def get_tests(project_dir):
    ans = []
    if os.path.isdir(project_dir + '\\src\\test'):
        if os.path.isdir(project_dir + '\\src\\test\\java'):
            ans.extend(parse_tests(project_dir + '\\src\\test\\java'))
        else:
            ans.extend(parse_tests(project_dir + '\\src\\test'))
    for filename in os.listdir(project_dir):
        file_abs_path = os.path.join(project_dir, filename)
        if os.path.isdir(file_abs_path):
            if not (filename == 'src' or filename == '.git'):
                ans.extend(get_tests(file_abs_path))
    return ans


# Parses all the test java classes in a given directory
def parse_tests(tests_dir):
    ans = []
    for filename in os.listdir(tests_dir):
        abs_path = os.path.join(tests_dir, filename)
        if os.path.isdir(abs_path):
            ans.extend(parse_tests(abs_path))
        elif filename.endswith(".java"):
            ans.append(TestClass(abs_path))
    return ans


# Gets path to maven project directory and returns parsed
def get_tests_reports(project_dir):
    ans = []
    path_to_reports = os.path.join(project_dir, 'target\\surefire-reports')
    if os.path.isdir(path_to_reports):
        ans.extend(parse_tests_reports(path_to_reports, project_dir))
    for filename in os.listdir(project_dir):
        file_abs_path = os.path.join(project_dir, filename)
        if os.path.isdir(file_abs_path):
            if not (filename == 'src' or filename == '.git'):
                ans.extend(get_tests_reports(file_abs_path))
    return ans


# Returns the files generated compilation error in the maven build report
def get_compilation_error_testcases(compilation_error_report):
    ans = []
    for line in compilation_error_report:
        if is_error_report_line(line):
            compilation_error_testcase = get_error_test_case(line)
            if not compilation_error_testcase == None and not compilation_error_testcase in ans:
                ans.append(compilation_error_testcase)
    return ans


# Returns list of cimpilation error reports objects
def get_compilation_errors(compilation_error_report):
    ans = []
    for line in compilation_error_report:
        if is_error_report_line(line):
            error = CompilationErrorReport(line)
            if not error in ans:
                ans.append(error)
    return ans


# Returns lines list describing to compilation error in th build report
def get_compilation_error_report(build_report):
    ans = []
    report_lines = build_report.splitlines()
    i = 0
    while i < len(report_lines):
        if '[ERROR] COMPILATION ERROR :' in report_lines[i]:
            ans.append(report_lines[i])
            ans.append(report_lines[i + 1])
            i += 2
            while not end_of_compilation_errors(report_lines[i]):
                ans.append(report_lines[i])
                i += 1
        elif report_lines[i].endswith('Compilation failure'):
            while i < len(report_lines) and not end_of_compilation_errors(report_lines[i]):
                if is_error_report_line(report_lines[i]):
                    ans.append(report_lines[i])
                i += 1
        else:
            i += 1
    return ans


# Gets the test case associated with the compilation error
def get_error_test_case(line):
    ans = None
    path = ''
    error_address = ''
    parts = line.split(' ')
    path_and_error_address = parts[1].split(':')
    error_address = path_and_error_address[len(path_and_error_address) - 1]
    error_line = int(error_address.strip('[]').split(',')[0])
    path = ':'.join(path_and_error_address[:-1])
    if path.startswith('/') or path.startswith('\\'):
        path = path[1:]
    return get_line_testcase(path, error_line)


# Returns the files generated compilation error in the maven build report
def end_of_compilation_errors(line):
    return '[INFO] -------------------------------------------------------------' in line


# Returns true iff the given report line is a report of compilation error file
def is_error_report_line(line):
    if line.startswith('[ERROR]'):
        words = line.split(' ')
        if len(words) < 2:
            return False
        if len(words[1])<1:
            return False
        if words[1][0] == '/':
            words[1] = words[1][1:]
        if not ':' in words[1]:
            return False
        if words[1].find('.java') == -1:
            return False
        should_be_a_path = words[1][:words[1].find('.java') + len('.java')]
        return os.path.isfile(should_be_a_path)
    return False


# Returns all testcases of given test classes
def get_testcases(test_classes):
    ans = []
    for test_class in test_classes:
        ans += test_class.testcases
    return ans


# Returns TestCase object representing the testcase in file_path that contains line
def get_line_testcase(path, line):
    if not os.path.isfile(path):
        raise FileNotFoundError
    if not path.endswith('.java'):
        raise TestParserException('Cannot parse files that are not java files')
    testclass = TestClass(path)
    class_decl = get_compilation_error_class_decl(testclass.tree(), line)
    method = get_compilation_error_method(testclass.tree(), line)
    return TestCase(method, class_decl, testclass)


# Returns the method name of the method containing the compilation error
def get_compilation_error_method(tree, error_line):
    ans = None
    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        for method in node.methods:
            if get_method_line_position(method) < error_line:
                if ans == None:
                    ans = method
                elif get_method_line_position(ans) < get_method_line_position(method):
                    ans = method
    return ans


# Returns the method name of the method containing the compilation error
def get_compilation_error_class_decl(tree, error_line):
    ans = None
    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        if get_class_line_position(node) < error_line:
            if ans == None:
                ans = node
            elif get_class_line_position(node) < get_class_line_position(node):
                ans = node
    return ans


# Returns the line in which the method starts
def get_method_line_position(method):
    return method.position[0]


# Returns the line in which the class starts
def get_class_line_position(class_decl):
    return class_decl.position[0]


def export_as_csv(tests):
    with open('all_tests.csv', 'a', newline='') as csvfile:
        fieldnames = ['test_name', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for test in tests:
            writer.writerow({'test_name': test.name, 'time': str(test.time)})


# Returns mvn command string that runns the given tests in the given module
def generate_mvn_test_cmd(testcases, module):
    testclasses = []
    for testcase in testcases:
        if not testcase.parent in testclasses:
            testclasses.append(testcase.parent)
    if module==proj_dir:
        ans = 'mvn clean test -fn'
    else:
        ans = 'mvn -pl :{} -am clean test -fn'.format(
            os.path.basename(module))
    #ans = 'mvn test surefire:test -DfailIfNoTests=false -Dmaven.test.failure.ignore=true -Dtest='
    ans += ' -DfailIfNoTests=false -Dtest='
    for testclass in testclasses:
         if not ans.endswith('='):
             ans += ','
         ans += testclass.mvn_name
    ans += ' -f ' + proj_dir
    return ans


# Returns mvn command string that compiles the given the given module
def generate_mvn_test_compile_cmd(module):
    ans = 'mvn -pl :{} -am clean test-compile -fn'.format(
        os.path.basename(module))
    ans += ' -f ' + proj_dir
    return ans


# Returns mvn command string that cleans the given the given module
def generate_mvn_clean_cmd(module):
    ans = 'mvn -pl :{} -am clean -fn'.format(
        os.path.basename(module))
    ans += ' -f ' + proj_dir
    return ans


def get_mvn_exclude_tests_list(tests, time):
    count = 0
    ans = '-Dtest='
    for test in tests:
        if test.time > time:
            if ans[len(ans) - 1] != '=':
                ans += ','
            ans += '!' + test.name
            count += 1
    return ans

# Changes all the pom files in a module recursively
def get_all_pom_paths(module_dir):
    # with open(r'C:\Users\user\Code\Python\mvnpy\tmp.txt', 'r') as f:
    #     str = f.read()
    #     copy_str = ''
    #     for char in str[::]:
    #         if 125 < ord(char) <= 225:
    #             copy_str += 'X'
    #         else:
    #             copy_str += char
    #     f.write(copy_str)
    ans = []
    if os.path.isfile(os.path.join(module_dir, 'pom.xml')):
        ans.append(os.path.join(module_dir, 'pom.xml'))
    for file in os.listdir(module_dir):
        full_path = os.path.join(module_dir, file)
        if os.path.isdir(full_path):
            ans.extend(get_all_pom_paths(full_path))
    return ans
str
# Changes surefire version in a pom
def change_surefire_ver(module, version):
    poms = get_all_pom_paths(module)
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
            change_plugin_version_if_exists(plugins_tag,'maven-surefire-plugin', version)
        os.remove(pom)
        with open(pom, 'w+') as f:
            str = xmlFile.toprettyxml()
            copy_str = ''
            for char in str[::]:
                if 125 < ord(char):
                    copy_str += 'X'
                else:
                    copy_str += char
            f.write(copy_str)

        # with open(pom, 'r') as old_file:
        #     lines = old_file.readlines()
        # it = iter(lines)
        # for line in it:
        #     if '<plugins>' in line:
        #         new_file_lines.append(line)
        #         line =next(it)
        #         while not line == '<plugins>':
        #             new_file_lines.append(line)
        #             if '<plugin>' in line:
        #                 line = next(it)
        #                 new_file_lines.append(line)
        #                 curr_plugin = []
        #                 while not line == '<plugin>':
        #                     curr_plugin.append(line)
        #                     line = next(it)
        #                 curr_plugin.append(line)
        #                 if any(['<artifactId>maven-surefire-plugin</artifactId>' in l for l in curr_plugin ]):
        #                     for l in curr_plugin:
        #                         if '<version>' in l:
        #                             curr_plugin.remove(l)
        #                             break
        #                     num_of_spaces = len(curr_plugin[0]) - len(len(curr_plugin[0]).lstrip)
        #                     curr_plugin.add(''*num_of_spaces+'<version>'+version+'</version>')
        #                 new_file_lines.extend(curr_plugin)
        #         new_file_lines.append(line)
        #     else:
        #         new_file_lines.append(line)
    x=1

# changes the plugin version of 'plugin_artifact_id' to 'version'. Does nothing if the 'plugin_artifact_id' is not in plugins_tag
def change_plugin_version_if_exists(plugins_tag, plugin_artifact_id, version):
    plugin_p = None
    for plugin in plugins_tag.getElementsByTagName('plugin'):
        arifact_id_sing = list(filter(lambda child: child.localName == 'artifactId', plugin.childNodes))
        if len(arifact_id_sing) == 0:
            return
        assert len(arifact_id_sing) == 1
        if arifact_id_sing[0].firstChild.data == plugin_artifact_id:
            plugin_p = plugin
            break
    if plugin_p == None:
        return
    version_v = None
    surefire_version_sing = list(
        filter(lambda child: child.localName == 'version', plugin_p.childNodes))
    if len(surefire_version_sing) == 0:
        new_ver = plugin_p.ownerDocument.createElement(tagName='version')
        new_ver_text = new_ver.ownerDocument.createTextNode(version)
        new_ver.appendChild(new_ver_text)
        plugin_p.appendChild(new_ver)
        surefire_version_sing = [new_ver]
    assert len(surefire_version_sing) == 1
    version_v = surefire_version_sing[0]
    version_v.firstChild.data = version








class TestParserException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
