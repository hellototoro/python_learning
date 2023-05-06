import os
import sys
import subprocess
import time
import psutil
import signal
import shutil
import log_parser.valgrind_log_parser as valgrind_log_parser

running_tab = {}
app_log_map = {}

# 查找指定目录下的所有run_list.txt
def find_run_lists(directory, file_name = 'run_list.txt'):
    result = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == file_name:
                result.append(os.path.join(root, file))
    return result


# 创建log文件
def make_log_file(dir, name):
    log_dir = os.path.join(dir, 'log')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    return os.path.join(log_dir, name +'.log')


# 从run_list.txt里面提取shell命令
def get_cmds(run_list_path):
    cmd_list = []
    app_name_list = []
    app_name = ''
    with open(run_list_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line == '':
                continue
            if line.startswith('<'):
                app_name = line.strip('<>')
            else:
                app_name_list.append(app_name)
                cmd_list.append(line)
    return cmd_list, app_name_list


# 用valgrind的memcheck执行run_list.txt里面的每一个app
def memcheck(run_list_path):
    log_file_list = []
    already_running_list = []
    cmd_list, app_name_list = get_cmds(run_list_path)
    file_path = os.path.dirname(os.path.abspath(run_list_path))
    for cmd, app_name in zip(cmd_list, app_name_list):
        if not app_name == '' and app_name not in running_tab:
            running_tab[app_name] = True
            index = cmd.rindex(app_name)
            index = cmd.rfind(' ', 0, index)
            log_file = make_log_file(file_path, app_name)
            valgrind = 'valgrind --log-file=' + log_file + ' --tool=memcheck --leak-check=full --show-leak-kinds=all --track-origins=yes '
            cmd = cmd[:index+1] + valgrind + cmd[index+1:]
            app_log_map[app_name] = log_file
            log_file_list.append(log_file)
        elif app_name in running_tab:
            already_running_list.append(app_name)
            continue

        cmd += '& \n'
        subprocess.Popen(args=cmd, stderr=subprocess.STDOUT, shell=True)  # , stdout=subprocess.PIPE
        time.sleep(1)
    return file_path, log_file_list, already_running_list


# 解析log
def parser_log(log_file_list_all):
    for log_file_list in log_file_list_all:
        for log_file in log_file_list:
            file_name, file_extension = os.path.splitext(log_file)
            v = valgrind_log_parser.ValgrindLogParser(log_file, file_name + '.html')
            v.generate_html_report()


# 杀掉valgrind进程
def kill_memcheck():
    run_flag = True
    while run_flag:
        run_flag = False
        for proc in psutil.process_iter(['name']):
            index = str(proc.info['name']).find('memcheck')
            if index != -1:
                try:
                    run_flag = True
                    subprocess.call("kill " + str(proc.pid), shell=True)
                    time.sleep(20)
                except subprocess.CalledProcessError as err:
                    print(err)


# 终端终止信号
def signal_handler(sig, frame):
    kill_memcheck()
    exit()


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    run_lists = []
    if(len(sys.argv) > 1):
        for path in sys.argv[1:]:
            run_lists.append(path)
    else:
        search_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        run_lists = find_run_lists(search_path)

    log_file_list_all = []
    already_running_dic = {}
    for run_list_path in run_lists:
        file_path, log_file_list, already_running_list = memcheck(run_list_path)
        already_running_dic[os.path.join(file_path, 'log')] = already_running_list
        log_file_list_all.append(log_file_list)

    # 测试时间
    time.sleep(30)
    kill_memcheck()

    for log_path, already_running_list in already_running_dic.items():
        if not os.path.exists(log_path):
            os.mkdir(log_path)
        log_file_list = []
        for app_name in already_running_list:
            shutil.copy(app_log_map[app_name], log_path)
            log_file_list.append(os.path.join(log_path, os.path.basename(app_log_map[app_name])))
        log_file_list_all.append(log_file_list)
    parser_log(log_file_list_all)

if __name__ == '__main__':
    main()
