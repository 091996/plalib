import time

import requests


def tokenauth(dnsname, apihost, name, pas, ten):
    authurl = '{}/api/TokenAuth/Authenticate'.format(apihost)
    headers = {
        'Host': apihost.split('//', -1)[1],
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'Abp.TenantId': ten,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': dnsname,
        'Referer': '{}/'.format(dnsname),
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    date = {"userNameOrEmailAddress": name, "password": pas}
    r = requests.post(authurl, json=date, headers=headers)
    tok = ''
    if r.json()['result'] is None:
        log = '{} {} 登录失败'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), name)
    else:
        log = '{} {} 登录成功'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), name)
        tok = r.json()['result']
    return log, tok
