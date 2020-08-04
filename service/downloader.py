import os
import re
import threading
import time
from queue import Queue
import logging
from moviepy.video.io.VideoFileClip import VideoFileClip
from service.geter import get_response

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')

import requests


def down_m3u8_thread(url, file_name, host=None, headers=None):
    mkdir()

    file_name = file_name + '.mp4'
    logging.info('[url] %s [file_name] %s',url, file_name)
    host = host
    # 预下载，获取链接并写文件
    resp = get_response(url)
    m3u8_text = resp
    # 开链接队列
    ts_queue = Queue(10000)
    lines = m3u8_text.split('\n')
    concatfile = 'cache/' + "s" + '.txt'
    for i,line in enumerate(lines):
        if '.ts' in line:
            if 'http' in line:
                ts_queue.put(line)
            else:
                if line[0] == '/':
                    line = host + line
                else:
                    line = host + '/' + line
                ts_queue.put(line)
            filename = re.search('([a-zA-Z0-9-_]+.ts)', line).group(1).strip()
            open(concatfile, 'a+').write('file %s\n' % filename)


    num = ts_queue.qsize()
    logging.info('[下载开始，队列任务数：] %s', num)
    if num > 5:
        t_num = num // 5
    else:
        t_num = 1
    if t_num > 50:
        t_num = 50

    threads = []
    logging.info('下载开始')

    for i in range(t_num):
        t = threading.Thread(target=down, name='th-' + str(i),
                             kwargs={'ts_queue': ts_queue, 'headers': headers})
        t.setDaemon(True)
        threads.append(t)
    for t in threads:
        logging.info('[线程开始]')
        time.sleep(0.4)
        t.start()
    for t in threads:
        logging.info('[线程停止]')
        t.join()

    logging.info('下载完成，合并开始')
    merge(concatfile, file_name)
    logging.info('合并完成，删除冗余文件')
    remove()
    result = getLength(file_name)

    return result

# 关于m3u8格式视频多线程下载及合并的详解，在以前博客里记录过
# 最近突发奇想，准备搞点非正规电影网站的资源下载器，在进行第一个网站时，可能因为该网站通信质量差，导致我多线程卡死，阻塞了
# 研究了一下网上资料以及自己的代码，已经解决了，下面是思路
# 当线程卡死或者阻塞时，应首先考虑网络或者其他异常导致请求无法自动判定为超时，挂掉该线程，而是使线程一直处于卡死状态
# 当手动加上超时时间，就可以大概率解决该异常
# 从某种程度上来说，我们做请求时，都应该加上超时限制，不然代码卡在奇怪的地方，还要分析好久


def down(ts_queue, headers):
    tt_name = threading.current_thread().getName()
    while True:
        if ts_queue.empty():
            break
        url = ts_queue.get()
        filename = re.search('([a-zA-Z0-9-_]+.ts)', url).group(1).strip()
        try:
            requests.packages.urllib3.disable_warnings()
            r = requests.get(url, stream=True, headers=headers, verify=False, timeout=5)
            with open('cache/' + filename, 'wb') as fp:
                for chunk in r.iter_content(5424):
                    if chunk:
                        fp.write(chunk)
            logging.info('[url] %s [线程] %s [文件下载成功] %s',url, tt_name, filename)
        except Exception as e:
            ts_queue.put(url)
            logging.info('[ERROR] %s [文件下载失败，入队重试] %s', e, filename)


def merge(concatfile, file_name):
    try:
        path = 'cache/' + file_name
        command = 'ffmpeg -y -f concat -i %s -bsf:a aac_adtstoasc -c copy %s' % (concatfile, path)
        os.system(command)
    except:
        logging.info('Error')


def remove():
    dir = 'cache/'
    for line in open('cache/s.txt'):
        line = re.search('file (.*?ts)', line).group(1).strip()
        # print(line)
        os.remove(dir + line)
    logging.info('ts文件全部删除')
    try:
        os.remove('cache/s.txt')
        logging.info('文件已删除')
    except:
        logging.info('部分文件删除失败，请手动删除')


def getLength(file_name):
    video_path = 'cache/' + file_name
    clip = VideoFileClip(video_path)
    length = clip.duration
    logging.info('[视频时长] %s s', length)
    clip.reader.close()
    clip.audio.reader.close_proc()
    if length < 1:
        return 'defeat'
    else:
        return 'succeed'



# 所有下载方法执行前，判断是否存在缓存文件夹
def mkdir():
    root = 'cache/'
    flag = os.path.exists(root)
    if flag:
        pass
    else:
        os.mkdir(root)