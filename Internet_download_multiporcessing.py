import requests
import urllib3
import os
from time import time
# import re
from sys import stdout
from threading import Thread
from multiprocessing import Pool, Manager


class Iteration:
    __slots__ = ['time', 'content', 'sequence', 'times', 'done', 'speed', 'chunk_size']

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


class MultiprocessingDownload:
    __slots__ = ['src', 'name', 'timeout', 'cookies', 'path', 'start_time', 'total_size', 'block_size',
                 'done', 'multiprocess_num', 'headers', 'quit']

    def __init__(self, src, name='', headers=None, cookies=None, path='download', timeout=None, multiprocess_num=8):  # 初始化
        self.src = src
        if name:
            self.name = name[-125:] + self.src[-4:]
        else:
            self.name = self.src[self.src.rfind('/') + 1:]
        if timeout:
            self.timeout = timeout
        else:
            self.timeout = 120
        self.cookies = cookies
        self.path = path + '/'
        self.start_time = time()
        self.total_size = 0
        self.block_size = 0
        self.done = 0
        self.quit = False
        urllib3.disable_warnings()
        if multiprocess_num:
            self.multiprocess_num = multiprocess_num
        else:
            self.multiprocess_num = 8
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
            html = requests.get(self.src, headers=self.headers, cookies=self.cookies, stream=True, verify=True,
                                timeout=self.timeout)
        except requests.exceptions:
            print('连接错误')
            return False
        else:
            self.total_size = int(html.headers['Content-Length'])
            self.block_size = int(self.total_size / self.multiprocess_num)
            html.close()  # 关闭连接
            return True

    def download(self, sequence, list_i):  # 下载程序
        if sequence == self.multiprocess_num:
            end_size = ''
        else:
            end_size = str(sequence * self.block_size - 1)  # rrr
        start_size = str((sequence - 1) * self.block_size)
        if os.path.exists(self.path + self.name + str(sequence)):
            exist = os.path.getsize(self.path + self.name + str(sequence))
            start_size = str(exist + int(start_size))
            self.done += exist
            # print('断点续传')
        headers = {}
        for key, value in self.headers.items():
            headers[key] = value
        headers['Range'] = 'bytes=' + start_size + '-' + end_size
        try:
            # start_time = time()
            html = requests.get(self.src, headers=headers, cookies=self.cookies, stream=True, verify=True,
                                timeout=self.timeout)
        except requests.exceptions:
            print('连接错误')
            return False
        else:
            with open(self.path + self.name + str(sequence), 'ab') as file:
                iteration = Iteration(html, times=1, chunk_size=1024 * 1024)
                for chunk in iteration:
                    file.write(chunk)
                    file.flush()
                    list_i.append([len(chunk), iteration.speed])
            return True

    def joint(self):  # 连接程序
        with open(self.path + self.name + str(1), 'ab') as file:
            for i in range(2, self.multiprocess_num + 1):
                with open(self.path + self.name + str(i), 'rb') as r:
                    while True:
                        content = r.read(1024 * 1024)
                        if not content:
                            self.quit = True
                            break
                        else:
                            file.write(content)
                            file.flush()

    def prepare_for_process(self, sequence, list_i):  # 用于创建线程
        if os.path.exists(self.path + self.name):
            os.remove(self.path + self.name)
            print('删除前置版本')
        if self.download(sequence, list_i):
            pass
        else:
            print('The ' + sequence + 'th Part of ' + self.name + ' happens a error')

    def progress_bar(self, list_i):
        while not self.quit:
            if list_i:
                receive = list_i.pop(0)
                speed = receive[1]
                self.done += receive[0]
                percent = self.done / self.total_size
                # print(percent, '-', self.done)
                done = int(50*percent)
                stdout.write('\r[%s%s] %d%% %d kb/s' % ('▉'*done, ' '*(50-done), int(percent*100), speed))
                stdout.flush()

    def start(self):  # 创建线程并开始下载
        self.start_time = time()
        if self.get_size():
            manager = Manager()
            bar_args = manager.list()
            pool = Pool(self.multiprocess_num)
            for i in range(1, self.multiprocess_num + 1):
                pool.apply_async(self.prepare_for_process, (i, bar_args), error_callback=print_error)
            bar = Thread(target=self.progress_bar, args=(bar_args,), daemon=True)
            bar.start()
            pool.close()
            pool.join()
            self.joint()
            os.rename(self.path + self.name + str(1), self.path + self.name)
            if self.multiprocess_num >= 2:
                for i in range(2, self.multiprocess_num + 1):
                    os.remove(self.path + self.name + str(i))
            bar.join()
            print(' Finished')
            return True
        else:
            return False


def print_error(value):
    print('ERROR:', value)


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
    d = MultiprocessingDownload(url, doc, multiprocess_num=threads, timeout=timeout_)
    d.start()
    os.system('pause')
