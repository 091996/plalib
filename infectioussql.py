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
                             outer apply (select IsCheck from QuickCheckResult where SpecimenBillNo = a.BillNo) e
                    where (a.SampleTestType <> 0 or (a.SampleTestType = 0 and e.IsCheck = 1)) and a.BillStatus <> 4 and a.SampleTestType <> 3
                      and a.TenantId = {}
                      and b.TenantId = {}
                      and datediff(day, d.CreationTime, getdate()) = 0
                      and c.OriginalResults is null
                    group by a.BillNo, d.SerialNumber order by d.SerialNumber""".format(tenant, tenant)
    elif '卫光' in name:
        sql = """select a.BillNo from Specimen a
                    join TestItem b on 1 = 1 and b.Type in (3, 4, 5, 6)
                    left join SampleResults c on c.SpecimenBillNo = a.BillNo and c.TestItemId = b.Id and c.BillStatus = 3
                where a.BillStatus <> 4 and a.TenantId = {} and b.TenantId = {} and datediff(day, a.CreationTime, getdate()) = 0
                group by a.BillNo""".format(tenant, tenant)
    else:
        sql = """select a.BillNo
                    from Specimen a
                             join TestItem b on 1 = 1 and b.Type in (3, 4, 5, 6)
                             left join SampleResults c on a.BillNo = c.SpecimenBillNo and b.Id = c.TestItemId and c.BillStatus = 3
                             outer apply (select IsCheck from QuickCheckResult where SpecimenBillNo = a.BillNo) d
                    where (a.SampleTestType <> 0 or (a.SampleTestType = 0 and d.IsCheck = 1)) and a.BillStatus <> 4 and a.SampleTestType <> 3
                    and a.TenantId = {} 
                    and b.TenantId = {}
                    and datediff(day, a.CreationTime, getdate()) = 0
                    group by a.BillNo""".format(tenant, tenant)
    return sql

# 卫伦先找出酶免4项的检验项目信息
def wl_getallpage(host, apihost, tenant, token):
    url = '{}/api/services/app/TestItem/GetAllPage'.format(apihost)
    header = {'Host': apihost.split('//', -1)[1], 'Connection': 'keep-alive', 'Accept': 'application/json, text/plain, */*',
        'Authorization': 'Bearer {}'.format(token), 'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Origin': host, 'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(url, headers=header)
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
                    try:
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
                    except:
                        continue
        for j in range(0, len(batch)):
            # materialType 枚举  0试剂；1质控
            if str(test[i]['id']) in batch[j]['baseMaterial']['testItemId']:
                if batch[j]['baseMaterial']['materialType'] == 1:
                    try:
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
                    except:
                        continue
    # 打包给下一个方法使用
    alltest = [HBsAg, HIVAb, HCVAb, Syphilis]
    return alltest

# 卫伦生成样板信息
def wl_savebody(test):
    body = {"billStatus": 0, "batchNumber": "{}01".format(time.strftime("%Y%m%d", time.localtime())),
        "testItemId": test[1]['id'],
        "samplePlateNumber": "{}{}".format(test[0], time.strftime("%Y%m%d%H%M%S", time.localtime())),
        "qcBatchNumber": test[3]['id'], "reaBatchNumber": test[2]['id'], "sortDirection": 1,
        "batchRemark": "{}01001".format(time.strftime("%Y%m%d", time.localtime())), "detailLists": [],
        "reaBatchInformation": test[2], "qcBatchInformation": test[3], "testTemplateMain": {"billStatus": 0}}
    return body

# 卫伦保存样板
def wl_save(tenantname, host, apihost, tenant, token, infdate):
    alltest = wl_testbatch(host, apihost, tenant, token)
    if '卫光' in tenantname or '同路' in tenantname:
        url = '{}/api/services/app/SpecimenLayoutManagementBetail/Save'.format(apihost)
    else:
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
        # print(infdate)
        DataSource = wl_slm_ori(infdate, alltest[i][0], billinf['samplePlateNumber'], tenantname)
        # print(DataSource.encode('utf-8').decode('unicode_escape'))
        time.sleep(1)
        if '卫光' in tenantname:
            sql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'URANUS-AE115', N'" + DataSource.encode('utf-8').decode('unicode_escape') + "', N'" + billinf['samplePlateNumber'] + "', 0, " + tenant + ", getdate(), null, getdate(), null);"
        elif '同路' in tenantname:
            sql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'URANUS-AE145', N'" + DataSource.encode('utf-8').decode('unicode_escape') + "', N'" + billinf['samplePlateNumber'] + "', 0, " + tenant + ", getdate(), null, getdate(), null);"
        else:
            sql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'ADDCARE', N'" + DataSource.encode('utf-8').decode('unicode_escape') + "', N'"+billinf['samplePlateNumber']+"', 0, "+tenant+", getdate(), null, getdate(), null);"
        # print([alltest[i][0], sql])
        ret.append([alltest[i][0], r.json()['error'], sql])
    return ret

# 卫伦生成样板内容
def wl_slm_ori(date, testname, sampno, tenantname):
    if '卫光' in tenantname or '同路' in tenantname:
        slm = {"TestName": testname, "Operator": "system", "TestTime": time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime()), "PlateNo": sampno,
            "SampleResults": [
                {"BatchInfoName": "NC", "SpecimenBillNo": "NC", "PositionNo": "A01", "Info": "0.003", "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"},
                {"BatchInfoName": "NC", "SpecimenBillNo": "NC", "PositionNo": "B01", "Info": "0.003", "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"},
                {"BatchInfoName": "NC", "SpecimenBillNo": "NC", "PositionNo": "C01", "Info": "0.003", "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"},
                {"BatchInfoName": "PC", "SpecimenBillNo": "NC", "PositionNo": "D01", "Info": "3.319", "OriginResult": "3.319", "AnalysisInfo": "26.984", "Result": "+"},
                {"BatchInfoName": "PC", "SpecimenBillNo": "NC", "PositionNo": "E01", "Info": "3.361", "OriginResult": "3.361", "AnalysisInfo": "27.325", "Result": "+"},
                {"BatchInfoName": "QC", "SpecimenBillNo": "NC", "PositionNo": "F01", "Info": "0.419", "OriginResult": "0.419", "AnalysisInfo": "3.407", "Result": "+"}
            ]}
    else:
        slm = {"TestName": testname, "Operator": "system", "TestTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), "PlateNo": sampno, "CutOff": "0.123",
            "SampleResults": [
                {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "A01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "阴性"},
                {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "B01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "阴性"},
                {"BatchInfoName": "NC", "SpecimenBillNo": None, "PositionNo": "C01", "Info": None, "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "阴性"},
                {"BatchInfoName": "PC", "SpecimenBillNo": None, "PositionNo": "D01", "Info": None, "OriginResult": "3.319", "AnalysisInfo": "26.984", "Result": "阳性"},
                {"BatchInfoName": "PC", "SpecimenBillNo": None, "PositionNo": "E01", "Info": None, "OriginResult": "3.361", "AnalysisInfo": "27.325", "Result": "阳性"},
                {"BatchInfoName": "QC", "SpecimenBillNo": None, "PositionNo": "F01", "Info": None, "OriginResult": "0.419", "AnalysisInfo": "3.407", "Result": "阳性"}]}
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

        if 'Result' in ori:
            if '卫光' in tenantname or '同路' in tenantname:
                ii = {"BatchInfoName": "SMP1", "SpecimenBillNo": date[i]['BillNo'], "PositionNo": date[i]['PositionNo'], "Info": ori["OriginResult"]}
                ii.update(ori)
                if ii['Result'] == '阳性':
                    ii.update({'Result': '+'})
                else:
                    ii.update({'Result': '-'})
            else:
                ii = {"BatchInfoName": date[i]['BillNo'], "SpecimenBillNo": None, "PositionNo": date[i]['PositionNo'], "Info": None}
                ii.update(ori)
        slm["SampleResults"].append(ii)
    slm = json.dumps(slm)
    # print('整版的内容', slm)
    return slm


# 因为同路的没有自动解析，所以需要调用后端接口进行解析
def tl_OriginalResultid(tenant):
    sql = "select top 1 Id from OriginalResult where TenantId = " + tenant + " and EquipmentName = 'URANUS-AE145' order by CreationTime desc"
    return sql


def tl_TestAE(apihost, tenant, original, textBrowser):
    url = '{}/api/services/app/OriginalResult/TestAE'.format(apihost)
    headers = {
        'Host': apihost.split('//', -1)[1],
        'Connection': 'keep-alive',
        'accept': '*/*',
        'Authorization': 'null',
        'Cookie': 'jenkins-timestamper-offset=-28800000; JSESSIONID.a498e839=node0fj1l6faupmma14pc5ljau9k280.node0; screenResolution=1600x900; .AspNetCore.Antiforgery.nZNI7wbmT0k=CfDJ8BrRSekVSMFAsv2lVQp6vT7XIYvHd2qmVaI70NFQgC8en-9Saq7Nn39qVzjpklbQPY3mZV2j-iceQ_OSh_AlL6BtSzfJLBjPcJfPpH5tyH46lzS6uLTWMNOSD3ZFRm5Hkb6J4pkGZMZn7kv6ZFmEfRs; XSRF-TOKEN=CfDJ8BrRSekVSMFAsv2lVQp6vT6u0h1yjh_XIphaPZPJnfVZihSsPtUqf59tPZcmKk0a8WobrvjfSa6Hi6l6gOIib9k7QGfc5jM8LXEaKs6jkv_oaf2tg3AJECWWdiLdv1I761yC1XtbRyNsGgLUB7zKw9k; tenantId={}; vue_admin_template_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA1IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjU4MzgzMTM1NUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFkbWluIiwiaHR0cDovL3d3dy5hc3BuZXRib2lsZXJwbGF0ZS5jb20vaWRlbnRpdHkvY2xhaW1zL3RlbmFudElkIjoiMiIsInN1YiI6IjEwMDA1IiwianRpIjoiNGMxMDU4YjktNjgyOC00OTg0LThhNTgtM2E1MWU4OGRmMGY0IiwiaWF0IjoxNjgwMjM1MzkwLCJuYmYiOjE2ODAyMzUzOTAsImV4cCI6MTY4MDMyMTc5MCwiaXNzIjoiTWtDaGVja1N5c3RlbSIsImF1ZCI6Ik1rQ2hlY2tTeXN0ZW0ifQ.VeI_YqVzMb1zitxfgs0VEJYKlgF7Jjrc870d6jqaJfU; UserId=10005'.format(tenant),
        'Content-Type': 'application/json-patch+json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        'X-XSRF-TOKEN': 'CfDJ8BrRSekVSMFAsv2lVQp6vT6u0h1yjh_XIphaPZPJnfVZihSsPtUqf59tPZcmKk0a8WobrvjfSa6Hi6l6gOIib9k7QGfc5jM8LXEaKs6jkv_oaf2tg3AJECWWdiLdv1I761yC1XtbRyNsGgLUB7zKw9k',
        'Referer': '{}/swagger/index.html'.format(apihost), 'Origin': apihost, 'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.post(url, headers=headers, json={"id": original})
    if r.json()['success']:
        log = '解析成功'
    else:
        log = r.json()['error']['details']
    textBrowser.append('{} {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), log))


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
                        # print('试剂', batchs[ii])
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
            if str(item[i]['testItemId']) in str(batchs[j]['baseMaterial']['testItemId']):
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
    alltest = [HBsAg, HIVAb, HCVAb, Syphilis]
    return alltest


# 丹霞样板基本结构
def dx_layoutmanagementbetail(inf, batchnumber):
    jsondata = {
        "billStatus": 0,
        "batchNumber": "{}01".format(time.strftime("%Y%m%d", time.localtime())),
        "batchRemark": batchnumber,
        "testItemId": int(inf[1]['testItemId']),
        "inspectionTemplate": inf[1]['billNo'],
        "samplePlateNumber": batchnumber,
        "reaBatchNumber": inf[2]['id'],
        "qcBatchNumber": inf[3]['id'],
        "sortDirection": 1,  # 横排竖排的字段，这里默认给横排
        "sortSerialNumberStart": "",
        "sortSerialNumberEnd": "",
        "reaBatchInformation": inf[2],
        "qcBatchInformation": inf[3],
        "testTemplateMain": {"billStatus": 0},
        "detailLists": inf[1]['detailLists']
    }
    row = []
    col = []
    li = inf[1]['detailLists']
    for ii in range(0, len(li)):
        # 原数据里缺失【inspectionNo】【messageType】字段
        jsondata["detailLists"][ii].update({"inspectionNo": jsondata["detailLists"][ii]["type"], "messageType": 0})
        row.append(li[ii]['rowNum'])
        col.append(li[ii]['columnNum'])
    return max(row), max(col), jsondata


#丹霞获取版号号码
def dx_getsinceplatenumber(host, apihost, tenant, token):
    url = '{}/api/services/app/SpecimenLayoutManagementBetail/GetSincePlateNumber'.format(apihost)
    headers = {'Host': apihost.split('//', -1)[1], 'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*', 'Authorization': 'Bearer {}'.format(token),
        'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Origin': host,
        'Referer': '{}/'.format(host), 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    r = requests.get(url, headers=headers)
    res = r.json()['result']
    return res


# 样板数据生成
def detaillists(platenumber, testname, typeid, date, detail):
    # typeid 3:HBsAg;4:HCVAb;5:HIVAb;6:TPAb
    a = {"BatchInfoName": "", "SpecimenBillNo": "", "PositionNo": "", "Info": "", "OriginResult": "", "AnalysisInfo": "", "Result": ""}  # 这个是孔的信息
    row = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']  # 这里做个对应 rowNum
    col = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']  # 这里可以用 columnNum 作为下标找到对应的值
    # 定义好基本的标本内容

    N = {"Info": "0.002", "OriginResult": "0.003", "AnalysisInfo": "0.024", "Result": "-"}
    P = [{"Info": "3.319", "OriginResult": "3.319", "AnalysisInfo": "26.984", "Result": "+"}, {"Info": "3.361", "OriginResult": "3.361", "AnalysisInfo": "27.325", "Result": "+"}]
    Q = {"Info": "0.419", "OriginResult": "0.419", "AnalysisInfo": "3.407", "Result": "+"}

    hbsagy = [{"Info": "0.001", "OriginResult": "0.001", "AnalysisInfo": "0.010", "Result": "-"}, {"Info": "0.002", "OriginResult": "0.002", "AnalysisInfo": "0.019", "Result": "-"}, {"Info": "0.003", "OriginResult": "0.003", "AnalysisInfo": "0.029", "Result": "-"}]
    hbsagf = {"Info": "0.306", "OriginResult": "0.306", "AnalysisInfo": "2.914", "Result": "+"}

    hcvaby = [{"Info": "0.000", "OriginResult": "0.000", "AnalysisInfo": "0.000", "Result": "-"}, {"Info": "0.001", "OriginResult": "0.001", "AnalysisInfo": "0.008", "Result": "-"}, {"Info": "0.002", "OriginResult": "0.002", "AnalysisInfo": "0.016", "Result": "-"}, {"Info": "0.003", "OriginResult": "0.003", "AnalysisInfo": "0.025", "Result": "-"}, {"OriginResult": "0.004", "AnalysisInfo": "0.033", "Result": "-"}]
    hcvabf = {"Info": "0.572", "OriginResult": "0.572", "AnalysisInfo": "4.689", "Result": "+"}

    hivaby = [{"Info": "0.001", "OriginResult": "0.001", "AnalysisInfo": "0.008", "Result": "-"}, {"Info": "0.002", "OriginResult": "0.002", "AnalysisInfo": "0.019", "Result": "-"}, {"Info": "0.003", "OriginResult": "0.003", "AnalysisInfo": "0.029", "Result": "-"}]
    hivabf = {"Info": "0.216", "OriginResult": "0.216", "AnalysisInfo": "1.756", "Result": "+"}

    tpaby = [{"Info": "0.000", "OriginResult": "0.000", "AnalysisInfo": "0.000", "Result": "-"}, {"Info": "0.001", "OriginResult": "0.001", "AnalysisInfo": "0.006", "Result": "-"}, {"Info": "0.002", "OriginResult": "0.002", "AnalysisInfo": "0.011", "Result": "-"}]
    tpabf = {"Info": "0.711", "OriginResult": "0.711", "AnalysisInfo": "2.843", "Result": "+"}

    ii = len(detail) - len(date)  # 这里计算样板模板里有几个固定的
    sol = {"TestName": testname, "Operator": "Administrator", "TestTime": "{}".format(time.strftime("%Y年%m月%d日 %H:%M:%S", time.localtime())), "PlateNo": platenumber, "SampleResults": []}
    for i in range(0, len(detail)):
        if i >= ii:
            among = date[i-ii]
            a.update({"BatchInfoName": "SMP", "SpecimenBillNo": among['BillNo'], "PositionNo": "{}{}".format(row[detail[i]['rowNum']], col[detail[i]['columnNum']])})
            if int(typeid) == 3 and among['HBsAg'] == '-':
                a.update(random.choice(hbsagy))
            elif int(typeid) == 3 and among['HBsAg'] == '+':
                a.update(hbsagf)

            elif int(typeid) == 4 and among['HCVAb'] == '-':
                a.update(random.choice(hcvaby))
            elif int(typeid) == 4 and among['HCVAb'] == '+':
                a.update(hcvabf)

            elif int(typeid) == 5 and among['HIVAb'] == '-':
                a.update(random.choice(hivaby))
            elif int(typeid) == 5 and among['HIVAb'] == '+':
                a.update(hivabf)

            elif int(typeid) == 6 and among['TPAb'] == '-':
                a.update(random.choice(tpaby))
            elif int(typeid) == 6 and among['TPAb'] == '+':
                a.update(tpabf)
        else:
            among = detail[i]
            if 'N' in among['type']:
                a.update({"BatchInfoName": "NC", "SpecimenBillNo": "NC", "PositionNo": "{}{}".format(row[among['rowNum']], col[among['columnNum']])})
                a.update(N)
            elif 'P' in among['type']:
                a.update({"BatchInfoName": "PC", "SpecimenBillNo": "PC", "PositionNo": "{}{}".format(row[among['rowNum']], col[among['columnNum']])})
                a.update(random.choice(P))
            elif 'Q' in among['type']:
                if int(typeid) == 3:
                    a.update({"BatchInfoName": "QC-HBsAg", "SpecimenBillNo": "QC-HBsAg", "PositionNo": "{}{}".format(row[among['rowNum']], col[among['columnNum']])})
                elif int(typeid) == 4:
                    a.update({"BatchInfoName": "QC-HCVAb", "SpecimenBillNo": "QC-HCVAb", "PositionNo": "{}{}".format(row[among['rowNum']], col[among['columnNum']])})
                elif int(typeid) == 5:
                    a.update({"BatchInfoName": "QC-HIVAb", "SpecimenBillNo": "QC-HIVAb", "PositionNo": "{}{}".format(row[among['rowNum']], col[among['columnNum']])})
                elif int(typeid) == 6:
                    a.update({"BatchInfoName": "QC-TPAb", "SpecimenBillNo": "QC-TPAb", "PositionNo": "{}{}".format(row[among['rowNum']], col[among['columnNum']])})
                a.update(Q)
        if a['BatchInfoName'] != '':  # 不知道为啥，会出现空值的情况
            sol['SampleResults'].append(a)
        a = {"BatchInfoName": "", "SpecimenBillNo": "", "PositionNo": "", "Info": "", "OriginResult": "", "AnalysisInfo": "", "Result": ""}  # 加在这里是重置一下，不重置会一直更新
    return sol


# 丹霞样板中加入样本
def dx_savenew(host, apihost, tenant, token, date):
    relist = []
    url = '{}/api/services/app/SpecimenLayoutManagementBetail/SaveNew'.format(apihost)
    headers = {'Host': apihost.split('//', -1)[1], 'Connection': 'keep-alive',
        'Accept': 'application/json, text/plain, */*', 'Authorization': 'Bearer {}'.format(token),
        'Abp.TenantId': tenant,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
        '.AspNetCore.Culture': 'zh-hans', 'Content-Type': 'application/json;charset=UTF-8',
        'Origin': host, 'Referer': '{}/'.format(host),
        'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    batchs = dx_batchinformation(host, apihost, tenant, token)
    for i in range(0, len(batchs)):
        inf = batchs[i]
        batchNumber = dx_getsinceplatenumber(host, apihost, tenant, token)
        betail = dx_layoutmanagementbetail(inf, batchNumber)
        positionno = []  # 这里是想把排序号拿出来，找到排序的最大值与最小值。用来更新【sortSerialNumberStart】【】
        # 这里的这个方式只能是横排的。
        for d in range(0, len(date)):
            positionno.append(int(date[d]['PositionNo']))
            r = int((d + betail[1])/12) + betail[0]
            c = d + betail[1] + 1
            betail[2]['detailLists'].append({"type": int(date[d]['PositionNo']), "inspectionNo": int(date[d]['PositionNo']), "messageType": 1, "rowNum": r, "columnNum": c})
        betail[2].update({"sortSerialNumberStart": min(positionno)})
        betail[2].update({"sortSerialNumberEnd": max(positionno)})
        # print(inf)
        # print(betail[2]['samplePlateNumber'], inf[1]['name'], inf[1]['testItem']['type'], date, betail[2]['detailLists'])
        s = detaillists(betail[2]['samplePlateNumber'], inf[0], inf[1]['testItem']['type'], date, betail[2]['detailLists'])
        DataSource = json.dumps(s, ensure_ascii=False)
        r = requests.post(url, headers=headers, data=json.dumps(betail[2], ensure_ascii=False).encode("utf-8"))
        # print(r.text)
        sql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES ((select Value from SysConfigure where TenantId = "+tenant+" and Code = 'ALY01'), N'"+DataSource+"', N'"+betail[2]['samplePlateNumber']+"', 0, "+tenant+", getdate(), null, null, null);"
        relist.append([inf[1]['name'], r.json()['error'], sql])
        time.sleep(1)
    return relist


# print(dx_savenew('http://192.168.1.112:1001', 'http://192.168.1.112:2001', '3',
#               'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA2IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjExMUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFkbWluIiwiaHR0cDovL3d3dy5hc3BuZXRib2lsZXJwbGF0ZS5jb20vaWRlbnRpdHkvY2xhaW1zL3RlbmFudElkIjoiMyIsInN1YiI6IjEwMDA2IiwianRpIjoiYmMwMjkxNTEtZTg0OC00MjYxLWEzZWYtMzE1YjAwZDE5NzM1IiwiaWF0IjoxNjc4MjQ4MDYzLCJuYmYiOjE2NzgyNDgwNjMsImV4cCI6MTY3ODMzNDQ2MywiaXNzIjoiTWtDaGVja1N5c3RlbSIsImF1ZCI6Ik1rQ2hlY2tTeXN0ZW0ifQ.hFGN0vhYALeGi8pxeqBoH15wNTY0B2_PD16PzF4MKKE',
# [{'BillNo': '2023030701', 'PositionNo': '1', 'HBsAg': '-', 'HCVAb': '-', 'HIVAb': '-', 'TPAb': '-'}, {'BillNo': '2023030702', 'PositionNo': '2', 'HBsAg': '-', 'HCVAb': '-', 'HIVAb': '-', 'TPAb': '-'}, {'BillNo': '2023030703', 'PositionNo': '3', 'HBsAg': '-', 'HCVAb': '-', 'HIVAb': '-', 'TPAb': '-'}]
# ))

