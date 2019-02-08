import os
from pom_file import PomValue
from subprocess import Popen

class JcovTracer(object):
    """
               <artifactId>maven-surefire-plugin</artifactId>
           <version>2.18.1</version>
           <configuration>
-            <argLine>-Xmx2048m</argLine>
-          </configuration>
+            <argLine>"-javaagent:C:\Users\User\Documents\GitHub\jcov\JCOV_BUILD\jcov_3.0\jcov.jar=grabber,include_list=C:\Users\User\Documents\GitHub\jcov\classes_file.txt"</argLine>
+                                 <additionalClasspathElements>
+            <additionalClasspathElement>C:\Users\User\Documents\GitHub\jcov\JCOV_BUILD\jcov_3.0\listener.jar</additionalClasspathElement>
+          </additionalClasspathElements>
+
+          <properties>
+                       <property>
+                       <name>listener</name>
+                       <value>com.sun.tdk.listener.JUnitExecutionListener</value>
+                       </property>
+                       </properties>
+                 </configuration>
         </plugin>
         <plugin>
           <groupId>org.apache.maven.plugins</groupId>
    """

    JCOV_JAR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "externals", "jcov.jar")
    LISTENER_JAR_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "externals", "listener.jar")
    LISTENER_CLASS = "com.sun.tdk.listener.JUnitExecutionListener"

    def __init__(self, classes_dir, path_to_out_template=None, path_to_classes_file=None, path_to_result_file=None, class_path=None, instrument_only_methods=True):
        self.classes_dir = classes_dir
        self.path_to_out_template = path_to_out_template
        self.path_to_classes_file = path_to_classes_file
        self.path_to_result_file = path_to_result_file
        self.class_path = class_path
        self.instrument_only_methods = instrument_only_methods
        self.agent_port = str(self.get_open_port())
        self.command_port = str(self.get_open_port())

    def get_open_port(self):
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
            s.close()
            return port

    def template_creator_cmd_line(self):
        cmd_line = ['java', '-jar', JcovTracer.JCOV_JAR_PATH, 'tmplgen', '-verbose']
        if self.class_path :
            cmd_line.extend(['-cp', self.class_path])
        if self.path_to_out_template:
            cmd_line.extend(['-t', self.path_to_out_template])
        if self.path_to_classes_file:
                cmd_line.extend(['-c', self.path_to_classes_file])
        if self.instrument_only_methods:
            cmd_line.extend(['-type', 'method'])
        cmd_line.extend(self.get_classes_path())
        return cmd_line

    def grabber_cmd_line(self):
            cmd_line = ['java', '-jar', JcovTracer.JCOV_JAR_PATH, 'grabber', '-vv', '-port', self.agent_port, '-command_port', self.command_port]
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
                PomValue("maven-surefire-plugin", ["configuration", "additionalClasspathElements", "additionalClasspathElement"], JcovTracer.LISTENER_JAR_PATH)]

    def get_enviroment_variables_values(self):
        return [PomValue("maven-surefire-plugin", ["configuration", "forkMode"], "always"),
                PomValue("maven-surefire-plugin", ["configuration", "environmentVariables", "JcovGrabberCommandPort"], self.command_port)]

    def get_values_to_add(self):
        return JcovTracer.static_values_to_add_to_pom() + [self.get_agent_arg_line()] + self.get_enviroment_variables_values()

    def stop_grabber(self):
        Popen(["java", "-jar", JcovTracer.JCOV_JAR_PATH, "grabberManager", "-save",'-command_port', self.command_port]).communicate()
        Popen(["java", "-jar", JcovTracer.JCOV_JAR_PATH, "grabberManager", "-stop", '-command_port', self.command_port]).communicate()

    def execute_jcov_process(self):
        Popen(self.template_creator_cmd_line()).communicate()
        Popen(self.grabber_cmd_line())
