import lzma
import os
import shutil
import tempfile
import time
import zipfile
from tkinter import *
from tkinter import messagebox, ttk, filedialog, font
import logging
from logging import handlers

USER_GUIDE = """This tool is to extract some specific logs in gNB snapshot.

User Guide:
            
    Quick Unzip: \n\t\tFind latest zip in current directory then unzip logs in it.\n
    Select Snapshot: \n\t\tSelect snapshot that need to unzip or get SS info.\n
    Unzip Snapshot: \n\t\tunzip selected snapshot\n
    Open Log DIR: \n\t\tOpen the log directory after unzip done\n
    Get SS Architecture: \n\t\tGet the Architecture information of the selected zip, then open the log path, 
\t\treturn the information file 'archive_datetime.log'
    
"""

# Author: xing.liu@nokia-bell.com

class App:
    def __init__(self, root):
        self.root = root

        # 窗口主体
        self.root.geometry('700x450')
        self.root.title('Snapshot Log Tool')
        self.root.minsize(700, 450)

        # 选项区域
        self.flag_area = Frame(self.root)
        self.flag_area.pack(side=RIGHT, anchor=N)

        # 变量，用于储存当前的log文件夹和当前选中的snapshot
        self.cur_ss = None
        self.dir = None

        # flag变量，用于存储用户设置的cp，asp，pcap的设置
        self.cp_stat = IntVar()
        self.pcap_stat = IntVar()
        self.asp_stat = IntVar()

        # flag的设置按钮
        self.cp_flag = Checkbutton(self.flag_area, text='CP log', variable=self.cp_stat, command=self.get_cur_flag)
        self.cp_flag.pack(side=TOP, padx=5, pady=5, anchor=NW)
        self.cp_flag.invoke()
        self.cpnb_pcap = Checkbutton(self.flag_area, text='PCAP log', variable=self.pcap_stat,
                                     command=self.get_cur_flag)
        self.cpnb_pcap.pack(side=TOP, padx=5, pady=5, anchor=NW)
        self.asp_log = Checkbutton(self.flag_area, text='ASP log', variable=self.asp_stat, command=self.get_cur_flag)
        self.asp_log.pack(side=TOP, padx=5, pady=5, anchor=NW)
        self.clear_button = Button(self.flag_area, text='Clear Screen', command=self.clear_screen)
        self.clear_button.pack(side=BOTTOM, padx=5, pady=5, anchor=S)

        # 输出窗口
        self.log_window = Text(self.root)
        self.log_window.pack(fill='both', expand=True)
        self.ft = font.Font(family='Arial', size=10)
        self.log_window.tag_add('tag', END)
        self.log_window.tag_config('tag', foreground='blue', font=self.ft)
        self.log_window.insert(END, USER_GUIDE, 'tag')

        # 显示当前选择的Snapshot
        self.stat_area = Frame(self.root)
        self.stat_area.pack(anchor=W, fill='x')

        self.snapshot_label = Label(self.stat_area, text='Current Snapshot:')
        self.snapshot_label.pack(side=LEFT, padx=5, pady=5, anchor=W)

        self.snapshot = StringVar()
        self.snapshot.set(value='No Snapshot Selected')
        self.cur_file = ttk.Label(self.stat_area, background='white', textvariable=self.snapshot)
        self.cur_file.pack(side=TOP, fill='both', padx=5, pady=5, expand=True)

        # 各种按钮的设置
        self.quick_button = ttk.Button(text='Quick Unzip', command=self.auto_search_zipfile)
        self.quick_button.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

        self.select_button = ttk.Button(text='Select Snapshot', command=self.select_snapshot)
        self.select_button.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

        self.unzip_button = ttk.Button(text='Unzip Snapshot', command=self.unzip_snapshot, stat=DISABLED)
        self.unzip_button.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

        self.Open_button = ttk.Button(text='Open Log DIR', command=self.open_dir, stat=DISABLED)
        self.Open_button.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

        self.Archive_button = ttk.Button(text='Get SS Architecture', command=self.get_architecture, stat=DISABLED)
        self.Archive_button.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

        # 本工具的log配置
        self.log_name = 'log.txt'
        self.logger = logging.getLogger('helper')
        self.logger.setLevel(logging.DEBUG)
        self.fh = logging.FileHandler(self.log_name)
        self.fh.setLevel(logging.DEBUG)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.ch.setFormatter(self.formatter)
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.ch)
        self.logger.addHandler(self.fh)
        # self.log_rotate = logging.handlers.RotatingFileHandler(
        #     self.log_name, maxBytes=20, backupCount=5)
        # self.logger.addHandler(self.log_rotate)

    def cal_time(func):
        def wrapper(self, *args, **kwargs):
            t1 = time.time()
            func(self, *args, **kwargs)
            t2 = time.time()
            t = t2 - t1
            self.send_log(f"{func.__name__} function has been finished!, used {str(t)[:4]}s")
            return t2 - t1
        return wrapper

    @cal_time
    def quick_unzip(self):
        """
        解压当前选择的Snapshot文件
        :return:
        """
        file = self.cur_ss
        log_dir = os.getcwd() + f'\\snapshot-{time.strftime("%m%d-%H%M%S")}'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with tempfile.TemporaryDirectory(dir=log_dir) as tmpdir1:
            self.extract_zip(file, tmpdir1)
            with tempfile.TemporaryDirectory(dir=log_dir) as tmpdir2:
                for item in os.listdir(tmpdir1):
                    if item.endswith('.zip'):  # 解析所有zip
                        self.extract_zip(tmpdir1 + os.sep + item, tmpdir2)
                with tempfile.TemporaryDirectory(dir=log_dir) as tmpdir3:
                    for ind, item2 in enumerate(os.listdir(tmpdir2)):
                        if 'pcap' in item2 and self.pcap_stat.get():  # 解析pcap
                            node_id = item2.split(sep='_')[1]
                            shutil.move(tmpdir2 + os.sep + item2, log_dir + os.sep + node_id + item2)
                        if item2.endswith('runtime.zip') or item2.endswith('startup.zip'):  # 解析runtime或者startup
                            node_id = item2.split(sep='_')[1]
                            self.extract_zip(tmpdir2 + os.sep + item2, tmpdir3)
                            for i in os.listdir(tmpdir3):
                                if self.asp_stat.get() and 'ASP' in i:
                                    shutil.move(tmpdir3 + os.sep + i, log_dir + os.sep + node_id + i)
                                    self.send_log(node_id + '/' + i + ' Found !!!')
                                if self.cp_stat.get():
                                    if '_cp_' in i or 'BTSOM' in i:
                                        shutil.move(tmpdir3 + os.sep + i, log_dir + os.sep + node_id + i)
                                        self.send_log(node_id + '/' + i + ' Found !!!')
        self.change_button_stat(True)
        self.Archive_button['state'] = ACTIVE
        self.dir = log_dir
        self.unzip_xz()
        self.get_cur_flag()
        self.send_log(f"File {self.cur_ss} has been extracted. \n\tThe log directory is {self.dir}.")
        messagebox.showinfo('info', 'Unzip CP log Complete!')

    def extract_zip(self, file, path):
        """
        解压zip文件
        :param file: 选择要解压的文件
        :param path: 解压到哪个路径
        :return:
        """
        helper = zipfile.ZipFile(file)
        helper.extractall(path=path)
        helper.close()

    def unzip_xz(self):
        """
        解压当前self.dir文件夹下的.xz文件
        :return:
        """
        for xz in os.listdir(self.dir):
            if xz.endswith('.xz'):
                source = self.dir + os.sep + xz
                target = self.dir + os.sep + xz[:-3]
                with lzma.open(source) as f1, open(target, 'wb') as f2:
                    content = f1.read()
                    f2.write(content)
                os.remove(source)
        self.send_log('All xz file was extracted to .log file!')

    def select_snapshot(self):
        """
        选择一个你要解压的Snapshot 文件
        :return:
        """
        name = filedialog.askopenfilename(filetypes=[('zip', '*.zip'), ('all', '*.*')])
        if len(name) > 0:
            self.send_log(f'{name} SELECTED')
        else:
            self.send_log(f'Select action cancelled by user.')
            return
        self.cur_ss = name
        name = name.split(sep='/')[-1]
        self.snapshot.set(value=name)
        self.get_cur_flag()
        self.Archive_button['state'] = ACTIVE

    def unzip_snapshot(self):
        """
        解压当前的选择的Snapshot文件
        :return:
        """
        if self.snapshot.get().endswith('zip') and self.cur_ss.split('/')[-1] == self.snapshot.get():
            self.send_log(f'Starting unzip snapshot.{self.cur_ss.split("/")[-1]}')
            self.quick_unzip()
        else:
            messagebox.showinfo('Info', 'Snapshot is not correct, or no snapshot selected')
            self.send_log(f'No snapshot selected', level='warning')

    @cal_time
    def get_architecture(self):
        """
        获取当前的Snapshot里的所有文件结构信息
        :return:
        """
        cur_time = time.strftime('%m%d-%H%M%S', time.localtime())
        if self.cur_ss:
            c1 = os.path.basename(self.cur_ss)
            self.send_log("get_architecture started!")
            with open(f'Snapshot_menber_list_{cur_time}.log', 'a+') as f:
                f.write(c1 + '\n')
                with tempfile.TemporaryDirectory() as tp1:
                    unzip1 = zipfile.ZipFile(self.cur_ss)
                    unzip1.extractall(path=tp1)
                    li1 = unzip1.namelist()
                    unzip1.close()
                    for i in li1:
                        if i.endswith('.zip'):
                            f.write('\t' + i + '\n')
                            print('\t' + i + '\n')
                            with tempfile.TemporaryDirectory() as tp2:
                                unzip2 = zipfile.ZipFile(tp1 + os.sep + i)
                                unzip2.extractall(path=tp2)
                                li2 = unzip2.namelist()
                                unzip2.close()
                                for j in li2:
                                    if j.endswith('.zip'):
                                        f.write('\t\t' + j + '\n')
                                        print('\t\t' + j + '\n')
                                        unzip3 = zipfile.ZipFile(tp2 + os.sep + j)
                                        li3 = unzip3.namelist()
                                        unzip3.close()
                                        for k in li3:
                                            f.write('\t\t\t' + k + '\n')
                                            print('\t\t\t' + k + '\n')
                                    else:
                                        f.write('\t\t' + j + '\n')
                                        print('\t\t' + j + '\n')
                        else:
                            f.write('\t' + i + '\n')
                            print('\t' + i + '\n')
                        self.send_log(f'{i} is analyzed.')
            messagebox.showinfo('Info', 'Done!')
            self.send_log(f'Snapshot menber list OK.')
            os.startfile(os.curdir)
        else:
            messagebox.showinfo('Info', 'No Snapshot was selected!')
            self.send_log(f'No Snapshot was selected!')

    def open_dir(self):
        """
        打开当前存放解压log的文件夹
        :return:
        """
        if self.dir:
            os.startfile(self.dir)
            self.send_log(f'{self.dir} is the result path!')
        else:
            messagebox.showinfo('Info', 'Can\'t open the log directory, maybe you should unzip a snapshot first !')
            self.send_log(f'Can\'t open the log directory, maybe you should unzip a snapshot first !')

    def auto_search_zipfile(self):
        """
        寻找当前目录下最新的Snapshot文件
        :return:
        """
        files = []
        current_dir = os.getcwd()
        dir_file = os.listdir('../../../../N-5CG73876P8-Data/xiliu/Desktop')
        for line in dir_file:
            if line.endswith('.zip'):
                self.send_log(f'snapshot found, that is {line}')
                f = current_dir + os.sep + line
                files.append(f)
        res = sorted(files, key=lambda x: os.path.getmtime(x))
        if len(res) > 0:
            self.send_log(f'Latest snapshot is {res[-1]}')
            status = messagebox.askokcancel('Info', f'The {res[-1]} will be unzip, are you sure?')
            if status:
                self.cur_ss = res[-1]
                self.send_log(f'snapshot {res[-1]} is selected, unzipping it.')
                self.quick_unzip()
                self.snapshot.set(value=self.cur_ss)
            else:
                self.send_log(f'snapshot {res[-1]} is not selected, cancel it.')
        else:
            messagebox.showerror('Error',
                                 'No Zip File found in current directory!! You can choose a snapshot, then press Unzip button.')
            self.send_log(f'No Zip File found in current directory!!')

    def send_log(self, s, level='debug'):
        """
        更新本工具的log打印到屏幕，并且储存到log.txt文件
        :param s: 待打印的log
        :param level: 储存到log.txt里的log等级
        :return:
        """
        curtime = time.strftime('%y-%m/%d %H:%M:%S:', time.localtime())
        self.log_window.insert(END, curtime + '\n', 'tag')
        self.log_window.insert(END, '\t' + s + '\n')
        if level == 'debug':
            self.logger.debug(s)
        elif level == 'info':
            self.logger.info(s)
        elif level == 'error':
            self.logger.error(s)
        elif level == 'warning':
            self.logger.warning(s)
        else:
            self.logger.error(ValueError)
            raise ValueError
        self.log_window.see(END)

    def get_cur_flag(self):
        """
        获取当前用户设置的log flag
        :return: 当前的log配置
        """
        res = f'CP: {bool(self.cp_stat.get())}, PCAP: {bool(self.pcap_stat.get())}, ASP: {bool(self.asp_stat.get())}'
        self.send_log(res)
        if not self.cp_stat.get() and not self.pcap_stat.get() and not self.asp_stat.get():
            self.send_log('Please select at least 1 type of log. Otherwise, no log will be extracted.', level='warning')
            messagebox.showerror('Warning', 'Please select at least 1 type of log, Otherwise, no log will be extracted.')
            self.change_button_stat(False)
        else:
            if self.cur_ss:
                self.change_button_stat(True)
            else:
                self.change_button_stat(False)
        return res

    def clear_screen(self):
        self.log_window.delete(1.0, END)
        self.send_log('Screen has been cleared!')

    def change_button_stat(self, stat):
        if stat:
            tmp = ACTIVE
        else:
            tmp = DISABLED
        self.unzip_button['state'] = tmp
        self.Open_button['state'] = tmp


rt = Tk()
gui = App(rt)
rt.mainloop()
