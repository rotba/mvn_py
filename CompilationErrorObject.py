import os

class CompilationErrorReport(object):
    def __init__(self, compilation_error_report_line):
        self._path = ''
        self._error_line = ''
        self._error_col = ''
        self.str = compilation_error_report_line
        parts = compilation_error_report_line.split(' ')
        if parts[1].endswith(':'):
            path_and_error_address = parts[1][:-1].split(':')
        else:
            path_and_error_address = parts[1].split(':')
        error_address = path_and_error_address[len(path_and_error_address) - 1]
        self._error_line = int(error_address.strip('[]').split(',')[0])
        self._error_col = int(error_address.strip('[]').split(',')[1]) if len(error_address.strip('[]').split(',')) >1 else -1
        self._path = ':'.join(path_and_error_address[:-1])
        if self._path.startswith('/') or self._path.startswith('\\'):
            self._path = self._path[1:]
        self._path = os.path.realpath(self._path)

    @property
    def path(self):
        return self._path

    @property
    def line(self):
        return self._error_line

    @property
    def column(self):
        return self._error_col

    def __repr__(self):
        return self.str

    def __str__(self):
        return self.str

    def __eq__(self, o):
        if not isinstance(o, CompilationErrorReport):
            return False
        else:
            return self.path == o.path and self.line == o.line and self.column == o.column