import logging

import javalang
import os
import re
import xml.etree.ElementTree as ET

from javalang.parser import JavaSyntaxError
from pathlib import Path
import javadiff


class TestClass(object):
    def __init__(self, file_path, repo_path):
        self._path = os.path.realpath(file_path)
        self._module = self.find_module(self._path, repo_path)
        self._mvn_name = self.generate_mvn_name()
        self._testcases = []
        self._report = None
        self._id = '#'.join([os.path.basename(self.module), self.mvn_name])
        with open(self._path, 'r') as src_file:
            try:
                contents = src_file.read()
                tokens = list(javalang.tokenizer.tokenize(contents))
                parser = javalang.parser.Parser(tokens)
                self._tree = parser.parse()
                self.source_file = javadiff.SourceFile.SourceFile(contents, self._path, analyze_source_lines=False)
                for method in self.source_file.methods.values():
                    if self.is_valid_testcase(method):
                        self._testcases.append(TestCase(method, self))
            except UnicodeDecodeError as e:
                raise TestParserException('Java file parsing problem:' + '\n' + str(e))
            except JavaSyntaxError as e:
                logging.info(str(e) + " java parsing problem in file {}".format(src_file.name))
                self._tree = javalang.parse.parse('')
            except Exception as e:
                logging.info(str(e) + " java parsing problem in file {}".format(src_file.name))
                self._tree = javalang.parse.parse('')

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
            self.report = TestClassReport(self.get_report_path(), self.module)
            for t in self.testcases:
                self.attach_report_to_testcase(t)
            return True
        except TestParserException:
            return False

    def clear_report(self):
        self.report = None
        for t in self.testcases:
            t.clear_report()

    def find_module(self, file_path, repo_path):
        parent_dir = os.path.dirname(file_path)
        is_root = False
        while not is_root:
            if os.path.isfile(os.path.join(parent_dir, 'pom.xml')) or os.path.isfile(os.path.join(parent_dir, 'project.xml')):
                return parent_dir
            else:
                tmp = os.path.dirname(parent_dir)
                is_root = tmp == os.path.dirname(repo_path)
                parent_dir = tmp
        raise TestParserException(file_path + ' is not part of a maven module')

    def is_valid_testcase(self, method):
        return method.method_name.lower() != 'setup' and method.method_name.lower() != 'teardown' and \
               len(method.parameters) == 0 and hasattr(method, 'return_type') and getattr(method, 'return_type') == None

    def generate_mvn_name(self):
        relpath = self.get_testclass_rel_path()
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

    def get_testclass_rel_path(self):
        if is_evosuite_test_class(self.src_path) and '.evosuite' in Path(self.src_path).parts:
            return os.path.relpath(self.src_path, self.module + '\\.evosuite\\best-tests').replace('.java', '')
        return os.path.relpath(self.src_path, self.module + '\\src\\test\\java').replace('.java', '')


class TestCase(object):
    def __init__(self, method, parent):
        self._parent = parent
        self._method = method
        self._mvn_name = self.parent.mvn_name + '.' + self.method.method_name
        self._id = self._method.id
        self._report = None
        self._start_line = self.method.start_line
        self._end_line = self.method.end_line

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
        if len(self.method.body) == len(other.method.body):
            i = 0
            while i < len(self.method.body):
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
        return line in self.method.method_used_lines

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
            i += 1
        if open_position[0] == -1 or open_position[1] == -1:
            return -1
        i = 1
        is_string = False
        for line in lines:
            if i < open_position[0]:
                i += 1
                continue
            j = 1
            for letter in line:
                if i == open_position[0] and j <= open_position[1]:
                    j += 1
                    continue
                if '"' == letter: is_string = not is_string
                if is_string: continue
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


class TestClassReport(object):
    def __init__(self, xml_doc_path, modlue_path, observed_tests=None):
        self.xml_path = xml_doc_path
        self.observed_tests = observed_tests
        self.success_testcases = []
        self.failed_testcases = []
        self._testcases = []
        self._time = 0.0
        self.maven_multiModuleProjectDirectory = ''
        self._module_path = modlue_path
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        self._name = observed_tests[0].classname
        self._src_file_path = self.parse_src_path()
        for testcase in observed_tests:
            m_test = TestCaseReport(testcase, self)
            if m_test.passed:
                self.success_testcases.append(m_test)
            else:
                self.failed_testcases.append(m_test)
            self._testcases.append(m_test)
            self._time += m_test.time
        # properties_root = root.find('properties')
        # properties = properties_root.findall('property')
        # for property in properties:
        #     if property.get('name') == 'maven.multiModuleProjectDirectory':
        #         self.maven_multiModuleProjectDirectory = property.get('value')

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
        self._name = self.testcase_tag.full_name
        self.test_result = testcase
        self._time = self.test_result.time
        self._passed = self.test_result.is_passed()
        self._failed = False
        self._has_error = False
        self._failed = self.testcase_tag.result = 'failure'
        self._has_error = self.testcase_tag.result = 'error'

    @property
    def time(self):
        return self._time

    @property
    def name(self):
        return self._name

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


def is_evosuite_test_class(src_path):
    return '.evosuite' in Path(src_path).parts or os.path.basename(src_path).endswith('_ESTest_scaffolding.java') or os.path.basename(src_path).endswith('_ESTest.java')


class TestParserException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)
