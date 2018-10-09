import os
import TestObjects
import CompilationErrorObject

# Returns the testcases generated compilation error in the maven build report
import sys


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


# Returns true if the given line ends the complation error report
def end_of_compilation_errors(line):
    return '[INFO] -------------------------------------------------------------' in line


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
def wrap_mvn_cmd(cmd):
    with os.popen(cmd) as proc:
        tmp_file_path = 'tmp_file.txt'
        with open(tmp_file_path, "w+") as tmp_file:
            duplicate_stdout(proc, tmp_file)
        with open(tmp_file_path, "r") as tmp_file:
            duplicate_stdout(proc, tmp_file)
            build_report = tmp_file.read()
    return build_report

def duplicate_stdout(proc, file):
    while (True):
        line = proc.readline()
        if line == '':
            break
        sys.stdout.write(line)
        file.write(line)
