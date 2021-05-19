# coding=utf-8
"""
@file: Python_auto_click.py.py
@time: 2021/4/8 10:44
@author: h4zhang
"""

from pywinauto.application import Application
import time

app = Application(backend='win32').connect(path=r"C:\Holmes\ET\QPM_LK1.3.1(Hangzhou)\ClientMain.exe", timeout=5)
dlg = app.window(title_re="QPM Licence Keeper v.1.3.1")
dlg.print_control_identifiers()
# app['Login'].click()

# C:\windows\system32\notepad.exe
# app1 = Application(backend='win32').connect(path=r"C:\windows\system32\notepad.exe")
# about_dlg = app1.window(title_re="记事本")
# about_dlg.print_control_identifiers()
# app1['记事本']['不保存'].click()

# C:\Holmes\software\Everything\Everything.exe
# app = Application(backend='win32').connect(path=r"C:\Holmes\software\Everything\Everything.exe")
# dlg = app.window(title_re="添加书签")
# dlg.print_control_identifiers()
# app['添加书签']['取消'].click()

# python C:\Holmes\code\Cheese\Python_Application\Python_auto_click.py
