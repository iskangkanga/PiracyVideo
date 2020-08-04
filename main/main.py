import datetime

from spiders import yszxwang
import logging

from tkinter import *


logging.basicConfig(level=logging.INFO,
                    filename='main.log',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


def begin_parse(type, name):
    try:
        if type == '1':
            result = parse_alone(name)
        else:
            result = parse_many(name)
    except Exception as e:
        print('解析失败')
        result = "全网站检索已完成，下载失败，请查看错误信息"
    return result


def parse_alone(name):
    ys = yszxwang.YszxWangSpider(name)
    result = ys.parse_alone()
    # 成功，结束爬虫，不进行下一解析
    if result == "succeed" or result == 'over':
        result = name + " 任务结束"
        return
    logging.info('[网站] yszxwang [提示：] %s, 进入下一解析', result)


def parse_many(name):
    # 检索效果差且网络差，优先级靠后
    ys = yszxwang.YszxWangSpider(name)
    result = ys.parse_many()
    # 成功，结束爬虫，不进行下一解析
    if result == "succeed" or result == 'over':
        result = name + " 任务结束"
        return result
    # logging.info('[网站] yszxwang [提示：] %s, 进入下一解析', result)


if __name__ == '__main__':
    type = input("单剧集如电影，输入1，多剧集如电视剧，输入2:")
    name = input("请输入关键词:")
    start_time = datetime.datetime.now().replace(microsecond=0)
    result = begin_parse(type, name)
    end_time = datetime.datetime.now().replace(microsecond=0)