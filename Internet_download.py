import requests
import urllib3
import os
from time import time
# import re
import sys
from threading import Thread as Th


class Iteration:
    def __init__(self, content, times=10, chunk_size=1024):
        self.time = time()
        self.content = content
        self.sequence = 0
        self.times = times
        self.done = 0
        self.speed = 0
        self.chunk_size = chunk_size

    def __iter__(self):
        return self

    def __next__(self, chunk_size=1024):
        self.sequence += 1
        if self.sequence >= self.times:
            if self.sequence % self.times == 1:
                self.time = time()
                self.done = 0
        chunk = next(self.content.iter_content(chunk_size=self.chunk_size))
        self.done += len(chunk)
        if self.sequence % self.times == 0:
            self.speed = self.done / 1024 / (time() - self.time)
        return chunk


class ThreadingDownload:

    def __init__(self, src, name='', headers=None, cookies=None, path='download', timeout=None, threads_num=8):  # 初始化
        self.src = src
        if name:
            self.name = name + self.src[-4:]
        else:
            self.name = self.src[self.src.rfind('/''')+1:]
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = 120
        self.cookies = cookies
        self.path = path + '/'
        self.start_time = time()
        self.total_size = 0
        self.block_size = 0
        self.threads = []
        self.done = 0
        urllib3.disable_warnings()
        if threads_num:
            self.threads_num = threads_num
        else:
            self.threads_num = 8
        if headers:
            self.headers = headers
        else:
            self.headers = {}
        if os.path.exists(self.path):
            pass
        else:
            os.makedirs(self.path)

    def get_size(self):  # 获取即将下载文件的大小
        try:
            html = requests.get(self.src, headers=self.headers, cookies=self.cookies, stream=True, verify=False, timeout=self.timeout)
        except requests.exceptions:
            print('连接错误')
        else:
            self.total_size = int(html.headers['Content-Length'])
            self.block_size = int(self.total_size / self.threads_num)
            html.close()  # 关闭连接

    def download(self, sequence):  # 下载程序
        if sequence == self.threads_num:
            end_size = ''
        else:
            end_size = str(sequence * self.block_size - 1)
        start_size = str((sequence - 1) * self.block_size)
        if os.path.exists(self.path + self.name + str(sequence)):
            exist = os.path.getsize(self.path + self.name + str(sequence))
            start_size = str(exist + int(start_size))
            self.done += exist
            # print('断点续传')
        self.headers['Range'] = 'bytes=' + start_size + '-' + end_size
        try:
            # start_time = time()
            html = requests.get(self.src, headers=self.headers, cookies=self.cookies, stream=True, verify=False, timeout=self.timeout)
        except requests.exceptions:
            print('连接错误')
            os.system('pause')
        else:
            with open(self.path + self.name + str(sequence), 'ab') as file:
                iteration = Iteration(html, times=1, chunk_size=1024*1024)
                for chunk in iteration:
                    file.write(chunk)
                    file.flush()
                    # 显示进度条
                    self.done += len(chunk)
                    speed = iteration.speed
                    percent = int(100 * self.done / self.total_size)
                    sys.stdout.write("\r[%s%s] %d%% %dkb/s" % ('█' * int(percent / 2), ' ' * (50 - int(percent / 2)), percent, speed))
                    sys.stdout.flush()

    def joint(self):  # 连接程序
        with open(self.path + self.name + str(1), 'ab') as file:
            for i in range(2, self.threads_num + 1):
                with open(self.path + self.name + str(i), 'rb') as r:
                    while True:
                        content = r.read(1024*1024)
                        if not content:
                            break
                        else:
                            file.write(content)
                            file.flush()

    def prepare_for_thread(self, sequence):  # 用于创建线程
        self.get_size()
        if os.path.exists(self.path + self.name):
            os.remove(self.path + self.name)
            print('删除前置版本')
        self.download(sequence)

    def start(self):  # 创建线程并开始下载
        self.start_time = time()
        for i in range(1, self.threads_num + 1):
            t = Th(target=self.prepare_for_thread, args=(i,))
            self.threads.append(t)
            t.start()
        for i in self.threads:
            i.join()
        self.joint()
        os.rename(self.path + self.name + str(1), self.path + self.name)
        if self.threads_num >= 2:
            for i in range(2, self.threads_num + 1):
                os.remove(self.path + self.name + str(i))
        print('Finished')
        return True


if __name__ == '__main__':
    url = input('请输入下载链接')
    # url = 'https://w.wallhaven.cc/full/4v/wallhaven-4vqezl.jpg'  # 'https://w.wallhaven.cc/full/47/wallhaven-4768ev.jpg'
    doc = input('请输入文件名')
    try:
        threads = int(input('线程数'))
    except ValueError:
        threads = None
    try:
        timeout_ = int(input('输入限时'))
    except ValueError:
        timeout_ = None
    d = ThreadingDownload(url, doc, threads_num=threads, timeout=timeout_)
    d.start()
    os.system('pause')
