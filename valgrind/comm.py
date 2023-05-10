import os
import sys
import subprocess
import time
import psutil
import shutil
from jinja2 import Environment, FileSystemLoader

running_tab = {}
app_log_map = {}
log_path = ''
check_type = ''
check_map = { 'memcheck':' -v --tool=memcheck --leak-check=full --show-leak-kinds=all --track-origins=yes --log-file=',
              'massif':' -v --tool=massif --time-unit=B --detailed-freq=1 --massif-out-file='}
             # 'massif':' --tool=massif --massif-out-file='}

# 查找指定目录下的所有run_list.txt
def find_run_lists(directory, file_name = 'run_list.txt'):
    result = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == file_name:
                result.append(os.path.join(root, file))
    return result


# 创建log文件
def make_log_file(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    log_dir = os.path.join(dir, 'log')
    os.makedirs(log_dir)
    return log_dir


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
def valcheck_internal(check_type, run_list_path, log_path):
    log_file_list = []
    already_running_list = []
    cmd_list, app_name_list = get_cmds(run_list_path)
    file_path = os.path.dirname(os.path.abspath(run_list_path))
    log_dir = os.path.join(log_path, os.path.basename(file_path))
    log_dir = make_log_file(log_dir)
    for cmd, app_name in zip(cmd_list, app_name_list):
        if not app_name == '' and app_name not in running_tab:
            running_tab[app_name] = True
            index = cmd.rindex(app_name)
            index = cmd.rfind(' ', 0, index)
            log_file = os.path.join(log_dir, app_name +'.log')
            valgrind = 'valgrind ' + check_map[check_type] + log_file + ' '
            if check_type == 'memcheck':
                ignore_file = os.path.join(file_path, 'memcheck.ignore')
                if os.path.exists(ignore_file):
                    valgrind += '--suppressions=' + ignore_file + ' '
            cmd = cmd[:index+1] + valgrind + cmd[index+1:]
            app_log_map[app_name] = log_file
            log_file_list.append(log_file)
        elif app_name in running_tab:
            already_running_list.append(app_name)
            continue

        cmd += '& \n'
        subprocess.Popen(args=cmd, stderr=subprocess.STDOUT, shell=True)  # , stdout=subprocess.PIPE
        time.sleep(5)
    return log_dir, log_file_list, already_running_list


# 杀掉valgrind进程
def kill_valcheck(check_type):
    run_flag = True
    while run_flag:
        run_flag = False
        for proc in psutil.process_iter(['name']):
            index = str(proc.info['name']).find(check_type)
            if index != -1:
                try:
                    run_flag = True
                    subprocess.call("kill " + str(proc.pid), shell=True)
                    time.sleep(10)
                except subprocess.CalledProcessError as err:
                    print(err)


def valcheck(search_path, _log_path, _check_type):
    check_type = _check_type
    log_path = _log_path
    run_lists = []
    if(len(sys.argv) > 1):
        for path in sys.argv[1:]:
            run_lists.append(path)
    else:
        run_lists = find_run_lists(search_path)

    log_file_list_all = []
    already_running_dic = {}
    for run_list_path in run_lists:
        log_dir, log_file_list, already_running_list = valcheck_internal(check_type, run_list_path, log_path)
        already_running_dic[log_dir] = already_running_list
        log_file_list_all.append(log_file_list)

    # 测试时间
    time.sleep(10)
    kill_valcheck(check_type)

    for log_dir, already_running_list in already_running_dic.items():
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        log_file_list = []
        for app_name in already_running_list:
            shutil.copy(app_log_map[app_name], log_dir)
            log_file_list.append(os.path.join(log_dir, os.path.basename(app_log_map[app_name])))
        log_file_list_all.append(log_file_list)

    return log_file_list_all, already_running_dic


def create_index(_check_type, index_path, html_list):
    path = os.path.dirname(os.path.abspath(__file__))
    env = Environment(loader=FileSystemLoader(path+'/data'))
    template = env.get_template('index.html')

    with open(index_path, 'w+', encoding='utf-8') as f:
        out = template.render(type=_check_type, report_list=html_list)
        f.write(out)
        f.close()
