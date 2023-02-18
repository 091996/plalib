import time

import requests


# 找出需要排板的标本
def findbill(tenant):
    sql = """select a.BillNo
from Specimen a
         join TestItem b on 1 = 1 and b.Type in (3, 4, 5, 6)
         left join SampleResults c on a.BillNo = c.SpecimenBillNo and b.Id = c.TestItemId and c.BillStatus = 3
where a.TenantId = {}
  and b.TenantId = {}
  and datediff(day, a.CreationTime, getdate()) = 0
  and c.OriginalResults is null
group by a.BillNo""".format(tenant, tenant)
    return sql


# 丹霞的方法
def dx_templatelist(host, apihost, tenant, token):
    url = '{}/api/services/app/TestTemplateBetail/GetAllList?maxResultCount=1000'.format(apihost)
    headers = {'Host': apihost, 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token), 'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Origin': host, 'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(url, headers=headers)
    # print(r.json()['result']['items'])
    return r.json()['result']['items']


# 卫伦先找出酶免4项的检验项目信息
def wl_getallpage(host, apihost, tenant, token):
    url = '{}/api/services/app/TestItem/GetAllPage'.format(apihost)
    headers = {'Host': apihost, 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token), 'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Origin': host, 'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(url, headers=headers)
    inf = r.json()['result']
    re = []
    for i in range(0, len(inf)):
        if inf[i]['type'] in (3, 4, 5, 6):
            re.append(inf[i])
    return re


# 找出所有的物资信息
def wl_batchinformation(host, apihost, tenant, token):
    url = '{}/api/services/app/BatchInformation/GetManufacturerBatchNumberList'.format(apihost)
    headers = {'Host': apihost, 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token), 'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Origin': host, 'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(url, headers=headers)
    inf = r.json()['result']
    return inf


# 根据项目找出试剂、质控
def wl_testbatch(host, apihost, tenant, token):
    test = wl_getallpage(host, apihost, tenant, token)
    batch = wl_batchinformation(host, apihost, tenant, token)
    HBsAg = ['HBsAg']
    HCVAb = ['HCVAb']
    HIVAb = ['HIVAb']
    Syphilis = ['TPAb']
    for i in range(0, len(test)):
        if test[i]['type'] == 3:
            HBsAg.append(test[i])
        elif test[i]['type'] == 4:
            HCVAb.append(test[i])
        elif test[i]['type'] == 5:
            HIVAb.append(test[i])
        elif test[i]['type'] == 6:
            Syphilis.append(test[i])

        # 因为一个检验项目里可能存在多个物质批号，因此做两个循环分别取出试剂和质控品
        for ii in range(0, len(batch)):
            # materialType 枚举  0试剂；1质控
            if str(test[i]['id']) in batch[ii]['baseMaterial']['testItemId']:
                if batch[ii]['baseMaterial']['materialType'] == 0:
                    if batch[ii]['inventory']['qty'] != 0:
                        # print('试剂', batch[ii])
                        if test[i]['type'] == 3:
                            HBsAg.append(batch[ii])
                        elif test[i]['type'] == 4:
                            HCVAb.append(batch[ii])
                        elif test[i]['type'] == 5:
                            HIVAb.append(batch[ii])
                        elif test[i]['type'] == 6:
                            Syphilis.append(batch[ii])
                        break
        for j in range(0, len(batch)):
            # materialType 枚举  0试剂；1质控
            if str(test[i]['id']) in batch[j]['baseMaterial']['testItemId']:
                if batch[j]['baseMaterial']['materialType'] == 1:
                    if batch[j]['inventory']['qty'] != 0:
                        # print('质控', batch[j])
                        if test[i]['type'] == 3:
                            HBsAg.append(batch[j])
                        elif test[i]['type'] == 4:
                            HCVAb.append(batch[j])
                        elif test[i]['type'] == 5:
                            HIVAb.append(batch[j])
                        elif test[i]['type'] == 6:
                            Syphilis.append(batch[j])
                        break
    # 打包给下一个方法使用
    print(HBsAg)
    print(HIVAb)
    print(HCVAb)
    print(Syphilis)
    alltest = [HBsAg, HIVAb, HCVAb, Syphilis]
    return alltest


# 生成样板信息
def wl_savebody(test):
    body = {"billStatus": 0, "batchNumber": "{}01".format(time.strftime("%Y%m%d", time.localtime())),
        "testItemId": test[1]['id'],
        "samplePlateNumber": "{}{}".format(test[0], time.strftime("%Y%m%d%H%M%S", time.localtime())),
        "qcBatchNumber": test[3]['id'], "reaBatchNumber": test[2]['id'], "sortDirection": 1,
        "batchRemark": "{}{}".format(test[0], time.strftime("%Y%m%d%H%M%S", time.localtime())), "detailLists": [],
        "reaBatchInformation": test[2], "qcBatchInformation": test[3], "testTemplateMain": {"billStatus": 0}}
    return body


# 保存样板
def wl_save(host, apihost, tenant, token):
    alltest = wl_testbatch(host, apihost, tenant, token)
    print(alltest)
    url = '{}/api/services/app/SpecimenLayoutManagementBetail/SaveNew'.format(apihost)
    headers = {'Host': apihost, 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token), 'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Content-Type': 'application/json;charset=UTF-8', 'Origin': host,
        'Referer': '{}/'.format(host), 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    for i in range(0, len(alltest)):
        body = wl_savebody(alltest[i])
        r = requests.post(url, headers=headers, json=body)
        billinf = r.json()['result']
        time.sleep(1)
        print(billinf)
        # return billinf


# 生成样板内容
def wl_slm_ori(date):
    slm = {"TestName": "HCV", "Operator": "陈彦颖", "TestTime": "2023-02-17 12:14:12", "PlateNo": "20230217121412HCV", "CutOff": "0.123",
        "SampleResults": [
            {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "A01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"},
            {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "B01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"},
            {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "C01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"},
            {"BatchInfoName": "PC", "SpecimenBillNo": None, "PositionNo": "D01", "Info": None, "OriginResult": "3.319", "AnalysisInfo": "26.984", "Result": "+"},
            {"BatchInfoName": "PC", "SpecimenBillNo": None, "PositionNo": "E01", "Info": None, "OriginResult": "3.361", "AnalysisInfo": "27.325", "Result": "+"},
            {"BatchInfoName": "QC", "SpecimenBillNo": None, "PositionNo": "F01", "Info": None, "OriginResult": "0.419", "AnalysisInfo": "3.407", "Result": "+"}]
        }
    for i in range(0, len(date)):
        ii = {"BatchInfoName": date[i]['BillNo'], "SpecimenBillNo": None, "PositionNo": date[i]['PositionNo'], "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"}


# print(wl_save('http://192.168.1.112:1002', 'http://192.168.1.112:21021', '3',
#               'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA2IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjExMUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFkbWluIiwiaHR0cDovL3d3dy5hc3BuZXRib2lsZXJwbGF0ZS5jb20vaWRlbnRpdHkvY2xhaW1zL3RlbmFudElkIjoiMyIsInN1YiI6IjEwMDA2IiwianRpIjoiZjQ5ZjM1ZjQtNmNmMy00N2I5LWJlODAtYjA1M2VlYTBlYTQ3IiwiaWF0IjoxNjc2Njg3Mzg1LCJuYmYiOjE2NzY2ODczODUsImV4cCI6MTY3Njc3Mzc4NSwiaXNzIjoiTWtDaGVja1N5c3RlbSIsImF1ZCI6Ik1rQ2hlY2tTeXN0ZW0ifQ.ZWc7kJR7SESIXPQmuj1RigHBNlBAyIM7yJ3BuzYN4L4'))
