import requests


def tenantlist(dnsname, apihost):
    url = '{}/api/services/app/Tenant/GetAllTenant'.format(apihost)
    headers = {
        'Host': apihost.split('//', -1)[1],
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'Abp.TenantId': 'undefined',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans',
        'Referer': '{}/'.format(apihost),
        'Origin': dnsname,
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    r = requests.get(url, headers=headers)
    return r.json()['result']
