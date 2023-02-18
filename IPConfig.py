import datetime
import json
import time

import requests


def getapihost(dnsname):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        'Referer': '{}/'.format(dnsname)
    }
    url = dnsname + '/IPConfig.js'
    host = ''
    r = requests.get(url=url, headers=headers)
    try:
        jsonstr = r.text.split('=', -1)[2].replace(' ', '').replace('\n', '').replace('\r', '').replace("'", '"').replace('"//"', "")
        apihost = json.loads(jsonstr)
        host = '{}:{}'.format(apihost['IP'], apihost['Host'])
        log = '{} 测试地址校验正常，继续下一步！'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    except:
        log = '{} 测试地址校验失败，请重新输入！'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    return log, host