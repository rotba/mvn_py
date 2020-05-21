import xml.etree.cElementTree as et
et.register_namespace('', "http://maven.apache.org/POM/4.0.0")
et.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")


def is_surefire_plugin(plugin):
    return filter(lambda x: x.text == PomPlugin.SUREFIRE_ARTIFACT_ID, Pom.get_children_by_name(plugin, PomPlugin.ARTIFACT_ID_NAME))

def is_junit_plugin(plugin):
    return filter(lambda x: x.text == PomPlugin.JUNIT_ARTIFACT_ID, Pom.get_children_by_name(plugin, PomPlugin.ARTIFACT_ID_NAME))

def is_javadoc_plugin(plugin):
    return filter(lambda x: x.text == PomPlugin.JAVADOC_ARTIFACT_ID, Pom.get_children_by_name(plugin, PomPlugin.ARTIFACT_ID_NAME))

def is_maven_site_plugin(plugin):
    return filter(lambda x: x.text == PomPlugin.SITE_ARTIFACT_ID, Pom.get_children_by_name(plugin, PomPlugin.ARTIFACT_ID_NAME))


class PomPlugin(object):
    PLUGINS_PATH = ['build', 'plugins', 'plugin']
    PLUGINS_MANAGEMENT_PATH = ['build', 'pluginManagement', 'plugins', 'plugin']
    REPORTING_PATH = ['reporting', 'plugins', 'plugin']
    SUREFIRE_ARTIFACT_ID = "maven-surefire-plugin"
    JUNIT_ARTIFACT_ID = "junit"
    JAVADOC_ARTIFACT_ID = "maven-javadoc-plugin"
    SITE_ARTIFACT_ID = "maven-site-plugin"
    ARTIFACT_ID_NAME = "artifactId"
    PLUGINS = {"maven-surefire-plugin": is_surefire_plugin, "maven-javadoc-plugin": is_javadoc_plugin, "maven-site-plugin": is_maven_site_plugin}

    @staticmethod
    def get_plugins(pom):
        return pom.get_elements_by_path(PomPlugin.PLUGINS_PATH)

    @staticmethod
    def get_plugin_management(pom):
        return pom.get_elements_by_path(PomPlugin.PLUGINS_MANAGEMENT_PATH)

    @staticmethod
    def get_report_plugin(pom):
        return pom.get_elements_by_path(PomPlugin.REPORTING_PATH)

    @staticmethod
    def get_plugin_by_name(pom, plugin_name):
        assert plugin_name in PomPlugin.PLUGINS
        ans = list(filter(PomPlugin.PLUGINS[plugin_name], PomPlugin.get_plugins(pom) + PomPlugin.get_plugin_management(pom)))
        return ans

    @staticmethod
    def get_report_plugin_by_name(pom, plugin_name):
        assert plugin_name in PomPlugin.PLUGINS
        return filter(PomPlugin.PLUGINS[plugin_name], PomPlugin.get_report_plugin(pom))

    @staticmethod
    def get_plugin_management_by_name(pom, plugin_name):
        assert plugin_name in PomPlugin.PLUGINS
        return filter(PomPlugin.PLUGINS[plugin_name], PomPlugin.get_plugin_management(pom))


class PomValue(object):
    def __init__(self, plugin_name, path_to_create, value, should_append=True, plugin_version=None, reporting=False):
        self.plugin_name = plugin_name
        self.path_to_create = path_to_create
        self.value = value
        self.should_append = should_append
        self.plugin_version = plugin_version
        self.reporting = reporting

    def is_plugin(self):
        return self.plugin_name


class Pom(object):
    def __init__(self, pom_path):
        self.pom_path = pom_path
        self.element_tree = et.parse(self.pom_path)
        self.set_junit_version()

    @staticmethod
    def get_children_by_name(element, name):
        return filter(lambda e: e.tag.endswith(name), element.getchildren())

    @staticmethod
    def get_or_create_child(element, name):
        child = Pom.get_children_by_name(element, name)
        if len(child) == 0:
            return Pom.create_element(element, name)
        else:
            return child[0]

    @staticmethod
    def create_element(element, name):
        return et.SubElement(element, name)

    @staticmethod
    def get_or_create_by_path(element, path):
        for name in path:
            element = Pom.get_or_create_child(element, name)
        return element

    def get_elements_by_path(self, path):
        elements = [self.element_tree.getroot()]
        for name in path:
            elements = reduce(list.__add__, map(lambda elem: Pom.get_children_by_name(elem, name), elements), [])
        return elements

    def create_plugin_artifact(self, path, pom_value):
        element = Pom.get_or_create_by_path(self.element_tree.getroot(), path)
        new_plugin = Pom.create_element(element, 'plugin')
        artifact = Pom.create_element(new_plugin, PomPlugin.ARTIFACT_ID_NAME)
        artifact.text = pom_value.plugin_name
        version = Pom.create_element(new_plugin, 'version')
        version.text = pom_value.plugin_version
        return element

    def have_build(self):
        return len(self.get_elements_by_path(['build'])) > 0

    def add_pom_value(self, pom_value, create_plugin_if_not_exists=False):
        # if len(self.get_elements_by_path([pom_value.path_to_create[0]])) == 0:
        #     return
        if pom_value.plugin_version:
            management_path = PomPlugin.get_plugin_management_by_name(self, pom_value.plugin_name)
            if len(management_path) == 0:
                management_path = self.create_plugin_artifact(PomPlugin.PLUGINS_MANAGEMENT_PATH[:-1], pom_value)
            else:
                management_path = management_path[0]
            versions = Pom.get_children_by_name(management_path, "version")
            map(lambda version: setattr(version, "text", pom_value.plugin_version), versions)

        additions = [(PomPlugin.get_plugin_by_name(self, pom_value.plugin_name), PomPlugin.PLUGINS_PATH)]
        if pom_value.reporting:
            additions.append((PomPlugin.get_report_plugin_by_name(self, pom_value.plugin_name),PomPlugin.REPORTING_PATH))
        for plugins_path, base_path in additions:
            if len(plugins_path) == 0 and create_plugin_if_not_exists:
                plugins_path = [self.create_plugin_artifact(PomPlugin.PLUGINS_PATH, pom_value)]
            for plugin_path in plugins_path:
                created_element = Pom.get_or_create_by_path(plugin_path, pom_value.path_to_create)
                element_text = ''
                if pom_value.should_append and created_element.text:
                    element_text = created_element.text + ' '
                element_text += pom_value.value
                created_element.text = element_text
        self.save()

    def set_junit_version(self, version='4.11'):
        junit_dependencies = filter(is_junit_plugin, self.get_elements_by_path(['dependencies', 'dependency']))
        for dependency in junit_dependencies:
            created_element = Pom.get_or_create_by_path(dependency, ['version'])
            created_element.text = version
        self.save()

    def set_site_version(self, version='3.3'):
        dependencies = filter(is_maven_site_plugin, self.get_elements_by_path(['build', 'pluginManagement', 'plugins', 'plugin']))
        for dependency in dependencies:
            created_element = Pom.get_or_create_by_path(dependency, ['version'])
            created_element.text = version
        self.save()

    def save(self):
        self.element_tree.write(self.pom_path, xml_declaration=True)

    def has_surefire(self):
        return len(PomPlugin.get_plugin_by_name(self, PomPlugin.SUREFIRE_ARTIFACT_ID)) > 0
