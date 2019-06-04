import os
from pom_file import PomValue


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