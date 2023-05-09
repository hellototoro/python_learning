import os
import sys
import signal

current_file_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_file_path, '../'))
import comm

check_type = 'massif'


# 解析log
def parser_log(log_file_list_all):
    for log_file_list in log_file_list_all:
        for log_file in log_file_list:
            index = log_file.rfind('/')
            file_name = log_file[0:index-len('log/')] + log_file[index:len(log_file)-len('.log')] + '.html'
            with open(log_file, 'r') as f:
                content_log = f.read()
                f.close()
            with open(os.path.join(current_file_path, 'data/template.html'), 'r') as f:
                content_template = f.readlines()
                f.close()
            content_template.insert(757, content_log)
            with open(file_name, 'w') as f:
                f.writelines(content_template)
                f.close()


# 终端终止信号
def signal_handler(sig, frame):
    comm.kill_valcheck(check_type)
    exit()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    search_path = os.path.join(current_file_path, '../../')
    log_path = os.path.join(search_path, '../valcheck_report/' + check_type)
    log_file_list_all, already_running_dic = comm.valcheck(search_path, log_path, check_type)

    parser_log(log_file_list_all)

    for log_dir, already_running_list in already_running_dic.items():
        files = sorted(os.listdir(os.path.dirname(log_dir)))
        files.remove('log')
        index_path = os.path.join(os.path.dirname(log_dir), 'index.html')
        comm.create_index(check_type, index_path, files)


if __name__ == '__main__':
    main()
