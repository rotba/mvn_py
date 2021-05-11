import os
from .pom_file import PomValue
from subprocess import Popen
import socket


class JcovTracer(object):

    JCOV_JAR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "externals", "jcov.jar")
    LISTENER_JAR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "externals", "listener.jar")
    LISTENER_CLASS = "com.sun.tdk.listener.JUnitExecutionListener"
    DEBUG_CMD = ["-Xdebug", "-Xrunjdwp:transport=dt_socket,address=5000,server=y,suspend=y"]

    def __init__(self, classes_dir, path_to_out_template=None, path_to_classes_file=None, path_to_result_file=None, class_path=None, instrument_only_methods=True, classes_to_trace=None):
        self.classes_dir = classes_dir
        self.path_to_out_template = path_to_out_template
        self.path_to_classes_file = path_to_classes_file
        self.path_to_result_file = path_to_result_file
        self.class_path = class_path
        self.instrument_only_methods = instrument_only_methods
        self.classes_to_trace = classes_to_trace
        self.agent_port = str(self.get_open_port())
        self.command_port = str(self.get_open_port())
        self.env = {"JcovGrabberCommandPort": self.command_port}
        assert os.environ['JAVA_HOME'], "java home is not configured"

    def get_open_port(self):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
            s.close()
            return port

    def check_if_grabber_is_on(self):
        import time
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            time.sleep(5)
            s.connect(('127.0.0.1', int(self.command_port)))
            s.close()
            return True
        except:
            return False
        return False

    def template_creator_cmd_line(self, debug=False):
        cmd_line = [os.path.join(os.environ['JAVA_HOME'], "bin\java.exe"), '-Xms2g'] + (JcovTracer.DEBUG_CMD if debug else []) + ['-jar', JcovTracer.JCOV_JAR_PATH, 'tmplgen', '-verbose']
        if self.class_path :
            cmd_line.extend(['-cp', self.class_path])
        if self.path_to_out_template:
            cmd_line.extend(['-t', self.path_to_out_template])
        if self.path_to_classes_file:
                cmd_line.extend(['-c', self.path_to_classes_file])
        if self.instrument_only_methods:
            cmd_line.extend(['-type', 'method'])
        if self.classes_to_trace:
            for c in self.classes_to_trace:
                cmd_line.extend(['-i', c])
        cmd_line.extend(self.get_classes_path())
        return cmd_line

    def grabber_cmd_line(self, debug=False):
            cmd_line = [os.path.join(os.environ['JAVA_HOME'], "bin\java.exe"), '-Xms2g'] + (JcovTracer.DEBUG_CMD if debug else []) + ['-jar', JcovTracer.JCOV_JAR_PATH, 'grabber', '-vv', '-port', self.agent_port, '-command_port', self.command_port]
            if self.path_to_out_template:
                cmd_line.extend(['-t', self.path_to_out_template])
            if self.path_to_result_file:
                    cmd_line.extend(['-o', self.path_to_result_file])
            return cmd_line

    def get_agent_arg_line(self):
        arg_line = r'-javaagent:{JCOV_JAR_PATH}=grabber,port={PORT}'.format(JCOV_JAR_PATH=JcovTracer.JCOV_JAR_PATH, PORT=self.agent_port)
        if self.path_to_classes_file:
            arg_line += r',include_list={CLASSES_FILE}'.format(CLASSES_FILE=self.path_to_classes_file)
        if self.path_to_out_template:
            arg_line += r',template={0}'.format(self.path_to_out_template)
        if self.instrument_only_methods:
            arg_line += r',type=method'
        return PomValue("maven-surefire-plugin", ["configuration", "argLine"], '"{0}"'.format(arg_line))


    def get_classes_path(self):
        all_classes = [self.classes_dir]
        for root, dirs, files in os.walk(self.classes_dir):
            if "target" in dirs:
                classes_path = os.path.join(root, "target", "classes")
                if os.path.exists(classes_path):
                    all_classes.append(classes_path)
        return all_classes

    @staticmethod
    def static_values_to_add_to_pom():
        return [PomValue("maven-surefire-plugin", ["configuration", "properties", "property", "name"], "listener"),
                PomValue("maven-surefire-plugin", ["configuration", "properties", "property", "value"], JcovTracer.LISTENER_CLASS),
                PomValue("maven-surefire-plugin", ["configuration", "additionalClasspathElements", "additionalClasspathElement"], JcovTracer.LISTENER_JAR_PATH),
                PomValue("maven-surefire-plugin", ["version"], "2.22.0", should_append=False),
                #PomValue("maven-surefire-plugin", ["configuration", "forkMode"], "once", should_append=False),
                #PomValue("maven-surefire-plugin", ["configuration", "forkedProcessTimeoutInSeconds"], "600", should_append=False),
                PomValue("maven-surefire-plugin", ["configuration", "forkCount"], "1", should_append=False),
                PomValue("maven-surefire-plugin", ["configuration", "reuseForks"], "false", should_append=False)]

    def get_enviroment_variables_values(self):
        return [#PomValue("maven-surefire-plugin", ["configuration", "forkMode"], "once", should_append=False),
                #PomValue("maven-surefire-plugin", ["configuration", "forkedProcessTimeoutInSeconds"], "600", should_append=False),
                PomValue("maven-surefire-plugin", ["configuration", "forkCount"], "1", should_append=False),
                PomValue("maven-surefire-plugin", ["configuration", "reuseForks"], "false", should_append=False),
                PomValue("maven-surefire-plugin", ["configuration", "environmentVariables", "JcovGrabberCommandPort"], self.command_port)]

    def get_values_to_add(self):
        return JcovTracer.static_values_to_add_to_pom() + [self.get_agent_arg_line()] + self.get_enviroment_variables_values()

    def stop_grabber(self):
        Popen(["java", "-jar", JcovTracer.JCOV_JAR_PATH, "grabberManager", "-save", '-command_port', self.command_port]).communicate()
        Popen(["java", "-jar", JcovTracer.JCOV_JAR_PATH, "grabberManager", "-stop", '-command_port', self.command_port]).communicate()

    def execute_jcov_process(self, debug=False):
        Popen(self.template_creator_cmd_line(debug=debug)).communicate()
        for path in [self.path_to_classes_file, self.path_to_out_template]:
            if path:
                with open(path) as f:
                    assert f.read(), "{0} is empty".format(path)
        if self.classes_to_trace:
            with open(self.path_to_classes_file, "wb") as f:
                f.write("\n".join(self.classes_to_trace))
        p = Popen(self.grabber_cmd_line(debug=debug))
        assert p.poll() is None
        assert self.check_if_grabber_is_on()
