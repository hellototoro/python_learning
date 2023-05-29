import os
import signal
import comm
import memcheck.log_parser.valgrind_log_parser as valgrind_log_parser

current_file_path = os.path.dirname(os.path.abspath(__file__))
check_type = 'memcheck'


# 解析log
def parser_log(log_file_list_all):
    for log_file_list in log_file_list_all:
        for log_file in log_file_list:
            index = log_file.rfind('/')
            file_name = log_file[0:index-len('log/')] + log_file[index:len(log_file)-len('.log')]
            v = valgrind_log_parser.ValgrindLogParser(log_file, file_name + '.html')
            v.generate_html_report()


# 终端终止信号
def signal_handler(sig, frame):
    comm.kill_valcheck(check_type)
    exit()


def memcheck():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    search_path = os.path.join(current_file_path, '../'*2)
    log_path = os.path.join(search_path, 'valcheck_report/' + check_type)
    log_file_list_all, already_running_dic = comm.valcheck(search_path, log_path, check_type)

    parser_log(log_file_list_all)

    for log_dir, already_running_list in already_running_dic.items():
        files = sorted(os.listdir(os.path.dirname(log_dir)))
        files.remove('log')
        index_path = os.path.join(os.path.dirname(log_dir), 'index.html')
        comm.create_index(check_type, index_path, files)
