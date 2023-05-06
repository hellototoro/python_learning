import re
import os
import argparse
from log_parser.utils.json_helper import JsonHelper
from log_parser.utils.html_converter import dump_html_report
from log_parser.utils.decorators import trycatch

class ValgrindLogParser(object):
    @trycatch
    def __init__(
        self,
        valgrind_log_file,
        html_report_location=None
    ):
        self._definitely_regex = None
        self._indirectly_regex = None
        self._possibly_regex = None
        self._still_reachable_regex = None
        self._summary_regex = None
        self._end_regex = None

        self.valgrind_log_file = valgrind_log_file
        if not html_report_location:
            html_report_location = os.getcwd()
        self.html_report_location = html_report_location
        self.regex_json = JsonHelper(os.path.join(os.path.dirname(__file__), 'data', 'valgrind_regexes.json'))
        self.errors_dict = {
            self.valgrind_log_file: {
                "memory_leak_definitely": [],
                "memory_leak_indirectly": [],
                "memory_leak_possibly": [],
                "memory_leak_still_reachable": [],
                "memory_leak_summary": []
            }
        }
        self.out_data = {"app_name" : self.valgrind_log_file}

    @property
    def definitely_regex(self):
        if not self._definitely_regex:
            self._definitely_regex = re.compile(self.regex_json.error_start_regexes.get('memory_leak_definitely'), re.I)
        return self._definitely_regex

    @property
    def indirectly_regex(self):
        if not self._indirectly_regex:
            self._indirectly_regex = re.compile(self.regex_json.error_start_regexes.get('memory_leak_indirectly'), re.I)
        return self._indirectly_regex

    @property
    def possibly_regex(self):
        if not self._possibly_regex:
            self._possibly_regex = re.compile(self.regex_json.error_start_regexes.get('memory_leak_possibly'), re.I)
        return self._possibly_regex

    @property
    def still_reachable_regex(self):
        if not self._still_reachable_regex:
            self._still_reachable_regex = re.compile(self.regex_json.error_start_regexes.get('memory_leak_still_reachable'), re.I)
        return self._still_reachable_regex

    @property
    def summary_regex(self):
        if not self._summary_regex:
            self._summary_regex = re.compile(self.regex_json.error_summary_regexes.get('memory_leak_summary'), re.I)
        return self._summary_regex

    @property
    def end_regex(self):
        if not self._end_regex:
            self._end_regex = re.compile(self.regex_json.error_end_regexes.get('all_error_end_regex'), re.I)
        return self._end_regex

    @trycatch
    def _parser(self):
        with open(self.valgrind_log_file, 'r') as in_file:
            append_lines_flag = False
            leak_trace = ""
            matched_regex = None
            for line in in_file:
                for regex in [self.definitely_regex, self.indirectly_regex, self.possibly_regex, self.still_reachable_regex, self.summary_regex]:
                    start_match = re.match(regex, line.strip('\n'))
                    if start_match:
                        matched_regex = regex
                        append_lines_flag = True

                    end_match = re.match(self.end_regex, line.strip('\n'))
                    if end_match:
                        append_lines_flag = False
                        if (not line == '' or line is not None) and not leak_trace == '':
                            if matched_regex == self.definitely_regex:
                                self.errors_dict.get(self.valgrind_log_file).get('memory_leak_definitely').append(leak_trace)
                            if matched_regex == self.indirectly_regex:
                                self.errors_dict.get(self.valgrind_log_file).get('memory_leak_indirectly').append(leak_trace)
                            if matched_regex == self.possibly_regex:
                                self.errors_dict.get(self.valgrind_log_file).get('memory_leak_possibly').append(leak_trace)
                            if matched_regex == self.still_reachable_regex:
                                self.errors_dict.get(self.valgrind_log_file).get('memory_leak_still_reachable').append(leak_trace)
                            if matched_regex == self.summary_regex:
                                self.errors_dict.get(self.valgrind_log_file).get('memory_leak_summary').append(leak_trace)
                        leak_trace = ''

                    if append_lines_flag:
                        line=line.strip()
                        if not line == '' or line is not None:
                            leak_trace += "{line} <br>".format(line=line.strip('\n'))
                        break

    def generate_html_report(self):
        self._parser()
        app_name = self.valgrind_log_file.split('/')[-1].split('.')[0]
        data = self.errors_dict[self.valgrind_log_file]
        dump_html_report(app_name, data, self.html_report_location)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--valgrind_file', required=True)

    parser.add_argument('--html_report_location', default='./valgrind_html_report.html')

    args = parser.parse_args()
    v = ValgrindLogParser(args.valgrind_file, args.html_report_location)
    v.generate_html_report()
