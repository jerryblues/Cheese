# -*- coding:utf-8 -*-
import re
import sys
import os
import zipfile
import shutil
import time
import msvcrt

class Analyse:
    def __init__(self):
        self.arg = sys.argv[:]
        self.interface = []
        self.module = []

    def get_snapshot(self):
        files = []
        current_dir = os.getcwd()
        dir_file = os.listdir('.')
        for line in dir_file:
            if line.endswith('.zip'):
                f = current_dir + os.sep + line
                files.append(f)
                print('The current zip file is {}'.format(current_dir + os.sep + line))
        res = sorted(files, key=lambda x: os.path.getmtime(x))
        print('Zip file is {}, mtime :{}'.format(res[-1],os.path.getmtime(res[-1])))
        return res[-1]

    def find_cp_log(self, file):
        check_dir = '.\\test'
        # 创建初始存放的文件夹
        if not os.path.exists(check_dir):
            os.makedirs('.\\test')
        log_dir = os.getcwd() + '\\test'
        # 解压snapshot
        snapshot = zipfile.ZipFile(file)
        snapshot.extractall(path=log_dir)
        snapshot.close()
        # 创建最终存放log的文件夹
        final_log = '.\\test\\logs'
        if not os.path.exists(final_log):
            os.makedirs(final_log)
        second_dir = os.listdir('.\\test')
        for line in second_dir:
            if line.endswith('.zip'):
                print(line)
                sub_zip = '.\\test' + os.sep + line
                each_zip = zipfile.ZipFile(sub_zip)
                each_zip.extractall('.\\test\\logs')
                each_zip.close()
        file_container = os.listdir(final_log)
        result_log = '.\\result'
        if not os.path.exists(result_log):
            os.makedirs(result_log)
        for line in file_container:
            if line.endswith('runtime.zip') or line.endswith('startup.zip'):
                print(line)
                result_zip = '.\\test\\logs' + os.sep + line
                shutil.move(result_zip, result_log)
        shutil.rmtree(check_dir)
        log_file = os.listdir(result_log)
        for line in log_file:
            log_zip = '.\\result' + os.sep + line
            zipfile.ZipFile(log_zip).extractall('.\\result')
            os.remove(log_zip)
        log_file = os.listdir(result_log)
        for line in log_file:
            if '_cp_' not in line:
                dele_file = result_log + os.sep + line
                os.remove(dele_file)
        log_file = os.listdir(result_log)
        # for line in log_file:
        #     xz_file = result_log + os.sep + line
        #     # save_file = os.path.basename(xz_file)
        #     log_name = os.path.splitext(xz_file)[0]
        #     with lzma.open(xz_file) as f, open(log_name,'wb') as fout:
        #         print('正在解压 {}'.format(xz_file))
        #         file_content = f.read()
        #         fout.write(file_content)
        #         fout.close()
        #         f.close()
        #     print('正在删除 {}'.format(xz_file))
        #     os.remove(xz_file)
        log_file = os.listdir(result_log)
        for i in log_file:
            print('Find {}'.format(i))
        print('Complete CP log search ! log stored under .\\result path')


    def remove_result(self):
        last_result = os.path.exists('.\\result')
        if last_result:
            print('Old log exists, deleting it.....')
            shutil.rmtree('.\\result')
        else:
            print('Directory is clean !')


if __name__ == '__main__':
    test = Analyse()
    test.remove_result()
    file = test.get_snapshot()
    test.find_cp_log(file=file)
    #print('输入任意键退出...')
    #print(ord(msvcrt.getch()))
    for s in range(0,10):
        print('Exiting in '+ str(s) + ' s')
        time.sleep(1)
    sys.exit()
