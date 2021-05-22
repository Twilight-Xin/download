import unittest
from Internet_download import ThreadingDownload as Td
from time import time


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.url = 'https://w.wallhaven.cc/full/4v/wallhaven-4vqezl.jpg'
        self.headers1 = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)'}
        self.headers2 = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)"}
        self.headers3 = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)"}
        self.right = 0

    def judge(self, td):
        with open('download/std.jpg', 'rb') as std:
            with open(td.path + td.name, 'rb') as dl:
                while True:
                    a = std.read(1)
                    b = dl.read(1)
                    if a == b:
                        self.right += len(a)
                    else:
                        print("a:", a)
                        print("b:", b)
                        print("Right: ", self.right)
                        print("Block_size:", td.block_size)
                        print("Total_size:", td.total_size)
                        return False
                    if not a:
                        break
                return True

    def test_download_8(self):  # 测试无参数下载
        k = time()
        s = Td(self.url, headers=self.headers1)
        s.start()
        r = self.judge(s)
        e = time()
        print(str(e - k) + ' default')
        self.assertEqual(r, True)

    def test_download_2(self):  # 测试有参下载
        k = time()
        s = Td(self.url, headers=self.headers2, name='picture', threads_num=2, timeout='')
        s.start()
        r = self.judge(s)
        e = time()
        print(str(e - k) + ' threads_num=2')
        self.assertEqual(r, True)

    def test_download_1(self):  # 测试有参下载
        k = time()
        s = Td(self.url, headers=self.headers3, name='picture', threads_num=1, timeout=100)
        s.start()
        r = self.judge(s)
        e = time()
        print(str(e - k) + ' threads_num=1')
        self.assertEqual(r, True)


if __name__ == '__main__':
    unittest.main()
