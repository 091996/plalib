import json
import random
import time
import requests


# 找出需要排板的标本
def findbill(tenant, name):
    if '丹霞' in name:
        sql = """select a.BillNo,d.SerialNumber
                    from Specimen a
                             join TestItem b on 1 = 1 and b.Type in (3, 4, 5, 6)
                             left join SampleResults c on a.BillNo = c.SpecimenBillNo and b.Id = c.TestItemId and c.BillStatus = 3
                             left join SpecimenBatchManagementDetail d on d.SpecimenBillNo = a.BillNo
                    where a.TenantId = {}
                      and b.TenantId = {}
                      and datediff(day, d.CreationTime, getdate()) = 0
                      and c.OriginalResults is null
                    group by a.BillNo, d.SerialNumber order by d.SerialNumber""".format(tenant, tenant)
    else:
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

# 卫伦先找出酶免4项的检验项目信息
def wl_getallpage(apihost):
    url = '{}/api/services/app/TestItem/GetAllPage'.format(apihost)
    r = requests.get(url)
    inf = r.json()['result']
    re = []
    for i in range(0, len(inf)):
        if inf[i]['type'] in (3, 4, 5, 6):
            re.append(inf[i])
    return re

# 卫伦找出所有的物资信息
def wl_batchinformation(host, apihost, tenant, token):
    url = '{}/api/services/app/BatchInformation/GetManufacturerBatchNumberList'.format(apihost)
    header = {'Accept': 'application/json, text/plain, */*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Abp.TenantId': tenant, 'Referer': '{}/'.format(host),
        'Authorization': 'Bearer {}'.format(token), 'Origin': host, 'Connection': 'keep-alive', 'Host': apihost.split('//', -1)[1]}
    r = requests.get(url=url, headers=header)
    inf = r.json()['result']
    return inf

# 卫伦根据项目找出试剂、质控
def wl_testbatch(host, apihost, tenant, token):
    test = wl_getallpage(apihost)
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
    alltest = [HBsAg, HIVAb, HCVAb, Syphilis]
    return alltest

# 卫伦生成样板信息
def wl_savebody(test):
    body = {"billStatus": 0, "batchNumber": "{}01".format(time.strftime("%Y%m%d", time.localtime())),
        "testItemId": test[1]['id'],
        "samplePlateNumber": "{}{}".format(test[0], time.strftime("%Y%m%d%H%M%S", time.localtime())),
        "qcBatchNumber": test[3]['id'], "reaBatchNumber": test[2]['id'], "sortDirection": 1,
        "batchRemark": "{}{}".format(test[0], time.strftime("%Y%m%d%H%M%S", time.localtime())), "detailLists": [],
        "reaBatchInformation": test[2], "qcBatchInformation": test[3], "testTemplateMain": {"billStatus": 0}}
    return body

# 卫伦保存样板
def wl_save(host, apihost, tenant, token, infdate):
    alltest = wl_testbatch(host, apihost, tenant, token)
    # print(alltest)
    url = '{}/api/services/app/SpecimenLayoutManagementBetail/SaveNew'.format(apihost)
    headers = {'Host': apihost.split('//', -1)[1], 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token), 'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Content-Type': 'application/json;charset=UTF-8', 'Origin': host,
        'Referer': '{}/'.format(host), 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    ret = []
    for i in range(0, len(alltest)):
        body = wl_savebody(alltest[i])
        r = requests.post(url, headers=headers, json=body)
        billinf = r.json()['result']
        # print(billinf)
        # print('项目', alltest[i][0])
        # print(infdate)
        DataSource = wl_slm_ori(infdate, alltest[i][0], billinf['samplePlateNumber'])
        time.sleep(1)
        sql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'ADDCARE', N'"+DataSource+"', N'"+billinf['samplePlateNumber']+"', 0, "+tenant+", getdate(), null, getdate(), null);"
        # print([alltest[i][0], sql])
        ret.append([alltest[i][0], billinf['samplePlateNumber'], sql])
    return ret

# 卫伦生成样板内容
def wl_slm_ori(date, testname, sampno):
    slm = {"TestName": testname, "Operator": "system", "TestTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "PlateNo": sampno, "CutOff": "0.123",
        "SampleResults": [
            {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "A01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "阴性"},
            {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "B01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "阴性"},
            {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "C01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "阴性"},
            {"BatchInfoName": "PC", "SpecimenBillNo": None, "PositionNo": "D01", "Info": None, "OriginResult": "3.319", "AnalysisInfo": "26.984", "Result": "阳性"},
            {"BatchInfoName": "PC", "SpecimenBillNo": None, "PositionNo": "E01", "Info": None, "OriginResult": "3.361", "AnalysisInfo": "27.325", "Result": "阳性"},
            {"BatchInfoName": "QC", "SpecimenBillNo": None, "PositionNo": "F01", "Info": None, "OriginResult": "0.419", "AnalysisInfo": "3.407", "Result": "阳性"}
        ]}
    for i in range(0, len(date)):
        hbsagy = [{"OriginResult": "0.001", "AnalysisInfo": "0.010"}, {"OriginResult": "0.002", "AnalysisInfo": "0.019"}, {"OriginResult": "0.003", "AnalysisInfo": "0.029"}]
        hbsagf = {"OriginResult": "0.306", "AnalysisInfo": "2.914"}
        hcvaby = [{"OriginResult": "0.000", "AnalysisInfo": "0.000"}, {"OriginResult": "0.001", "AnalysisInfo": "0.008"}, {"OriginResult": "0.002", "AnalysisInfo": "0.016"}, {"OriginResult": "0.003", "AnalysisInfo": "0.025"}, {"OriginResult": "0.004", "AnalysisInfo": "0.033"}]
        hcvabf = {"OriginResult": "0.572", "AnalysisInfo": "4.689"}
        hivaby = [{"OriginResult": "0.001", "AnalysisInfo": "0.008"}, {"OriginResult": "0.002", "AnalysisInfo": "0.019"}, {"OriginResult": "0.003", "AnalysisInfo": "0.029"}]
        hivabf = {"OriginResult": "0.216", "AnalysisInfo": "1.756"}
        tpaby = [{"OriginResult": "0.000", "AnalysisInfo": "0.000"}, {"OriginResult": "0.001", "AnalysisInfo": "0.006"}, {"OriginResult": "0.002", "AnalysisInfo": "0.011"}]
        tpabf = {"OriginResult": "0.711", "AnalysisInfo": "2.843"}
        ori = {"OriginResult": "0.000", "AnalysisInfo": "0.000"}
        if date[i]['HBsAg'] == '-' and testname == 'HBsAg':
            ori.update(random.choice(hbsagy))
            ori.update({"Result": '阴性'})
        elif date[i]['HBsAg'] == '+' and testname == 'HBsAg':
            ori.update(hbsagf)
            ori.update({"Result": '阳性'})

        elif date[i]['HCVAb'] == '-' and testname == 'HCVAb':
            ori.update(random.choice(hcvaby))
            ori.update({'Result': '阴性'})
        elif date[i]['HCVAb'] == '+' and testname == 'HCVAb':
            ori.update(hcvabf)
            ori.update({'Result': '阳性'})

        elif date[i]['HIVAb'] == '-' and testname == 'HIVAb':
            ori.update(random.choice(hivaby))
            ori.update({'Result': '阴性'})
        elif date[i]['HIVAb'] == '+' and testname == 'HIVAb':
            ori.update(hivabf)
            ori.update({'Result': '阳性'})

        elif date[i]['TPAb'] == '-' and testname == 'TPAb':
            ori.update(random.choice(tpaby))
            ori.update({'Result': '阴性'})
        elif date[i]['TPAb'] == '+' and testname == 'TPAb':
            ori.update(tpabf)
            ori.update({'Result': '阳性'})

        ii = {"BatchInfoName": date[i]['BillNo'], "SpecimenBillNo": None, "PositionNo": date[i]['PositionNo'], "Info": None}
        ii.update(ori)
        slm["SampleResults"].append(ii)
    slm = json.dumps(slm)
    # print('整版的内容', slm)
    return slm


# 丹霞查找需要的样板信息
def dx_templatelist(host, apihost, tenant, token):
    url = '{}/api/services/app/TestTemplateBetail/GetAllList?maxResultCount=1000'.format(apihost)
    headers = {'Host': apihost.split('//', -1)[1],
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token),
        'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans',
        'Origin': host,
        'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    r = requests.get(url, headers=headers)
    ritems = r.json()['result']['items']
    items = []
    for ii in range(0, len(ritems)):
        if len(items) + 3 == int(ritems[ii]['testItem']['type']):
            items.append(ritems[ii])
    return items


# 丹霞找出试剂、质控信息
def dx_batchinformation(host, apihost, tenant, token):
    item = dx_templatelist(host, apihost, tenant, token)
    url = '{}/api/services/app/BatchInformation/GetManufacturerBatchNumberList'.format(apihost)
    headers = {'Host': apihost.split('//', -1)[1], 'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*', 'Authorization': 'Bearer {}'.format(token),
        'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Origin': host, 'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(url, headers=headers)
    batchs = r.json()['result']
    # for i in range(0, len(item)):
    #     # print(item[i]['testItemId'])
    #     print(item[i])
    #     for b in range(0, len(batchs)):
    #         # print(batchs[b]['baseMaterial']['testItemId'])
    #         if str(item[i]['testItemId']) in str(batchs[b]['baseMaterial']['testItemId']):
    #             print(batchs[b])

    HBsAg = ['HBsAg']
    HCVAb = ['HCVAb']
    HIVAb = ['HIVAb']
    Syphilis = ['TPAb']
    for i in range(0, len(item)):
        if item[i]['testItem']['type'] == 3:
            HBsAg.append(item[i])
        elif item[i]['testItem']['type'] == 4:
            HCVAb.append(item[i])
        elif item[i]['testItem']['type'] == 5:
            HIVAb.append(item[i])
        elif item[i]['testItem']['type'] == 6:
            Syphilis.append(item[i])

        # 因为一个检验项目里可能存在多个物质批号，因此做两个循环分别取出试剂和质控品
        for ii in range(0, len(batchs)):
            # materialType 枚举  0试剂；1质控
            if str(item[i]['testItemId']) in str(batchs[ii]['baseMaterial']['testItemId']):
                if batchs[ii]['baseMaterial']['materialType'] == 0:
                    if batchs[ii]['inventory']['qty'] != 0:
                        # print('试剂', batch[ii])
                        if item[i]['testItem']['type'] == 3:
                            HBsAg.append(batchs[ii])
                        elif item[i]['testItem']['type'] == 4:
                            HCVAb.append(batchs[ii])
                        elif item[i]['testItem']['type'] == 5:
                            HIVAb.append(batchs[ii])
                        elif item[i]['testItem']['type'] == 6:
                            Syphilis.append(batchs[ii])
                        break
        for j in range(0, len(batchs)):
            # materialType 枚举  0试剂；1质控
            if str(item[i]['testItemId']) in str(batchs[ii]['baseMaterial']['testItemId']):
                if batchs[j]['baseMaterial']['materialType'] == 1:
                    if batchs[j]['inventory']['qty'] != 0:
                        if item[i]['testItem']['type'] == 3:
                            HBsAg.append(batchs[j])
                        elif item[i]['testItem']['type'] == 4:
                            HCVAb.append(batchs[j])
                        elif item[i]['testItem']['type'] == 5:
                            HIVAb.append(batchs[j])
                        elif item[i]['testItem']['type'] == 6:
                            Syphilis.append(batchs[j])
                        break
    # 打包给下一个方法使用
    print(HBsAg)
    alltest = [HBsAg, HIVAb, HCVAb, Syphilis]
    return alltest




# def dx_savenew():
#     url = '/api/services/app/SpecimenLayoutManagementBetail/SaveNew'



# print(dx_batchinformation('http://192.168.1.112:1001', 'http://192.168.1.112:2001', '3',
#               'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA2IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjExMUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6WyJBZG1pbiIsIuWuoeaguCJdLCJodHRwOi8vd3d3LmFzcG5ldGJvaWxlcnBsYXRlLmNvbS9pZGVudGl0eS9jbGFpbXMvdGVuYW50SWQiOiIzIiwic3ViIjoiMTAwMDYiLCJqdGkiOiJjNDE4NTVmZS0wNzQxLTRmMDEtYjllYy0zZmRiYzNiZThiZDIiLCJpYXQiOjE2Nzc4MTQ1MDEsIm5iZiI6MTY3NzgxNDUwMSwiZXhwIjoxNjc3OTAwOTAxLCJpc3MiOiJNa0NoZWNrU3lzdGVtIiwiYXVkIjoiTWtDaGVja1N5c3RlbSJ9.tsWtvhpJ53VhjLi46TzckL9VyW9Je_CKCQ86oUPZbwk'
# ))

