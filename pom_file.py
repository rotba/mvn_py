import xml.etree.ElementTree
xml.etree.ElementTree.register_namespace('', "http://maven.apache.org/POM/4.0.0")
xml.etree.ElementTree.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")


class PomPath(object):
    def __init__(self, path):
        self.path = path


def is_surefire_plugin(plugin):
    return filter(lambda x: x.text == PomPlugin.SUREFIRE_ARTIFACT_ID, Pom.get_children_by_name(plugin, PomPlugin.ARTIFACT_ID_NAME))

class PomPlugin(object):
    PLUGINS_PATH = PomPath(['build', 'plugins', 'plugin'])
    SUREFIRE_ARTIFACT_ID = "maven-surefire-plugin"
    ARTIFACT_ID_NAME = "artifactId"
    PLUGINS = {"maven-surefire-plugin": is_surefire_plugin}

    @staticmethod
    def get_plugins(pom):
        return pom.get_elements_by_path(PomPlugin.PLUGINS_PATH)

    @staticmethod
    def get_plugin_by_name(pom, plugin_name):
        assert plugin_name in PomPlugin.PLUGINS
        return filter(PomPlugin.PLUGINS[plugin_name], PomPlugin.get_plugins(pom))


class PomValue(object):
    def __init__(self, plugin_name, path_to_create, value, should_append=True):
        self.plugin_name = plugin_name
        self.path_to_create = path_to_create
        self.value = value
        self.should_append = should_append


class Pom(object):
    def __init__(self, pom_path):
        self.pom_path = pom_path
        self.element_tree = xml.etree.ElementTree.parse(self.pom_path)

    @staticmethod
    def get_children_by_name(element, name):
        return filter(lambda e: e.tag.endswith(name), element.getchildren())

    @staticmethod
    def get_or_create_child(element, name):
        child = Pom.get_children_by_name(element, name)
        if len(child) == 0:
            return xml.etree.ElementTree.SubElement(element, name)
        else:
            return child[0]

    @staticmethod
    def get_or_create_by_path(element, path):
        for name in path:
            element = Pom.get_or_create_child(element, name)
        return element

    def get_elements_by_path(self, pom_path):
        elements = [self.element_tree.getroot()]
        for name in pom_path.path:
            elements = reduce(list.__add__, map(lambda elem: Pom.get_children_by_name(elem, name), elements), [])
        return elements

    def add_pom_value(self, pom_value):
        elements = PomPlugin.get_plugin_by_name(self, pom_value.plugin_name)
        for element in elements:
            created_element = Pom.get_or_create_by_path(element, pom_value.path_to_create)
            element_text = ''
            if pom_value.should_append and created_element.text:
                element_text = created_element.text + ' '
            element_text += pom_value.value
            created_element.text = element_text
        self.save()

    def save(self):
        self.element_tree.write(self.pom_path, xml_declaration=True)



