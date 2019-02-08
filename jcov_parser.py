import csv
import functools
import os
import xml.etree.cElementTree as et

import csv
import functools
import os
import xml.etree.cElementTree as et
import re


class PrimitiveTypes(object):
    PRIMITIVES = {'Z': "boolean", 'V': "void", 'I': "int", 'J': "long", 'C': "char", 'B': "byte", 'D': "double",
                  'S': "short", 'F': "float"}

    @staticmethod
    def get_primitive_type(primitive):
        return PrimitiveTypes.PRIMITIVES[primitive]


class Signature(object):
    MATCHER = re.compile("\\(([^\\)]*)\\)(.*)")

    def __init__(self, vmsig):
        self.vmsig = vmsig
        m = Signature.MATCHER.match(self.vmsig)
        self.return_value = Signature.convert_vm_type(m.group(2))
        self.args = Signature.get_args(m.group(1))

    @staticmethod
    def convert_vm_type(vm_type):
        return Signature.get_type_name(vm_type.replace('/', '.'))

    @staticmethod
    def get_type_name(vm_type):
        dims = 0
        while vm_type[dims] == '[':
            dims += 1
        type = ''
        if vm_type[dims] == 'L':
            type = vm_type[dims + 1: len(vm_type) - 1]
        else:
            type = PrimitiveTypes.get_primitive_type(vm_type[dims])
        return type + "[]" * dims

    @staticmethod
    def get_args(descr):
        if descr == "":
            return descr
        pos = 0
        last_pos = len(descr)
        args = ''
        dims = 0
        while pos < last_pos:
            ch = descr[pos]
            if ch == 'L':
                delimPos = descr.find(';', pos)
                if delimPos == -1:
                    delimPos = last_pos
                type = Signature.convert_vm_type(descr[pos: delimPos + 1])
                pos = delimPos + 1
            elif ch == '[':
                dims += 1
                pos += 1
                continue
            else:
                type = PrimitiveTypes.get_primitive_type(ch)
                pos += 1
            args += type + "[]" * dims
            dims = 0
            if pos < last_pos:
                args += ';'
        return args


class Trace(object):
    def __init__(self, test_name, trace):
        self.test_name = test_name
        self.trace = map(lambda t: t.lower(), trace)

    def files_trace(self):
        return list(set(map(lambda x: ".".join((x.split("(")[0].split(".")[:-1])), self.trace)))

    def get_trace(self, trace_granularity):
        if trace_granularity == 'methods':
            return list(set(self.trace))
        elif trace_granularity == 'files':
            return self.files_trace()
        assert False


class JcovParser(object):
    CLOSER = "/>"
    METH = "<meth"
    METHENTER = "<meth"
    CSV_HEADER = ["component", "hit_count"]

    def __init__(self, xml_folder_dir, instrument_only_methods=True):
        self.jcov_files = map(lambda name: os.path.join(xml_folder_dir, name),
                              filter(lambda name: name.endswith('.xml'), os.listdir(xml_folder_dir)))
        self.instrument_only_methods = instrument_only_methods
        self.ids = self._get_method_ids()
        self.lines_to_read = self._get_methods_lines()

    def parse(self):
        traces = {}
        for jcov_file in self.jcov_files:
            test_name = os.path.splitext(os.path.basename(jcov_file))[0].lower()
            traces[test_name] = self._parse_jcov_file(jcov_file, test_name)
        return traces

    def _parse_jcov_file(self, jcov_file, test_name):
        counts = self._get_methenter_ids_counts(jcov_file)
        return Trace(test_name, map(lambda id: self.ids[id], counts))

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
        method_prefix =  JcovParser.METH
        if not self.instrument_only_methods:
            method_prefix = JcovParser.METHENTER
        with open(self.jcov_files[0]) as f:
            return map(lambda line: line[0],
                       filter(lambda line: method_prefix in line[1] and JcovParser.CLOSER in line[1],
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
            package_name, class_name, method_name = map(lambda elem: elem.attrib['name'], method_path)
            if method_name == '<init>':
                method_name = class_name
            method_name = ".".join([package_name, class_name, method_name]) + "({0})".format(Signature(method.attrib['vmsig']).args)
            id = 0
            if self.instrument_only_methods:
                id = method.attrib['id']
            else:
                id = JcovParser.get_elements_by_path(method, ['bl', 'methenter'])[0][1].attrib['id']
            method_ids[id] = method_name
        return method_ids


if __name__ == "__main__":
    traces = JcovParser(r"C:\temp\tik\out").parse()
    print traces
    pass
