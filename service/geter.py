# 只做get请求，post请求在原解析做
import requests
import logging


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s')


def get_response(url, headers=None):
    # 重试次数
    times = 3
    info = ''
    while times:
        try:
            resp = requests.get(url, headers=headers, timeout=9)
            content = resp.content.decode('utf-8')
            if resp.status_code >= 400 or len(content) <= 50:
                info = ''
                times -= 1
            else:
                info = content
                break
        except Exception as e:
            logging.info('[ERROR:] %s', e)
            info = ''
            times -= 1
    return info
