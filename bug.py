import copy
import csv
import os
import pickle
import re
import shutil
import traceback
from pathlib import Path

from enum import Enum
# from sfl_diagnoser.Diagnoser import diagnoserUtils


class Bug(object):
    def __init__(self, issue_key, commit_hexsha, parent_hexsha, fixed_testcase, bugged_testcase, type, valid, desc,
                 traces=[], bugged_components=[], extra_desc = ''):
        self._issue_key = issue_key
        self._commit_hexsha = commit_hexsha
        self._parent_hexsha = parent_hexsha
        self._fixed_testcase = fixed_testcase
        self._bugged_testcase = bugged_testcase
        self._module = os.path.basename(bugged_testcase.module)
        self._type = type
        self._desc = desc
        self._extra_desc = extra_desc
        self._valid = valid
        self._traces = traces
        self._bugged_components = bugged_components
        self._has_annotations = 'Test' in list(map(lambda a: a.name, self._bugged_testcase.method.annotations))

    @property
    def issue(self):
        return self._issue_key

    @property
    def commit(self):
        return self._commit_hexsha

    @property
    def parent(self):
        return self._parent_hexsha

    @property
    def bugged_testcase(self):
        return self._bugged_testcase

    @property
    def fixed_testcase(self):
        return self._bugged_testcase

    @property
    def traces(self):
        return self._traces

    @property
    def bugged_components(self):
        return self._bugged_components

    @property
    def desctiption(self):
        return self._desc

    @property
    def type(self):
        return self._type

    @property
    def valid(self):
        return self._valid

    @property
    def has_test_annotation(self):
        return self._has_annotations

    @property
    def module(self):
        return self._module

    @property
    def extra_desc(self):
        return self._extra_desc

    def __str__(self):
        return 'type: ' + self.type.value + ' ,issue: ' + self.issue + ' ,commit: ' + self._commit_hexsha + ' ,parent: ' + self.parent + ' ,test: ' + self.bugged_testcase.mvn_name + ' description: ' + str(
            self._desc) +' ,extra description: '+str(self._extra_desc)


class Bug_data_handler(object):
    def __init__(self, path):
        self._path = path
        self._valid_bugs_csv_handler = Bug_csv_report_handler(os.path.join(self._path, 'valid_bugs.csv'))
        self._invalid_bugs_csv_handler = Bug_csv_report_handler(os.path.join(self._path, 'invalid_bugs.csv'))
        self._time_csv_handler = Time_csv_report_handler(os.path.join(self._path, 'times.csv'))

    @property
    def path(self):
        return self._path

    # Adds bug the data
    def add_bug(self, bug):
        if bug.valid:
            self._valid_bugs_csv_handler.add_bug(bug)
        else:
            self._invalid_bugs_csv_handler.add_bug(bug)
        self._store_bug(bug)

    # Adds row to the time tanle
    def add_time(self, issue_key, commit_hexsha, module, time, root_module, desctiption=''):
        self._time_csv_handler.add_row(issue_key, commit_hexsha, os.path.basename(module), time,
                                       classify_report_description(desctiption))
        if not desctiption == '':
            self._store_description(desctiption, issue_key, commit_hexsha, module, root_module)

    # Stores bug in it's direcrtory
    def _store_bug(self, bug):
        path_to_bug_testclass = self.get_bug_testclass_path(bug)
        if not os.path.exists(path_to_bug_testclass):
            os.makedirs(path_to_bug_testclass)
        bug_path = self.get_bug_path(bug)
        with open(bug_path, 'wb') as bug_file:
            pickle.dump(bug, bug_file, protocol=2)
        if len(bug.traces) > 0 and len(bug.bugged_components) > 0:
            try:
                matrix_path = os.path.join(path_to_bug_testclass, 'Matrix_' + bug.bugged_testcase.method.name + '.txt')
                diagnoserUtils.write_planning_file(
                    out_path=matrix_path,
                    bugs=bug.bugged_components,
                    tests_details=[(bug.bugged_testcase.mvn_name, bug.traces, int(bug.bugged_testcase.passed))]
                )
            except Exception as e:
                raise BugError(msg='Failed to create the matrix. Error:\n' + e.msg + '\n' + traceback.format_exc())

    # Adds bugs to the csv file
    def add_bugs(self, bugs):
        self._valid_bugs_csv_handler.add_bugs(list(filter(lambda b: b.valid, bugs)))
        self._invalid_bugs_csv_handler.add_bugs(list(filter(lambda b: not b.valid, bugs)))
        for bug in bugs:
            try:
                self._store_bug(bug)
            except BugError as e:
                raise e

    # Attach reports to the testclasses directories
    def attach_reports(self, issue, commit, testcases):
        testclasses = []
        for testcase in testcases:
            if not testcase.parent in testclasses:
                testclasses.append(testcase.parent)
        for testclass in testclasses:
            testclass_path = self.get_testclass_path(issue.key, commit.hexsha, testclass.id)
            report_copy_path = os.path.join(testclass_path, os.path.basename(testclass.get_report_path()))
            os.system(
                'copy ' + testclass.get_report_path().replace('/', '\\') + ' ' + report_copy_path.replace('/', '\\'))

    # Gets the path to the bug's testclass directory
    def get_bug_testclass_path(self, bug):
        return os.path.join(self.path, '/'.join([bug.issue, bug.commit, bug.bugged_testcase.parent.id]))

    # Gets the path to the directory of the testclass in the given commit and issue
    def get_testclass_path(self, issue_key, commit_hexsha, testclass_id):
        return os.path.join(self.path, '/'.join([issue_key, commit_hexsha, testclass_id]))

    # Gets the path to the directory of the testclass in the given commit and issue
    def get_commit_path(self, issue_key, commit_hexsha):
        return reduce(
            lambda acc, curr: os.path.join(acc, curr),
            [self.path, issue_key, commit_hexsha],
            []
        )

    # Gets the path to the directory of the testclass in the given commit and issue
    def get_bug_path(self, bug):
        return os.path.join(self.get_bug_testclass_path(bug), bug.bugged_testcase.method.name + '.pickle')

    # Sets up dirctories for bug results
    def set_up_bug_dir(self, issue, commit, testclasses, module, root_module):
        ans = {}

        def set_up_issue_dir():
            path_to_bug_dir = os.path.join(self.path, issue.key)
            if not os.path.isdir(path_to_bug_dir):
                os.makedirs(path_to_bug_dir)
            return path_to_bug_dir

        def set_up_commit_dir(path_to_bug_dir):
            path_to_bug_dir = os.path.join(path_to_bug_dir, commit.hexsha)
            if not os.path.isdir(path_to_bug_dir):
                os.makedirs(path_to_bug_dir)
            return path_to_bug_dir

        def set_up_pom_dir(path_to_bug_dir):
            path_to_pom_dir = os.path.join(path_to_bug_dir, os.path.basename(module) + '#pom')
            if not os.path.isdir(path_to_pom_dir):
                os.makedirs(path_to_pom_dir)
            return path_to_pom_dir

        def set_up_module_inspection_dir():
            path = os.path.join(self.path, reduce_module_inspection_path(issue.key, commit.hexsha, module, root_module))
            if not os.path.isdir(path):
                os.makedirs(path)

        path_to_bug_dir = set_up_issue_dir()
        path_to_commit_dir = set_up_commit_dir(path_to_bug_dir)
        path_to_pom_dir = set_up_pom_dir(path_to_commit_dir)
        set_up_module_inspection_dir()
        ans.update(self.set_up_class_dirs(testclasses, path_to_commit_dir))
        ans[module] = path_to_pom_dir
        return ans

    def cast_tests(self, issue, commit, testclasses):
        return self.set_up_class_dirs(
            testclasses=testclasses,
            path_to_commit_dir=reduce(lambda acc, curr: os.path.join(acc, curr), [self.path, issue.key, commit.hexsha])
        )

    def set_up_class_dirs(self, testclasses, path_to_commit_dir):
        ans = {}
        for testclass in testclasses:
            path_to_testclass_dir = os.path.join(path_to_commit_dir, testclass.id)
            if not os.path.isdir(path_to_testclass_dir):
                os.makedirs(path_to_testclass_dir)
                ans[testclass.id] = path_to_testclass_dir
        return ans

    # Gets all the data from fb_path
    def fetch_all_data(self, db_path):
        copytree(db_path, self.path)

    def fetch_issue_data(self, db_path, issue):
        copytree(os.path.join(db_path, issue), os.path.join(self.path, issue))

    # Gets all the bugs in issue_key in fixed commit_hexsha
    def get_bugs(self, issue_key, commit_hexsha):
        ans = []
        issue_dir = os.path.join(self.path, issue_key)
        commit_dir = os.path.join(issue_dir, commit_hexsha)
        if not os.path.isdir(commit_dir):
            return ans
        for filename in os.listdir(commit_dir):
            full_file_path = os.path.join(commit_dir, filename)
            if os.path.isdir(full_file_path):
                ans += self.get_testclass_bugs(full_file_path)
        return ans

    # Returns all teh bugs in testcalss path
    def get_testclass_bugs(self, testclass_path):
        ans = []
        for filename in os.listdir(testclass_path):
            if filename.endswith(".pickle"):
                full_path = os.path.join(testclass_path, filename)
                with open(full_path, 'rb') as bug_file:
                    ans.append(pickle.load(bug_file))
        return ans

    # Gets the patch applying bug
    def get_patch(self, bug):
        testclass_path = self.get_testclass_path(bug.issue, bug.commit, bug.bugged_testcase.parent.id)
        for filename in os.listdir(testclass_path):
            if filename.endswith(".patch"):
                return os.path.join(testclass_path, filename)

    # Gets valid_bugs_tuiplles
    def get_valid_bugs(self):
        ans = []
        with open(self._valid_bugs_csv_handler.path, 'r') as f:
            reader = csv.reader(f)
            ans = list(reader)
        return ans

    # Gets invalid_bugs_tuiplles
    def get_invalid_bugs(self):
        ans = []
        with open(self._invalid_bugs_csv_handler.path, 'r') as f:
            reader = csv.reader(f)
            ans = list(reader)
        return ans

    # Gets invalid_bugs_tuiplles
    def get_times(self):
        ans = []
        with open(self._time_csv_handler.path, 'r') as f:
            reader = csv.reader(f)
            ans = list(reader)
        return ans

    def get_scaffolding_dir(self, bug):
        return self.get_testclass_path(bug.issue, bug.commit, bug.bugged_testcase.parent.id + '_scaffolding')

    def get_file_patch(self, file_dir):
        for filename in os.listdir(file_dir):
            if filename.endswith(".patch"):
                return os.path.join(file_dir, filename)

    def get_poms_patches(self, bug):
        def get_pom_patch_path(pom_dir):
            return os.path.join(pom_dir, 'patch.patch')

        def is_pom_path(path):
            return '#pom' in path

        commit_path = self.get_commit_path(issue_key=bug.issue, commit_hexsha=bug.commit)
        return reduce(
            lambda acc, curr: acc + [os.path.join(commit_path, get_pom_patch_path(curr))],
            filter(lambda x: is_pom_path(x), os.listdir(commit_path)),
            []
        )

    def _store_description(self, description, issue_key, commit_hexsha, module, root_module):
        module_inspection_path = os.path.join(self.path, reduce_module_inspection_path(issue_key, commit_hexsha, module,
                                                                                       root_module))
        with open(os.path.join(module_inspection_path, 'description.txt'), 'w+') as desc_file:
            desc_file.write(description)
            desc_file.write('\n' + traceback.format_exc())


class Bug_csv_report_handler(object):
    def __init__(self, path):
        self._writer = None
        self._path = path
        self._fieldnames = ['valid', 'type', 'issue', 'module', 'commit', 'parent', 'testcase', 'has_test_annotation',
                             'traces', 'bugged_components','description', 'extra_description']
        if not os.path.exists(path):
            with open(self._path, 'w+') as csv_output:
                writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames, lineterminator='\n')
                writer.writeheader()

    # Adds bug to the csv file
    def add_bug(self, bug):
        with open(self._path, 'a') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames, lineterminator='\n')
            writer.writerow(self.generate_csv_tupple(bug))

    # Adds bugs to the csv file
    def add_bugs(self, bugs):
        with open(self._path, 'a') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames, lineterminator='\n')
            for bug in bugs:
                writer.writerow(self.generate_csv_tupple(bug))

    # Generated csv bug tupple
    def generate_csv_tupple(self, bug):
        return {'valid': bug.valid,
                'type': bug.type.value,
                'issue': bug.issue,
                'module': bug.module,
                'commit': bug.commit,
                'parent': bug.parent,
                'testcase': bug.bugged_testcase.mvn_name,
                'has_test_annotation': bug.has_test_annotation,
                'description': bug.desctiption,
                'traces': bug.traces,
                'bugged_components': bug.bugged_components,
                'extra_description':bug.extra_desc
                }

    @property
    def path(self):
        return self._path


class Time_csv_report_handler(object):
    def __init__(self, path):
        self._writer = None
        self._path = path
        self._fieldnames = ['issue', 'commit', 'module', 'time', 'description']
        if not os.path.exists(path):
            with open(self._path, 'w+') as csv_output:
                writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames, lineterminator='\n')
                writer.writeheader()

    # Adds bug to the csv file
    def add_row(self, issue_key, commit_hexsha, module, time, description_type):
        with open(self._path, 'a') as csv_output:
            writer = csv.DictWriter(csv_output, fieldnames=self._fieldnames, lineterminator='\n')
            writer.writerow(self.generate_csv_tupple(issue_key, commit_hexsha, module, time, description_type))

    # Generated csv bug tupple
    def generate_csv_tupple(self, issue_key, commit_hexsha, module, time, description):
        return {
            'issue': issue_key,
            'commit': commit_hexsha,
            'module': module,
            'time': time,
            'description': description
        }

    @property
    def path(self):
        return self._path


class BugError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class NoAssociatedChangedClasses(BugError):
    def __init__(self, msg):
        super(NoAssociatedChangedClasses, super).__init__(msg=msg)


class TooManyClassesToGenerateTestsFor(BugError):
    def __init__(self, msg, amount):
        self.amount = amount
        super(TooManyClassesToGenerateTestsFor, self).__init__(msg=msg)

    def __str__(self):
        return super(TooManyClassesToGenerateTestsFor, self).__str__() + '\n' + 'Too many classes! \n amount:{}'.format(
            self.amount)


invalid_comp_error_desc = 'testcase genrated compilation error when patched'
invalid_rt_error_desc = 'testcase genrated runtime error when tested'
invalid_passed_desc = 'testcase passed in parent'
invalid_not_fixed_failed_desc = 'testcase failed in commit'
invalid_not_fixed__error_desc = 'testcase generated runtime error in commit'


class Bug_type(Enum):
    DELTA = "Delta"
    DELTA_2 = "Delta^2"
    DELTA_3 = "Delta^3"
    REGRESSION = "Regression"
    GEN = "Auto-generated"

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


class Description_type(Enum):
    COMP_ERROR = "Compilation failure"
    DEPENDENCIES_ERROR = "Dependencies resolution failure"
    TIMEOUT_ERROR = 'Timeout failure'
    GENERATED_NO_TESTS_ERROR = 'Generated no tests'
    NO_ASSOCIATED_CLASS = 'No classes associated to this module'
    TOO_MANY_CLASSES_CLASS = 'Too many classes to generate tests for'
    UNEXPECTED = 'Unexpected'
    GIT_ERROR = 'Git error'
    SUCESS = 'Success'
    NO_POM_FILE = 'No pom file'
    ANIMAL_SNIFFER_CHECK = 'Failed to execute goal org.codehaus.mojo:animal-sniffer-maven-plugin:1.13:check'
    NOT_PART_OF_MVN_MODULE = 'Not part of maven module'
    NO_CHANGED_METHODS = 'No changed methods'
    OLD_POM_STRUCT = 'Old pom struct'

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value


def create_bug(issue, commit, parent, testcase, parent_testcase, type, traces, bugged_components):
    if testcase.passed and parent_testcase.failed:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase, type=type, valid=True, desc='',
                   traces=traces, bugged_components=bugged_components)
    elif testcase.passed and parent_testcase.has_error:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type, valid=False, desc=invalid_rt_error_desc,
                   traces=traces, bugged_components=bugged_components, extra_desc=parent_testcase.get_error())
    elif testcase.passed and parent_testcase.passed:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type, valid=False, desc=invalid_passed_desc, traces=traces, bugged_components=bugged_components)
    elif testcase.failed:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type, valid=False, desc=invalid_not_fixed_failed_desc, traces=traces,
                   bugged_components=bugged_components)
    elif testcase.has_error:
        return Bug(issue_key=issue.key, commit_hexsha=commit.hexsha, parent_hexsha=parent.hexsha,
                   fixed_testcase=testcase, bugged_testcase=parent_testcase,
                   type=type, valid=False, desc=invalid_not_fixed__error_desc + ' ' + testcase.get_error(),
                   traces=traces, bugged_components=bugged_components)
    else:
        assert 0 == 1


# copy directory from stackoverflow
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s) and not os.path.isdir(d):
            shutil.copytree(s, d, symlinks, ignore)
        elif os.path.isfile(s) and not os.path.isfile(d):
            shutil.copy2(s, d)


# Returns the ype of the bug
def determine_type(testcase, delta_testcases, gen_commit_valid_testcases):
    if testcase in gen_commit_valid_testcases:
        return Bug_type.GEN
    elif testcase in delta_testcases:
        return Bug_type.DELTA
    else:
        return Bug_type.REGRESSION


def is_comp_err(desctiption):
    return 'Compilation failure' in desctiption or '[ERROR] COMPILATION ERROR :' in desctiption


def is_dep_err(desctiption):
    return 'Could not resolve dependencies' in desctiption


def is_timeout_err(desctiption):
    return 'MVNTimeoutError' in desctiption or 'TIMEOUT!' in desctiption


def is_no_tests_gen_err(desctiption):
    return 'Generated no tests' in desctiption


def is_no_class_associated_err(desctiption):
    return 'No classes associated this module' in desctiption


def is_git_error_err(desctiption):
    return 'GitCommandError' in desctiption


def is_too_many_classes_err(desctiption):
    return 'Too many classes!' in desctiption


def is_no_pom_file_err(desctiption):
    return 'No pom file in module' in desctiption


def is_animal_sniffer_check_err(desctiption):
    return re.match('[\s\S]* to execute goal org.codehaus.mojo:animal-sniffer-maven-plugin:.*:check', desctiption)


def is_not_part_of_mvn_module_err(desctiption):
    return 'is not part of a maven module' in desctiption

def is_no_changed_methods(desctiption):
    return 'No changed methods' in desctiption


def is_old_pom_struct(desctiption):
    return 'ExpatError: must not undeclare prefix: line 1, column 0' in desctiption


def classify_report_description(desctiption):
    if desctiption == '':
        return Description_type.SUCESS
    elif is_comp_err(desctiption):
        return Description_type.COMP_ERROR
    elif is_dep_err(desctiption):
        return Description_type.DEPENDENCIES_ERROR
    elif is_timeout_err(desctiption):
        return Description_type.TIMEOUT_ERROR
    elif is_no_tests_gen_err(desctiption):
        return Description_type.GENERATED_NO_TESTS_ERROR
    elif is_no_class_associated_err(desctiption):
        return Description_type.NO_ASSOCIATED_CLASS
    elif is_git_error_err(desctiption):
        return Description_type.GIT_ERROR
    elif is_too_many_classes_err(desctiption):
        return Description_type.TOO_MANY_CLASSES_CLASS
    elif is_no_pom_file_err(desctiption):
        return Description_type.NO_POM_FILE
    elif is_animal_sniffer_check_err(desctiption):
        return Description_type.ANIMAL_SNIFFER_CHECK
    elif is_not_part_of_mvn_module_err(desctiption):
        return Description_type.NOT_PART_OF_MVN_MODULE
    elif is_no_changed_methods(desctiption):
        return Description_type.NO_CHANGED_METHODS
    elif is_old_pom_struct(desctiption):
        return Description_type.OLD_POM_STRUCT
    else:
        return Description_type.UNEXPECTED


def reduce_module_inspection_path(issue_key, commit_hexsha, module, root_module):
    return reduce(
        lambda acc, curr: os.path.join(acc, curr),
        Path(os.path.relpath(module, root_module)).parts,
        reduce(lambda acc, curr: os.path.join(acc, curr), [issue_key, commit_hexsha, 'root'])
    )
