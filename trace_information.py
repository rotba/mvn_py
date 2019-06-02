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


class HitInformation(object):
    def __init__(self, method_name, lst):
        assert len(lst) == 3
        self.method_name = method_name
        self.count, self.previous_slot, self.parent = lst

    def set_previous_method(self, method_name_by_id):
        self.previous_method = method_name_by_id.get(self.previous_slot, 'None')
        self.parent_method = method_name_by_id.get(self.parent, 'None')
        self.execution_edge = (self.previous_method, self.method_name)
        self.call_graph_edge = (self.parent_method, self.method_name)

    @staticmethod
    def read_hit_information_string(str, method_name):
        return map(lambda lst: HitInformation(method_name, lst), eval(str))


class TraceElement(object):
    def __init__(self, jcov_data, method_name_by_id):
        self.jcov_data = jcov_data
        self.id = int(self.jcov_data['id'])
        extra_slot = int(self.jcov_data['extra_slots'])
        if extra_slot != -1:
            self.extra_slot = extra_slot
        self.count = int(self.jcov_data['count'])
        self.method_name = method_name_by_id[self.id]
        self.hits_information = []
        if self.count:
            self.hits_information = HitInformation.read_hit_information_string(self.jcov_data['HitInformation'], self.method_name)
            # assert sum(map(lambda x: x.count, self.hits_information)) == self.count, "{0}-{1}, {2}".format(self.id, self.method_name, self.count)

    def set_previous_method(self, method_name_by_id):
        map(lambda hit: hit.set_previous_method(method_name_by_id), self.hits_information)

    def have_count(self):
        return self.count

    def get_trace(self, trace_granularity='methods'):
        if trace_granularity == 'methods':
            return self.method_name
        elif trace_granularity == 'files':
            return ".".join((self.method_name.split("(")[0].split(".")[:-1]))
        assert False

    def get_execution_edges(self):
        return map(lambda hit: hit.execution_edge, self.hits_information)

    def get_call_graph_edges(self):
        return map(lambda hit: hit.call_graph_edge, self.hits_information)


class Trace(object):
    def __init__(self, test_name, trace):
        self.test_name = test_name
        self.trace = trace

    def get_trace(self, trace_granularity='methods'):
        return list(set(map(lambda t: t.get_trace(trace_granularity), self.trace)))

    def get_execution_edges(self):
        return reduce(list.__add__, map(lambda element: element.get_execution_edges(), self.trace.values()), [])

    def get_call_graph_edges(self):
        return reduce(list.__add__, map(lambda element: element.get_call_graph_edges(), self.trace.values()), [])