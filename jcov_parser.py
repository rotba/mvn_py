import functools
import os
import gc
import xml.etree.cElementTree as et

from trace_information import Signature, TraceElement, Trace


class JcovParser(object):
    CLOSER = "/>"
    METH = "<meth"
    METHENTER = "<meth"
    CSV_HEADER = ["component", "hit_count"]

    def __init__(self, xml_folder_dir, instrument_only_methods=True):
        self.jcov_files = map(lambda name: os.path.join(xml_folder_dir, name),
                              filter(lambda name: name.endswith('.xml'), os.listdir(xml_folder_dir)))
        self.instrument_only_methods = instrument_only_methods
        self.method_name_by_id = self._get_method_ids()
        self.lines_to_read = self._get_methods_lines()

    def parse(self):
        for jcov_file in self.jcov_files:
            test_name = os.path.splitext(os.path.basename(jcov_file))[0].lower()
            yield self._parse_jcov_file(jcov_file, test_name)

    def _parse_jcov_file(self, jcov_file, test_name):
        gc.collect()
        trace = self._get_trace_for_file(jcov_file)
        method_name_by_extra_slot = dict(map(lambda e: (e.extra_slot, self.method_name_by_id[e.id]),filter(lambda e: hasattr(e,'extra_slot'),trace.values())))
        method_name_by_extra_slot[-1] = 'None'
        map(lambda element: element.set_previous_method(method_name_by_extra_slot), trace.values())
        return Trace(test_name, trace)

    def _get_trace_for_file(self, jcov_file):
        trace = {}
        for method in self._get_lines_by_inds(jcov_file):
            data = dict(map(lambda val: val.split('='),
                            method[len(JcovParser.METHENTER) + 1:-len(JcovParser.CLOSER)].replace('"', "").split()))
            trace_element = TraceElement(data, self.method_name_by_id)
            if trace_element.have_count():
                assert trace_element.id not in trace
                trace[trace_element.id] = trace_element
        return trace

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
            method_name = ".".join([package_name, class_name, method_name]) + "({0})".format(
                Signature(method.attrib['vmsig']).args)
            id = 0
            extra_slot = 0
            if self.instrument_only_methods:
                id = method.attrib['id']
                extra_slot = method.attrib['extra_slots']
            else:
                id = JcovParser.get_elements_by_path(method, ['bl', 'methenter'])[0][1].attrib['id']
                extra_slot = JcovParser.get_elements_by_path(method, ['bl', 'methenter'])[0][1].attrib['extra_slots']
            method_ids[int(id)] = method_name
        return method_ids


if __name__ == "__main__":
    traces = JcovParser(r"C:\Temp\traces").parse()
    import networkx
    for trace in traces:
        g = networkx.DiGraph()
        g.add_edges_from(traces[trace].get_execution_edges())
        networkx.write_gexf(g, os.path.join(r"C:\Temp\trace_grpahs", trace + "_execution.gexf"))
        g = networkx.DiGraph()
        g.add_edges_from(traces[trace].get_call_graph_edges())
        networkx.write_gexf(g, os.path.join(r"C:\Temp\trace_grpahs", trace + "_call_graph.gexf"))
        pass
    pass
