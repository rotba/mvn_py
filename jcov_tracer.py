import os
from pom_file import PomValue
from subprocess import Popen

class Jcov(object):
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

    def __init__(self, classes_dir, path_to_out_template=None, path_to_classes_file=None, path_to_result_file=None, class_path=None):
        self.classes_dir = classes_dir
        self.path_to_out_template = path_to_out_template
        self.path_to_classes_file = path_to_classes_file
        self.path_to_result_file = path_to_result_file
        self.class_path = class_path

    def template_creator_cmd_line(self):
        cmd_line = ['java', '-jar', Jcov.JCOV_JAR_PATH, 'tmplgen', '-verbose']
        if self.class_path :
            cmd_line.extend(['-cp', self.class_path ])
        if self.path_to_out_template:
            cmd_line.extend(['-t', self.path_to_out_template])
        if self.path_to_classes_file:
                cmd_line.extend(['-c', self.path_to_classes_file])
        cmd_line.extend(self.get_classes_path())
        return cmd_line

    def grabber_cmd_line(self):
            cmd_line = ['java', '-jar', Jcov.JCOV_JAR_PATH, 'grabber', '-vv']
            if self.path_to_out_template:
                cmd_line.extend(['-t', self.path_to_out_template])
            if self.path_to_result_file:
                    cmd_line.extend(['-o', self.path_to_result_file])
            return cmd_line

    def get_agent_arg_line(self):
        arg_line = r'-javaagent:{JCOV_JAR_PATH}=grabber'.format(JCOV_JAR_PATH=Jcov.JCOV_JAR_PATH)
        if self.path_to_classes_file:
            arg_line += r',include_list={CLASSES_FILE}'.format(CLASSES_FILE=self.path_to_classes_file)
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
               PomValue("maven-surefire-plugin", ["configuration", "properties", "property", "value"], Jcov.LISTENER_CLASS),
               PomValue("maven-surefire-plugin", ["configuration", "additionalClasspathElements", "additionalClasspathElement"], Jcov.LISTENER_JAR_PATH)]

    def get_values_to_add(self):
        return Jcov.static_values_to_add_to_pom() + [self.get_agent_arg_line()]

    def stop_grabber(self):
        Popen(["java", "-jar", Jcov.JCOV_JAR_PATH, "grabberManager", "-save"]).communicate()
        Popen(["java", "-jar", Jcov.JCOV_JAR_PATH, "grabberManager", "-stop"]).communicate()

    def execute_jcov_process(self):
        Popen(self.template_creator_cmd_line()).communicate()
        Popen(self.grabber_cmd_line())
