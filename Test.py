import os
import sys
import unittest
import Repo
import TestObjects

orig_wd = os.getcwd()
class Test_mvnpy(unittest.TestCase):
    # os.system('mvn clean install -f '+os.getcwd() + r'\static_files\MavenProj')
    # os.system('mvn clean install -f ' + os.getcwd() + r'\static_files\tika_1')
    def setUp(self):
        os.chdir(orig_wd)
        test_doc_1 = os.getcwd() + r'\static_files\TEST-org.apache.tika.cli.TikaCLIBatchCommandLineTest.xml'
        test_doc_2 = os.getcwd() + r'\static_files\MavenProj\sub_mod_2\target\surefire-reports\TEST-p_1.AssafTest.xml'
        self.test_report_1 = TestObjects.TestClassReport(test_doc_1, '')
        self.test_report_2 = TestObjects.TestClassReport(test_doc_2,
                                                  os.getcwd() + r'\static_files\MavenProj\sub_mod_2')
        self.test_1 = TestObjects.TestClass(
            os.getcwd() + r'\static_files\MavenProj\sub_mod_2\src\test\java\NaimTest.java')
        self.test_2 = TestObjects.TestClass(
            os.getcwd() + r'\static_files\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java')
        self.test_2 = TestObjects.TestClass(
            os.getcwd() + r'\static_files\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java')
        self.test_3 = TestObjects.TestClass(
            os.getcwd() + r'\static_files\tika_1\src\test\java\org\apache\tika\parser\AutoDetectParserTest.java')
        self.test_4 = TestObjects.TestClass(
            os.getcwd() + r'\static_files\tika_1\src\test\java\org\apache\tika\sax\AppendableAdaptorTest.java')
        self.test_5 = TestObjects.TestClass(
            os.getcwd() + r'\static_files\tika_1\src\test\java\org\apache\tika\sax _1\AppendableAdaptorTest.java')
        self.testcase_1 = [t for t in self.test_3.testcases if t.id.endswith('None_testExcel()')][0]
        self.testcase_2 = [t for t in self.test_4.testcases if t.id.endswith('None_testAppendChar()')][0]
        self.testcase_3 = [t for t in self.test_5.testcases if t.id.endswith('None_testAppendChar()')][0]
        self.testcase_4 = [t for t in self.test_5.testcases if t.id.endswith('None_testAppendString()')][0]

    def tearDown(self):
        pass

    def test_get_path(self):
        expected_name = os.getcwd() + r'\static_files\MavenProj\sub_mod_2\src\test\java\NaimTest.java'
        self.assertEqual(self.test_1.src_path, expected_name)

    def test_get_module(self):
        expected_module_1 = os.getcwd() + r'\static_files\MavenProj\sub_mod_2'
        expected_module_2 = os.getcwd() + r'\static_files\MavenProj\sub_mod_1'
        self.assertEqual(self.test_1.module, expected_module_1,
                         str(self.test_1) + ' module should be ' + expected_module_1)
        self.assertEqual(self.test_2.module, expected_module_2,
                         str(self.test_2) + ' module should be ' + expected_module_2)

    def test_mvn_name(self):
        expected_name = 'p_1.AmitTest'
        expected_method_name = 'p_1.AmitTest#hoo'
        self.assertEqual(self.test_2.mvn_name, expected_name)
        self.assertTrue(expected_method_name in list(map(lambda m: m.mvn_name, self.test_2.testcases)))

    def test_get_testcases(self):
        expected_testcase_id = os.getcwd() + r'\static_files\MavenProj\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_hoo()'
        self.assertTrue(expected_testcase_id in list(map(lambda tc: tc.id, self.test_2.testcases)))
        self.assertEqual(len(self.test_2.testcases), 4, "p_1.AmitTest should have only one method")

    def test_get_report_path(self):
        expected_report_path = os.getcwd() + r'\static_files\MavenProj\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        self.assertEqual(self.test_2.get_report_path(), expected_report_path)

    def test_report_get_src_file_path(self):
        expected_src_file_path = os.getcwd() + r'\static_files\MavenProj\sub_mod_2\src\test\java\p_1\AssafTest.java'
        self.assertEqual(self.test_report_2.src_path, expected_src_file_path)

    def test_report_get_time(self):
        testcases = self.test_report_1.testcases;
        expected_time = 0.0
        for testcase in self.test_report_1.testcases:
            expected_time += testcase.time
        self.assertEqual(self.test_report_1.time, expected_time)

    def test_report_get_testcases(self):
        expected_testcases_names = []
        expected_testcases_names.append("testTwoDirsNoFlags")
        expected_testcases_names.append("testBasicMappingOfArgs")
        expected_testcases_names.append("testOneDirOneFileException")
        expected_testcases_names.append("testTwoDirsVarious")
        expected_testcases_names.append("testConfig")
        expected_testcases_names.append("testJVMOpts")
        for testcase in self.test_report_1.testcases:
            if "testTwoDirsNoFlags" in testcase.name:
                self.assertEqual(testcase.time, 0.071)
            elif "testBasicMappingOfArgs" in testcase.name:
                self.assertEqual(testcase.time, 0.007)
            elif "testOneDirOneFileException" in testcase.name:
                self.assertEqual(testcase.time, 0.007)
            elif "testTwoDirsVarious" in testcase.name:
                self.assertEqual(testcase.time, 0.006)
            elif "testConfig" in testcase.name:
                self.assertEqual(testcase.time, 0.006)
            elif "testJVMOpts" in testcase.name:
                self.assertEqual(testcase.time, 0.007)
            else:
                self.fail("Unexpected testcase name: " + testcase.name)
        result_testcases_names = []
        for testcase in self.test_report_1.testcases:
            result_testcases_names.append(testcase.name)
        for name in expected_testcases_names:
            i = 0
            for res_name in result_testcases_names:
                if name in res_name:
                    continue
                else:
                    i += 1
                    if i == len(result_testcases_names):
                        self.fail(name + ' not associated to ' + self.test_report_1.name)

    def test_report_is_associated(self):
        t_associated_name_1 = 'testTwoDirsNoFlags'
        t_associated_name_2 = 'TikaCLIBatchCommandLineTest'
        t_not_associated_name_1 = 'testHeyDirsNoFlags'
        t_not_associated_name_2 = 'TikaBrotherCLIBatchCommandLineTest'
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_1))
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_2))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_1))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_2))

    def test_report_is_associated(self):
        t_associated_name_1 = 'testTwoDirsNoFlags'
        t_associated_name_2 = 'TikaCLIBatchCommandLineTest'
        t_not_associated_name_1 = 'testHeyDirsNoFlags'
        t_not_associated_name_2 = 'TikaBrotherCLIBatchCommandLineTest'
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_1))
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_2))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_1))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_2))

    def test_star_line_end_line(self):
        self.assertTrue(self.testcase_1.start_line == 130, 'result - start_line : '+str(self.testcase_1.start_line))
        self.assertTrue(self.testcase_1.end_line == 132, 'result - end_line : '+str(self.testcase_1.end_line))

    @unittest.skip("Not woking")
    def test_has_the_same_code(self):
        self.assertTrue(self.testcase_2.has_the_same_code_as(self.testcase_3))
        self.assertFalse(self.testcase_2.has_the_same_code_as(self.testcase_4))

    def test_change_surefire_ver_1(self):
        module = os.path.join( os.getcwd(),r'static_files\tika')
        repo = Repo.Repo(module)
        curr_wd = os.getcwd()
        os.chdir(module)
        os.system('git checkout HEAD -f')
        mvn_help_cmd = 'mvn help:describe -DgroupId=org.apache.maven.plugins -DartifactId=maven-surefire-plugin'
        excpected_version = '2.22.0'
        poms = repo .get_all_pom_paths(module)
        repo.change_surefire_ver(excpected_version, module )
        self.assertTrue(len(poms)>0)
        for pom in poms:
            print('#### checking '+pom+' ######')
            if(os.path.normcase(os.path.join( os.getcwd(),r'tika-dotnet\pom.xml')) ==os.path.normcase(pom)):
                print('#### passing ' + pom + ' ######')
                continue
            module_path = os.path.abspath(os.path.join(pom, os.pardir))
            with os.popen(mvn_help_cmd+' -f '+module_path) as proc:
                tmp_file_path = 'tmp_file.txt'
                with open(tmp_file_path, "w+") as tmp_file:
                    duplicate_stdout(proc, tmp_file)
                with open(tmp_file_path, "r") as tmp_file:
                    duplicate_stdout(proc, tmp_file)
                    build_report = tmp_file.readlines()
                version_line_sing = list(filter(lambda l: l.startswith('Version: '),build_report))
                assert len(version_line_sing) == 1
                version_line = version_line_sing[0]
                self.assertEqual(version_line.lstrip('Version: ').rstrip('\n'),excpected_version)
        os.system('git checkout HEAD -f')
        os.chdir(curr_wd)

    def test_change_surefire_ver_2(self):
        module = os.path.join(os.getcwd(),r'static_files\commons-math')
        repo  = Repo.Repo(module)
        curr_wd = os.getcwd()
        os.chdir(module)
        os.system('git checkout 35414bc4f4ef03ef12e99c027398e5dc84682a9e -f')
        mvn_help_cmd = 'mvn help:describe -DgroupId=org.apache.maven.plugins -DartifactId=maven-surefire-plugin'
        excpected_version = '2.22.0'
        poms = repo.get_all_pom_paths(module)
        repo.change_surefire_ver(excpected_version, module)
        self.assertTrue(len(poms)>0)
        for pom in poms:
            print('#### checking '+pom+' ######')
            if(os.path.normcase(r'C:\Users\user\Code\Python\BugMiner\mvn_parsers\static_files\tika\tika-dotnet\pom.xml') ==os.path.normcase(pom)):
                print('#### passing ' + pom + ' ######')
                continue
            module_path = os.path.abspath(os.path.join(pom, os.pardir))
            with os.popen(mvn_help_cmd+' -f '+module_path) as proc:
                tmp_file_path = 'tmp_file.txt'
                with open(tmp_file_path, "w+") as tmp_file:
                    duplicate_stdout(proc, tmp_file)
                with open(tmp_file_path, "r") as tmp_file:
                    duplicate_stdout(proc, tmp_file)
                    build_report = tmp_file.readlines()
                version_line_sing = list(filter(lambda l: l.startswith('Version: '),build_report))
                assert len(version_line_sing) == 1
                version_line = version_line_sing[0]
                self.assertEqual(version_line.lstrip('Version: ').rstrip('\n'),excpected_version)
        os.chdir(curr_wd)



    def test_change_surefire_ver_3(self):
        module = os.path.join( os.getcwd(),r'static_files\tika')
        repo = Repo.Repo(module)
        curr_wd = os.getcwd()
        os.chdir(module)
        os.system('git checkout d363b828bc6e714aa5f4ffedfbd1d09e1880f9ee -f')
        mvn_help_cmd = 'mvn help:describe -DgroupId=org.apache.maven.plugins -DartifactId=maven-surefire-plugin'
        excpected_version = '2.22.0'
        poms = repo .get_all_pom_paths(module)
        repo.change_surefire_ver(excpected_version, module )
        self.assertTrue(len(poms)>0)
        for pom in poms:
            print('#### checking '+pom+' ######')
            if(os.path.normcase(os.path.join( os.getcwd(),r'tika-dotnet\pom.xml')) ==os.path.normcase(pom)):
                print('#### passing ' + pom + ' ######')
                continue
            module_path = os.path.abspath(os.path.join(pom, os.pardir))
            with os.popen(mvn_help_cmd+' -f '+module_path) as proc:
                tmp_file_path = 'tmp_file.txt'
                with open(tmp_file_path, "w+") as tmp_file:
                    duplicate_stdout(proc, tmp_file)
                with open(tmp_file_path, "r") as tmp_file:
                    duplicate_stdout(proc, tmp_file)
                    build_report = tmp_file.readlines()
                version_line_sing = list(filter(lambda l: l.startswith('Version: '),build_report))
                assert len(version_line_sing) == 1
                version_line = version_line_sing[0]
                self.assertEqual(version_line.lstrip('Version: ').rstrip('\n'),excpected_version)
        os.system('git checkout HEAD -f')
        os.chdir(curr_wd)


    def test_setup_surfire_agent(self):
        module = os.path.join( os.getcwd(),r'static_files\MavenProj')
        tracer_dir =os.path.join( os.getcwd(),r'static_files\java_tracer\tracer')
        repo_mvn_tracer = Repo.Repo(tracer_dir)
        repo = Repo.Repo(module)
        expected_agent_path = os.path.join(repo.repo_dir, 'agent.jar')
        expected_paths_path = os.path.join(repo.repo_dir, 'paths.jar')
        repo_mvn_tracer.install()
        agnet_path = os.path.join(tracer_dir, r'target\tracer-1.0.1-SNAPSHOT.jar')
        repo.setup_surefire_agent(agnet_path)
        self.assertTrue(os.path.isfile(expected_agent_path))
        self.assertTrue(os.path.isfile(expected_paths_path))
        with open(expected_paths_path,'rb') as paths:
            lines = paths.readlines()
            self.assertEqual(lines[0], os.join(os.environ['USERPROFILE'], r'.m2\repository'))
            self.assertEqual(lines[1], repo.repo_dir)
        with open(os.path.join(repo.repo_dir,'pom.xml'),'rb') as pom:
            lines = pom.readlines()
            self.assertTrue('<argLine>javaagent:{}={}</argLine>'.format(expected_agent_path,expected_paths_path), os.join(os.environ['USERPROFILE'], r'.m2\repository'))

    @unittest.skip("Important test but will require some time to validate")
    def test_get_compilation_error_testcases(self):
        print('test_get_compilation_error_testcases')
        with open(os.getcwd() + r'\static_files\test_get_compilation_error_testcases_report.txt', 'r') as report_file:
            report = report_file.read()
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\MavenProj\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        commit_new_testcases = Main.get_commit_created_testcases(commit_testcases)
        compolation_error_testcases = Main.get_compilation_error_testcases(report, commit_new_testcases)
        self.assertTrue(expected_not_compiling_testcase in compolation_error_testcases,
                        "'MainTest#gooTest should have been picked as for compilation error")


def duplicate_stdout(proc, file):
    while(True):
        line = proc.readline()
        if line == '':
            break
        sys.stdout.write(line)
        file.write(line)


if __name__ == '__main__':
    unittest.main()
