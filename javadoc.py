import os
from pom_file import PomValue
from subprocess import Popen, PIPE
import json
import shutil
import tempfile


class JavaDoc(object):
    """<plugin>
        <artifactId>maven-javadoc-plugin</artifactId>
        <configuration>
          <encoding>UTF-8</encoding>
          <quiet>true</quiet>
          <jarOutputDirectory>lib</jarOutputDirectory>
          <reportOutputDirectory>docs</reportOutputDirectory>
          <javadocVersion>1.6</javadocVersion>
          <additionalJOption>-J-Xmx512m</additionalJOption>
        </configuration>
      </plugin>

    <plugin>
          <artifactId>maven-javadoc-plugin</artifactId>
          <version>2.9</version>
        </plugin>


    <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-javadoc-plugin</artifactId>
        <version>2.9</version>
        <reportSets>
          <reportSet>
            <reports>
              <report>javadoc</report>
            </reports>
          </reportSet>
        </reportSets>
      </plugin>
      """
    DOCLET_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "externals", "json-doclet-0.0.0-SNAPSHOT-jar-with-dependencies.jar")
    PLUGIN_NAME = "maven-javadoc-plugin"

    @staticmethod
    def get_pom_values():
        configuration_items = [("encoding", "UTF-8"), ("quiet", "true"), ("failOnError", "false"), ("author", "false")
            , ("show", "private"), ('docletPath', JavaDoc.DOCLET_PATH), ('doclet', "jp.michikusa.chitose.doclet.JsonDoclet")]
        return map(lambda x: PomValue(JavaDoc.PLUGIN_NAME, ["configuration", x[0]], x[1], plugin_version="3.1", reporting=True), configuration_items)

    @staticmethod
    def get_javadoc_data(base_dir):
        sources_path = r'src\main\java'
        target_path = r'target\classes'
        data = dict()
        for root, dirs, files in os.walk(base_dir):
            if not dirs:
                continue
            if not any(map(lambda x: x.endswith('.java'), files)):
                continue
            if sources_path in root:
                sources, package = root.split(sources_path)
                data.setdefault((os.path.join(sources, sources_path), os.path.join(sources, target_path)), []).append(
                    package.replace(os.sep, '.')[1:])
        return data

    @staticmethod
    def get_cmd(sources_path, target_path, out_path, packages):
        return ["javadoc", "-classpath", target_path, "-sourcepath", sources_path, "-docletpath",
                JavaDoc.DOCLET_PATH, "-doclet", "jp.michikusa.chitose.doclet.JsonDoclet", "-source", "'1.6'", "-quiet", "-private",
                "-encoding", "iso-8859-1", "-charset", "'iso-8859-1'", "-d", out_path] + packages

    @staticmethod
    def get_javadoc_as_json(sources_path, target_path, packages):
        path_to_dir = tempfile.mkdtemp()
        Popen(JavaDoc.get_cmd(sources_path, target_path, path_to_dir, packages)).wait()
        json_file = os.path.join(path_to_dir, "all_data.json")
        with open(json_file) as f:
            json_data = json.loads(f.read(), encoding='iso-8859-1')
        shutil.rmtree(path_to_dir)
        return json_data

    @staticmethod
    def get_dir_javadoc(base_dir):
        data = JavaDoc.get_javadoc_data(base_dir)
        jsons = []
        for sources_path, target_path in data:
            jsons.append(JavaDoc.get_javadoc_as_json(sources_path, target_path, data[(sources_path, target_path)]))
        return jsons