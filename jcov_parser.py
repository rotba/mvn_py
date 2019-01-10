import csv
import functools
import os
import xml.etree.cElementTree as et


class JcovParser(object):
    CLOSER = "/>"
    METHENTER = "<methenter"
    CSV_HEADER = ["component", "hit_count"]

    def __init__(self, xml_folder_dir):
        self.jcov_files = map(lambda name: os.path.join(xml_folder_dir, name),
                              filter(lambda name: name.endswith('.xml'), os.listdir(xml_folder_dir)))
        self.ids = self._get_method_ids()
        self.lines_to_read = self._get_methods_lines()

    def parse(self, output_folder_dir):
        for jcov_file in self.jcov_files:
            out_path = os.path.join(output_folder_dir, os.path.basename(jcov_file).replace(".xml", ""))
            self._parse_jcov_file(jcov_file, out_path)

    def _parse_jcov_file(self, jcov_file, out_path):
        counts = self._get_methenter_ids_counts(jcov_file)
        lines = [JcovParser.CSV_HEADER] + map(lambda id: [self.ids[id], counts[id]], counts)
        with open(out_path, "wb") as out_file:
            csv.writer(out_file).writerows(lines)

    def _get_methenter_ids_counts(self, jcov_file):
        counts = {}
        for method in self._get_lines_by_inds(jcov_file):
            data = dict(map(lambda val: val.split('='),
                            method[len(JcovParser.METHENTER) + 1:-len(JcovParser.CLOSER)].replace('"', "").split()))
            count = data["count"]
            if int(count):
                counts[data["id"]] = count
        return counts

    def _get_lines_by_inds(self, file_path):
        with open(file_path) as f:
            enumerator_next_ind = 0
            for ind in self.lines_to_read:
                map(functools.partial(next, f), xrange(enumerator_next_ind, ind))
                enumerator_next_ind = ind + 1
                yield next(f).strip()

    def _get_methods_lines(self):
        with open(self.jcov_files[0]) as f:
            return map(lambda line: line[0],
                       filter(lambda line: JcovParser.METHENTER in line[1] and JcovParser.CLOSER in line[1],
                              enumerate(f.readlines())))

    @staticmethod
    def get_children_by_name(element, name):
        return filter(lambda e: e.tag.endswith(name), element.getchildren())

    @staticmethod
    def get_elements_by_path(root, path):
        elements = [([], root)]
        for name in path:
            elements = reduce(list.__add__,
                              map(lambda elem: map(lambda child: (elem[0] + [child], child),
                                                   JcovParser.get_children_by_name(elem[1], name)), elements), [])
        return elements

    def _get_method_ids(self):
        root = et.parse(self.jcov_files[0]).getroot()
        method_ids = {}
        for method_path, method in JcovParser.get_elements_by_path(root, ['package', 'class', 'meth']):
            method_name = ".".join(map(lambda elem: elem.attrib['name'], method_path))
            id = JcovParser.get_elements_by_path(method, ['bl', 'methenter'])[0][1].attrib['id']
            method_ids[id] = method_name
        return method_ids


if __name__ == "__main__":
    JcovParser(r"C:\temp\tik\out").parse(r"C:\temp\tik\out_txt3")
