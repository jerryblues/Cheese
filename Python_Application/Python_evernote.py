# coding=utf-8
"""
@file: Python_evernote.py
@time: 2017/12/5 14:03
@author: h4zhang
"""

import evernote
import requests
from evernote.api.client import EvernoteClient
import evernote.edam.notestore.NoteStore as NoteStore

'''
Developer Token:
S=s1:U=947b5:E=1699a41660b:C=162429039b8:P=1cd:A=en-devtoken:V=2:H=89714dc55e92a0999fd2067e2de79198
NoteStore URL:
https://sandbox.evernote.com/shard/s1/notestore
Expires:
20 March 2019, 01:39
'''

dev_token = "S=s1:U=947b5:E=1699a41660b:C=162429039b8:P=1cd:A=en-devtoken:V=2:H=89714dc55e92a0999fd2067e2de79198"
client = EvernoteClient(token=dev_token)

userStore = client.get_user_store()
user = userStore.getUser()
print user.username

# # 获取类
# userStore = client.get_user_store()
# # 打印用户名print('Log in successfully as {}'.format(userStore.getUser().username))
# if userStore.getUser().premiumInfo.premium: print('We are friends!')
#
# # 获取类
# noteStore = client.get_note_store()
# # 获取笔记本数量
# print('There are {} notebooks in your account'.format(len(noteStore.listNotebooks())))
#
# # 打印每个笔记本的名字与guid
# for notebook in self.noteStore.listNotebooks():
#     notebookName = notebook.name
#     notebookGuid = notebook.guid
#     print('{}: {}'.format(notebookName, notebookGuid))
#
# # 列出第一个笔记本中的所有笔记的标题
# notebookGuid = noteStore.listNotebooks()[0]
# f = NoteStore.NoteFilter()
# f.notebookGuid = notebookGuid
# for note in noteStore.findNotes(token, f, 0, 999).notes:
#     print(note.title)
