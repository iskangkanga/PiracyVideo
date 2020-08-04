import re
from service.geter import get_response
import requests
import logging
from service.downloader import down_m3u8_thread

# 网站测试用例：釜山行2，环太平洋，刺客聂隐娘
# 釜山行和环太平洋可以使用同一种获取host（传入下载方法的host）的方法，刺客聂隐娘不行
# 釜山行和刺客聂隐娘可以使用同一种方法获取m3u8链接，环太平洋不行
# 该网站搜索不太行的样子，搜剑雨居然是动画


# 电视剧（综艺）下载逻辑
# 针对电视剧，首先获取该剧集所有资源
# 在获取到的资源中遍历，要求是，在某一资源，所有剧集可播放，否则弃用该资源，进入下一资源
# 如果有符合要求的资源，则可获取所有可播放剧集，循环调用下载方法，所有剧集下载完成后，视为成功
# 任一剧集下载失败，程序结束，提示错误，但是已经完成下载的剧集不会删除
# 网站测试用例：隐秘的角落，三十而已，密室大逃脱

# 在线可播放时，可选不下载在线播放，纯净播放链接，无广告

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


class YszxWangSpider:
    def __init__(self, name):
        self.name = name

    def parse_alone(self):
        self.type = input('选择模式（观看输入w），（下载输入d）如遇解析失败问题，可尝试下载到本地：')
        self.detail_url = self.get_detail_url()
        if 'http' not in self.detail_url:
            return self.detail_url
        self.play_page_urls = self.get_play_urls()
        if not isinstance(self.play_page_urls,list):
            return '解析失败'
        self.num = len(self.play_page_urls)
        self.real_url = self.get_real_url()
        if 'm3u8' not in self.data_url:
            s = self.data_url.split('/')
            self.host = s[0] + '//' + s[2]
        else:
            self.host = re.sub('/index.*', '', self.real_url)
        logging.info('[host：] %s', self.host)
        if 'http' not in self.real_url:
            return self.real_url
        if self.type == 'w':
            flag = input('选择下载请输入y，输入n或其他任意字符获得可播放资源链接（y/n）：')
        else:
            flag = input('输入y确认下载：')
        # if '.m3u8' in self.data_url:
        #     flag = 'y'
        #     print('当前资源不支持在线播放，已为你选择下载选项！')
        if flag != 'y':
            print('点击或复制到浏览器播放：')
            print(self.data_url)
            return 'over'
        result = self.down()
        return result

    def parse_many(self):
        self.type = input('选择模式（观看输入w），（下载输入d）如遇解析失败问题，可尝试下载到本地：')
        self.many_detail_url = self.get_detail_url()
        if 'http' not in self.many_detail_url:
            return self.many_detail_url
        self.all_play_list = self.get_all_source()
        self.source_num = len(self.all_play_list)
        if not isinstance(self.all_play_list,list) or self.source_num == 0:
            return '解析失败'
        self.many_real_url, self.many_data_url = self.get_many_real_url()
        if self.many_data_url == 'defeat' or self.many_real_url == 'defeat':
            return '解析失败'
        if self.type == 'w':
            flag = input('选择下载请输入y，输入其他任意字符将结束程序并获得可播放资源链接（y/n）：')
        else:
            flag = input('输入y确认下载：')
        if flag != 'y':
            print('点击或复制到浏览器播放：')
            for i, url in enumerate(self.many_data_url):
                print('第{}集'.format(i+1), url)
            return 'over'
        for i, real_url in enumerate(self.many_real_url):
            self.real_url = real_url
            if 'm3u8' not in self.many_data_url[i]:
                s = self.many_data_url[i].split('/')
                self.host = s[0] + '//' + s[2]
            else:
                self.host = re.sub('/index.*', '', self.real_url)
            result = self.down_many(i)
            if result == 'succeed':
                logging.info('[第]%s[集下载完成]', i+1)
            else:
                return '失败'
        return 'succeed'

    def down_many(self, i):
        name = self.name + str(i+1)
        result = down_m3u8_thread(self.real_url, name, self.host)
        return result

    def get_many_real_url(self):
        for i, play_list in enumerate(self.all_play_list):
            many_data_url = []
            many_real_url = []
            # logging.info('[当前资源第：] %s/%s [项]', i + 1, self.source_num)
            for j, play_page_url in enumerate(play_list):
                # logging.info('[当前解析第：] %s/%s [集]', j + 1, self.play_num)
                play_page_url = 'https://www.yszxwang.com' + play_page_url
                # logging.info('[播放页链接：] %s', play_page_url)
                resp1 = get_response(play_page_url)
                if resp1:
                    data_url = re.search('var now="(http.*?)"', resp1).group(1).strip()
                    # logging.info('[数据链接：] %s', data_url)
                    resp2 = get_response(data_url)
                    many_data_url.append(data_url)
                    if resp2:
                        u2 = ''
                        if 'm3u8' in data_url:
                            if self.type == 'w':
                                break
                            host = re.sub('index.*', '', data_url)
                            resp3 = get_response(data_url)
                            if resp3:
                                m3u8text = resp3.split('\n')
                                for text in m3u8text:
                                    if 'm3u8' in text:
                                        u2 = text
                        else:
                            # host = re.search('var redirecturl = "(http.*?)"', resp2).group(1).strip()
                            s = data_url.split('/')
                            host1 = s[0] + '//' + s[2]
                            u1 = re.search('var main = "(.*?)"', resp2).group(1).strip()
                            m3u8_url1 = host1 + u1
                            # logging.info('[第一个m3u8：] %s', m3u8_url1)
                            host = re.sub('index.*', '', m3u8_url1)
                            # 读取第一个m3u8链接，获取真实m3u8链接
                            resp3 = get_response(m3u8_url1)
                            if resp3:
                                m3u8text = resp3.split('\n')
                                for text in m3u8text:
                                    if 'm3u8' in text:
                                        u2 = text
                            else:
                                break
                        if u2:
                            if u2[0] == '/':
                                real_url = host + u2[1:]
                            else:
                                real_url = host + u2
                            if not real_url:
                                break
                            # logging.info('[真实m3u8：] %s', real_url)
                            resp = get_response(real_url)
                            # 简单测试链接可用性
                            if resp:
                                many_real_url.append(real_url)
                            else:
                                break
                    else:
                        break
                else:
                    break
            if len(many_real_url) == self.play_num and len(many_data_url) == self.play_num:
                return many_real_url, many_data_url

        return 'defeat', 'defeat'

    def get_all_source(self):
        max_num = 0
        max_play = 0
        resp = get_response(self.many_detail_url)
        all_source = re.findall("href='(/video.*?)'", resp)
        for s in all_source:
            num = int(re.search('-(\d+?)-', s).group(1).strip())
            play_num = int(re.search('-\d+?-(\d+?)\.html', s).group(1).strip())
            if num > max_num:
                max_num = num
            if play_num > max_play:
                max_play = play_num
        # 最大资源数
        source_num = max_num + 1
        # 最大集数，有些资源更新慢集数不足，弃用
        self.play_num = max_play + 1
        all_play_list = []
        for i in range(source_num):
            soruce_list = []
            for s in all_source:
                # 资源分类
                cate = int(re.search('-(\d+?)-', s).group(1).strip())
                if cate == i:
                    soruce_list.append(s)
            # 获取集数最大的所有资源
            if len(soruce_list) == self.play_num:
                all_play_list.append(soruce_list)
        # 弃用集数不足的资源
        logging.info('[共有资源]%s[项]，[每项资源]%s[集]', len(all_play_list), self.play_num)
        return all_play_list

    def get_real_url(self):
        for i, play_page_url in enumerate(self.play_page_urls):
            # logging.info('[当前资源第：] %s/%s [项]', i + 1, self.num)
            play_page_url = 'https://www.yszxwang.com' + play_page_url
            # logging.info('[播放页链接：] %s', play_page_url)
            resp1 = get_response(play_page_url)
            if resp1:
                self.data_url = re.search('var now="(http.*?)"', resp1).group(1).strip()
                # logging.info('[数据链接：] %s', self.data_url)
                resp2 = get_response(self.data_url)
                if resp2:
                    u2 = ''
                    if 'm3u8' in self.data_url:
                        if self.type == 'w':
                            break
                        host = re.sub('index.*', '', self.data_url)
                        resp3 = get_response(self.data_url)
                        if resp3:
                            m3u8text = resp3.split('\n')
                            for text in m3u8text:
                                if 'm3u8' in text:
                                    u2 = text
                    else:
                        s = self.data_url.split('/')
                        host1 = s[0] + '//' + s[2]
                        u1 = re.search('var main = "(.*?)"', resp2).group(1).strip()
                        m3u8_url1 = host1 + u1
                        # logging.info('[第一个m3u8：] %s', m3u8_url1)
                        host = re.sub('index.*', '', m3u8_url1)
                        # 读取第一个m3u8链接，获取真实m3u8链接
                        resp3 = get_response(m3u8_url1)
                        if resp3:
                            m3u8text = resp3.split('\n')
                            for text in m3u8text:
                                if 'm3u8' in text:
                                    u2 = text
                    if u2:
                        if u2[0] == '/':
                            real_url = host + u2[1:]
                        else:
                            real_url = host + u2
                        # logging.info('[真实m3u8：] %s', real_url)
                        resp = get_response(real_url)
                        if resp:
                            return real_url
            logging.info('[播放页异常：] %s', play_page_url)
        return '全部资源尝试完毕，解析失败'

    def get_detail_url(self):
        # 进入搜索获取搜索结果的第一条
        result = ''
        search_url = 'https://www.yszxwang.com/search.php'
        data = {
            'searchword': self.name
        }
        resp = requests.post(search_url, data=data, timeout=15)
        # print(resp.text)
        # 若网站检索无结果，直接返回错误提示并关闭爬虫
        if '对不起，没有找到' in resp.text:
            result = "ERROR, 网站检索无此结果！"
            return result
        # 进入搜索详情页，获取详情页链接
        urls = re.findall('href="(/[a-z]+?/.*?\d+/)"', resp.text)
        titles = re.findall('<h3><a.*?>(.*?)</a></h3>', resp.text)
        types = re.findall('<h3><a href="/(.*?)/.*?\d+/">.*?</a></h3>', resp.text)
        type_list = []
        for t in types:
            if t == 'tv':
                t = '电视剧'
            elif t == 'dm':
                t = '动漫'
            elif t == 'dy':
                t = '电影'
            elif t == 'zy':
                t = '综艺'
            type_list.append(t)
        # 暂时已发现 tv：剧集  dm：动漫  dy：电影  zy：综艺
        # print(titles)
        for url in urls:
            if len(url) > 60:
                urls.remove(url)
        r_urls = []
        for u in urls:
            if u not in r_urls:
                r_urls.append(u)
        print('已为你检索到结果如下：')
        for i, title in enumerate(titles):
            print(i + 1, title, type_list[i])
        choice = int(input('请输入数字选择资源：'))
        detail_url = 'https://www.yszxwang.com' + r_urls[choice - 1]
        # logging.info('[详情页面链接：] %s', detail_url)
        result = detail_url
        return result

    def get_play_urls(self):
        # 进入详情页，找到播放页链接
        resp = get_response(self.detail_url)
        if not resp:
            return "ERROR, 请求失败"
        play_page_urls = re.findall('a title=.*? href=\'(.*?)\' target="_self"', resp)
        return play_page_urls

    def down(self):
        result = down_m3u8_thread(self.real_url, self.name, self.host)
        return result