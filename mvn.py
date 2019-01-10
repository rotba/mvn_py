import os
import subprocess
from threading import Timer
from cStringIO import StringIO
from bug  import BugError
import TestObjects
import CompilationErrorObject
import sys
tracer_dir  = path = os.path.join(os.path.dirname(__file__),r'tracer\java_tracer\tracer')
dict_super_sub_tags = {'dependencies':'dependency',
                       'mailingLists':'mailingList',
                       'licenses':'license',
                       'developers':'developer',
                       'plugins': 'plugin'}
# Returns the testcases generated compilation error in the maven build report
def get_compilation_error_testcases(compilation_error_report):
    ans = []
    for line in compilation_error_report:
        if is_error_report_line(line):
            compilation_error_testcase = get_error_test_case(line)
            if not compilation_error_testcase == None and not compilation_error_testcase in ans:
                ans.append(compilation_error_testcase)
    return ans


# Returns list of compilation error reports objects
def get_compilation_errors(compilation_error_report):
    ans = []
    for line in compilation_error_report:
        if is_error_report_line(line):
            error = CompilationErrorObject.CompilationErrorReport(line)
            if not error in ans:
                ans.append(error)
    return ans


# Returns lines list describing the compilation errors in th build report
def get_compilation_error_report(build_report):
    ans = []
    report_lines = build_report.splitlines()
    i = 0
    while i < len(report_lines):
        if is_start_of_compilation_error_report(report_lines[i]):
            ans.append(report_lines[i])
            if '[ERROR] COMPILATION ERROR :' in report_lines[i]:
                ans.append(report_lines[i + 1])
                i += 1
            i += 1
            while not end_of_compilation_errors(report_lines[i]):
                ans.append(report_lines[i])
                i += 1
                if i == len(report_lines)-1:
                    break
        elif report_lines[i].endswith('Compilation failure'):
            while i < len(report_lines) and not end_of_compilation_errors(report_lines[i]):
                if is_error_report_line(report_lines[i]):
                    ans.append(report_lines[i])
                i += 1
        else:
            i += 1
    return ans

# Returns true if the line is a start of a compilation error report
def is_start_of_compilation_error_report(line):
    return '[ERROR] COMPILATION ERROR :' in line or\
          ('[ERROR] Failed to execute goal' in line and 'Compilation failure' in line)



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


# Returns true if the given line ends the complation error report
def end_of_compilation_errors(line):
    return '[INFO] -------------------------------------------------------------' in line or\
           '[INFO] Build failures were ignored.' in line or '[ERROR] -> [Help 1]' in line



# Returns true iff the given report line is a report of compilation error file
def is_error_report_line(line):
    if line.startswith('[ERROR]'):
        words = line.split(' ')
        if len(words) < 2:
            return False
        if len(words[1]) < 1:
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
    with open('all_tests.csv', 'a') as csvfile:
        fieldnames = ['test_name', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, lineterminator='\n')
        writer.writeheader()
        for test in tests:
            writer.writerow({'test_name': test.name, 'time': str(test.time)})


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

# Genrated maven class name
def generate_mvn_class_names(src_path, module):
    if 'src\\test' in src_path or 'src/test' in src_path or r'src\test' in src_path:
        relpath = os.path.relpath(src_path, module + '\\src\\test\\java').replace('.java', '')
    else:
        relpath = os.path.relpath(src_path, module + '\\src\\main\\java').replace('.java', '')
    while relpath.startswith('..\\'):
        relpath = relpath[3:]
    return relpath.replace('\\', '.')


# changes the plugin version of 'plugin_artifact_id' to 'version'. Does nothing if the 'plugin_artifact_id' is not in plugins_tag
def add_plugin_configuration_argline(plugins_tag, plugin_artifact_id, content):
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
    surefire_configuration_sing = list(
        filter(lambda child: child.localName == 'configuration', plugin_p.childNodes))
    if len(surefire_configuration_sing) == 0:
        new_configuration = plugin_p.ownerDocument.createElement(tagName='configuration')
        plugin_p.appendChild(new_configuration)
        surefire_configuration_sing = [new_configuration]
    assert len(surefire_configuration_sing) == 1
    configuration_tag = surefire_configuration_sing[0]
    surefire_argLine_sing = list(
        filter(lambda child: child.localName == 'argLine', configuration_tag.childNodes))
    if len(surefire_argLine_sing) == 0:
        new_argLine = configuration_tag.ownerDocument.createElement(tagName='argLine')
        new_argLine_text = new_argLine.ownerDocument.createTextNode('')
        new_argLine.appendChild(new_argLine_text)
        configuration_tag.appendChild(new_argLine)
        surefire_argLine_sing = [new_argLine]
    new_argLine = surefire_argLine_sing[0]
    new_argLine.firstChild.data = content


# Reutns tests object in the given tests directory
def parse_tests(tests_dir):
    ans = []
    for filename in os.listdir(tests_dir):
        abs_path = os.path.join(tests_dir, filename)
        if os.path.isdir(abs_path):
            ans.extend(parse_tests(abs_path))
        elif filename.endswith(".java"):
            ans.append(TestObjects.TestClass(abs_path))
    return ans


def wrap_mvn_cmd(cmd, time_limit = sys.maxint):
    output_tmp_files_dir = os.path.join('tmp_files','stdout_duplication')
    if not os.path.isdir(output_tmp_files_dir):
        os.makedirs(output_tmp_files_dir)
    tmp_file_path = os.path.join(output_tmp_files_dir,'tmp_file.txt')
    with open(tmp_file_path, 'w+') as tmp_f:
        proc = subprocess.Popen(cmd, shell=True,stdout=tmp_f)
        t = Timer(time_limit, kill, args=[proc])
        t.start()
        proc.wait()
        t.cancel()
    with open(tmp_file_path, "r") as tmp_f:
        build_report = tmp_f.read()
        print(build_report)
    if not time_limit == sys.maxint and not ('[INFO] BUILD SUCCESS' in build_report or '[INFO] BUILD FAILURE' in build_report):
        raise MVNTimeoutError('Build took too long', build_report)
    # if not ('[INFO] BUILD SUCCESS' in build_report or '[INFO] BUILD FAILURE' in build_report):
    #     raise MVNError('Build took too long', build_report)
    return build_report.replace('\\n','\n')

def wrap_mvn_cmd_1(cmd, time_limit = sys.maxint):
    proc = subprocess.Popen(cmd, shell=True, stdout= subprocess.PIPE)
    t = Timer(sys.maxint, kill, args=[proc])
    t.start()
    proc.wait()
    t.cancel()
    (out, err) = proc.communicate()
    if not time_limit == sys.maxint and not ('[INFO] BUILD SUCCESS' in build_log or '[INFO] BUILD FAILURE' in build_log):
        raise MVNError('Build took too long', build_log)
    return build_log

def wrap_mvn_cmd_3(cmd, time_limit = sys.maxint):
    sys.stderr.flush()
    sys.stdout.flush()
    olderr, oldout = sys.stderr, sys.stdout
    try:
        sys.stderr = StringIO()
        sys.stdout = StringIO()
        try:
            proc = subprocess.Popen(cmd, shell=True)
            t = Timer(time_limit, kill, args=[proc])
            t.start()
            proc.wait()
            t.cancel()
        finally:
            sys.stderr.seek(0)
            sys.stdout.seek(0)
            err = sys.stderr.read()
            build_log = sys.stdout.read()
    finally:
        sys.stderr = olderr
        sys.stdout = oldout
    if not time_limit == sys.maxint and not ('[INFO] BUILD SUCCESS' in build_log or '[INFO] BUILD FAILURE' in build_log):
        raise MVNError('Build took too long', build_log)
    return build_log

def duplicate_stdout(proc, file):
    while (True):
        line = proc.readline()
        if line == '':
            break
        sys.stdout.write(line)
        file.write(line)

# Define to kill a maven process if it tatkes too long
def kill(p):
    p.kill()

class MVNError(Exception):
    def __init__(self, msg, report = ''):
        self.msg = msg
        self.report  = report
    def __str__(self):
        return repr(self.msg+'\n'+self.report)

class MVNTimeoutError(MVNError):
    pass


def has_compilation_error(build_report):
    compilation_error_report = get_compilation_error_report(build_report)
    return len(compilation_error_report)>0

def tag_uri_and_name(elem):
    if elem.tag[0] == "{":
        uri, ignore, tag = elem.tag[1:].partition("}")
    else:
        uri = ''
        tag = elem.tag
    return uri, tag