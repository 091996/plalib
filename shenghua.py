import time

import requests


def findlist(tenant, tenantname):
    if '丹霞' in tenantname:
        sql = '''select a.BillNo,s.SerialNumber
                    from Specimen a
                             join TestItem b on 1 = 1 and b.Type in (1, 2)
                             join SpecimenBatchManagementDetail s on s.SpecimenBillNo = a.BillNo
                             left join SampleResults c on a.BillNo = c.SpecimenBillNo and b.Id = c.TestItemId and c.BillStatus = 3
                    where (b.Name like '%TP%' or b.Name like '%ALT%')
                      and a.TenantId = {}
                      and b.TenantId = {}
                      and datediff(day, a.CreationTime, getdate()) = 0
                      and c.OriginalResults is null
                    group by a.BillNo,s.SerialNumber order by s.SerialNumber'''.format(tenant, tenant)
    elif '卫伦' in tenantname:
        sql = '''select distinct a.BillNo, iif(c.m is null ,0,c.m) + ROW_NUMBER() OVER (ORDER BY (SELECT 1)) row
                from (select a.BillNo
                      from Specimen a
                               join TestItem b on 1 = 1 and b.Type in (1, 2)
                               left join SampleResults c on c.SpecimenBillNo = a.BillNo and b.Id = c.TestItemId and c.BillStatus = 3
                      where (b.Name like '%TP%' or b.Name like '%ALT%') and a.SampleTestType <> 3
                        and a.TenantId = {}
                        and b.TenantId = {}
                        and datediff(day, a.CreationTime, getdate()) = 0 and c.Id is null
                      group by a.BillNo) a
                         outer apply (select max(SampleResults.PlateNo) m from SampleResults where datediff(day, CreationTime, getdate()) = 0) c
                order by row'''.format(tenant, tenant)
    else:
        sql = '''select a.BillNo, ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS row
                from (select a.BillNo
                      from Specimen a
                               join TestItem b on 1 = 1 and b.Type in (1, 2)
                               left join SampleResults c on c.SpecimenBillNo = a.BillNo and b.Id = c.TestItemId and c.BillStatus = 3
                      where (b.Code like '%TP%' or b.Code like '%ALT%') and a.BillStatus <> 4
                        and a.TenantId = {}
                        and b.TenantId = {}
                        and datediff(day, a.CreationTime, getdate()) = 0
                      group by a.BillNo) a
                         left join SampleResults b on a.BillNo = b.SpecimenBillNo
group by a.BillNo'''.format(tenant, tenant)
    return sql

def baseinfo(date):
    # 这里返回的顺序与下面【base】的参数顺序是一样的
    # SampleTestType 枚举：0体检血样；1血辫血样；2回访血样；3电泳血样
    # Gender 枚举：1男；2女
    # IsAnticoagulant 是否带抗凝剂
    sql = "select BillNo,SampleTestType,Gender,IsAnticoagulant from Specimen where BillNo = '{}'".format(date['Code'])
    # print(sql)
    return sql


def sampleresults(tenant, tenancyName, date, base, status):
    altsql = None
    tpsql = None
    if status == 1:
        SampleTestType = base[1]
        IsAnticoagulant = base[3]
        # print(type(SampleTestType), type(IsAnticoagulant), type(float(date['TP'])))
        # print(SampleTestType, IsAnticoagulant, float(date['TP']))

        if SampleTestType == 0 and IsAnticoagulant is True and float(date['TP']) < 55:
            tpResults = '异常'
        elif SampleTestType == 0 and IsAnticoagulant is True and float(date['TP']) >= 55:
            tpResults = '正常'
        elif SampleTestType == 0 and IsAnticoagulant is False and float(date['TP']) < 65:
            tpResults = '异常'
        elif SampleTestType == 0 and IsAnticoagulant is False and float(date['TP']) >= 65:
            tpResults = '正常'
        elif SampleTestType == 1 and float(date['TP']) >= 55:
            tpResults = '正常'
        elif SampleTestType == 1 and float(date['TP']) < 55:
            tpResults = '异常'
        elif SampleTestType not in (0, 1) and float(date['TP']) >= 50:
            tpResults = '正常'
        else:
            tpResults = '异常'

        if float(date['ALT']) < 50:
            altResults = '正常'
        else:
            altResults = '异常'

        if '卫伦' in tenancyName:
            altsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, PlateNo, TestTime, IsTempResult) VALUES ( '"+date['Code']+"', '"+date['ALT']+"', '"+altResults+"', '"+date['ALT']+"', (select top 1 Id from TestItem where TenantId = "+tenant+" and Name like '%ALT%' and Type = 1), null, 0, null, null, "+tenant+", getdate(), null, getdate(), null, null, "+date['PlateNo']+", null, 0);"
            tpsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, PlateNo, TestTime, IsTempResult) VALUES ( '"+date['Code']+"', '"+date['TP']+"', '"+tpResults+"', '"+date['TP']+"', (select top 1 Id from TestItem where TenantId = "+tenant+" and Name like '%TP%' and Type = 2), null, 0, null, null, "+tenant+", getdate(), null, getdate(), null, null, "+date['PlateNo']+", null, 0);"
        elif '卫光' in tenancyName:
            altsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['ALT'] + "', '" + altResults + "', '" + date['ALT'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Code like '%ALT%' and Type = 1), null, 0, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
            tpsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['TP'] + "', '" + tpResults + "', '" + date['TP'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Code like '%TP%' and Type = 2), null, 0, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
        else:
            altsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['ALT'] + "', '" + altResults + "', '" + date['ALT'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Name like '%ALT%' and Type = 1), null, 0, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
            tpsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['TP'] + "', '" + tpResults + "', '" + date['TP'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Name like '%TP%' and Type = 2), null, 0, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"

    elif status == 0:
        if '卫光' in tenancyName:
            altsql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'MR-BS820M', N'MSH|^~\&|||||" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "||ORU^R01|68|P|2.3.1||||0||ASCII|||PID|" +date["PlateNo"]+ "|||||||O|||||||||||||||||||||||OBR|" +date["PlateNo"]+ "|" +date["BillNo"]+ "|65|^|N|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "||9^1^1^N0009||||" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|???|||||||||||||||||||||||||||||||||OBX|1|NM|ALT|????????????|" +date["ALT"]+ "|U/L|-|N|||F||29.611302|"+ time.strftime("%Y%m%d%H%M%S", time.localtime()) +"|||0|||M1|2008:AC9E#2008:8000|OBX|2|NM|TP|?????(????巨)|" +date["TP"]+ "|g/L|-|N|||F||62.869764|"+ time.strftime("%Y%m%d%H%M%S", time.localtime()) +"|||0|||M1|2001:9A0E#2001:C04E|', N'', 0, " + tenant + ", getdate(), null, getdate(), null);"
        elif '丹霞' in tenancyName:
            altsql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'MR-BS360s', N'MSH|^~\&|||||" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "||ORU^R01|68|P|2.3.1||||0||ASCII|||PID|" +date["PlateNo"]+ "|||||||O|||||||||||||||||||||||OBR|" +date["PlateNo"]+ "|" +date["BillNo"]+ "|" +date["PlateNo"]+ "|^|N|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "||9^1^1^N0009||||" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|???|||||||||||||||||||||||||||||||||OBX|1|NM|ALT|????????????|" +date["ALT"]+ "|U/L|-|N|||F||29.611302|"+ time.strftime("%Y%m%d%H%M%S", time.localtime()) +"|||0|||M1|2008:AC9E#2008:8000|OBX|2|NM|TP|?????(????巨)|" +date["TP"]+ "|g/L|-|N|||F||62.869764|"+ time.strftime("%Y%m%d%H%M%S", time.localtime()) +"|||0|||M1|2001:9A0E#2001:C04E|', N'', 0, " + tenant + ", getdate(), null, getdate(), null);"
        elif '卫伦' in tenancyName:
            altsql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'KH-ZY400', N'<STX>1H|\^&|ZY1200^1|1|A|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "<ETX>12<STX>2P|1<ETX>3F<STX>3O|1|1|ALT^1||B|" +date["Code"]+ "|||||" +date["PlateNo"]+ "|P|R|S|2<ETX>DE<STX>4R|1|ALT|" +date["ALT"]+ "|0.3|0.5|ml|H|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|2|<ETX>16<STX>5L|1<ETX>3E', N'', 0, "+ tenant +", getdate(), null, getdate(), null);"
            tpsql = "INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES (N'KH-ZY400', N'<STX>1H|\^&|ZY1200^1|1|A|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "<ETX>11<STX>2P|1<ETX>3F<STX>3O|1|1|TP^1||B|" +date["Code"]+ "|||||" +date["PlateNo"]+ "|P|R|S|13<ETX>2A<STX>4R|1|TP|" +date["TP"]+ "|0.3|0.5|ml|H|" +time.strftime("%Y%m%d%H%M%S", time.localtime())+ "|13|<ETX>70<STX>5L|1<ETX>3E', N'', 0, "+ tenant +", getdate(), null, getdate(), null);"
    return altsql, tpsql

def findbillno(tenant, billno):
    sql = "select BillNo from Specimen where Code = '{}' and TenantId = {}".format(billno, tenant)
    return sql

def seltopori(tenant, tenancyname):
    if '卫光' in tenancyname:
        sql = "select top 1 Id from OriginalResult where TenantId = " +tenant+ " and EquipmentName = 'MR-BS820M' order by CreationTime desc"
    elif '丹霞' in tenancyname:
        sql = "select top 1 Id from OriginalResult where TenantId = " +tenant+ " and EquipmentName = 'MR-BS360s' order by CreationTime desc"
    elif '卫伦' in tenancyname:
        sql = "select top 1 Id from OriginalResult where TenantId = " + tenant + " and EquipmentName = 'KH-ZY400' order by CreationTime desc"
    return sql

def OriginalResult(tenant, tenancyname, apihost, original):
    if '卫光' in tenancyname:
        url = '{}/api/services/app/OriginalResult/TestJobBS820?id={}'.format(apihost, original)
        headers = {
            'Host': apihost.split('//', -1)[1],
            'Connection': 'keep-alive', 'accept': 'text/plain',
            'Authorization': 'null',
            'Cookie': 'jenkins-timestamper-offset=-28800000; screenResolution=1600x900; JSESSIONID.92fd64e8=node0uoclcyoxtilz1vtc7h7rpnj7834.node0; tenantId={}; vue_admin_template_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA1IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjU4MzgzMTM1NUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFkbWluIiwiaHR0cDovL3d3dy5hc3BuZXRib2lsZXJwbGF0ZS5jb20vaWRlbnRpdHkvY2xhaW1zL3RlbmFudElkIjoiMiIsInN1YiI6IjEwMDA1IiwianRpIjoiZTNkZjM5ZTItZjgwZi00NTk3LTlhMGYtNzJkNjI2ZjAyNjRmIiwiaWF0IjoxNjc5NTU1NTk4LCJuYmYiOjE2Nzk1NTU1OTgsImV4cCI6MTY3OTY0MTk5OCwiaXNzIjoiTWtDaGVja1N5c3RlbSIsImF1ZCI6Ik1rQ2hlY2tTeXN0ZW0ifQ.UoLQOBztPlKHEJobNwU5LRKZmGPa_J2yvSUZ_Hd0Q98; UserId=10005; .AspNetCore.Antiforgery.rJ0iyJ2b1Ow=CfDJ8BrRSekVSMFAsv2lVQp6vT5Rt-YDolqkDzbYbtCmrJQf9sWgN6JlAYFh2kI0RoyOWuD9sU0GKAr6saUz5lAOpG8oZ-vI_w_k270Vg928Gxh3Yq9s2ksGZUYfdI6GEE4CevSU8YwShXoB4ljhH-zuxbY; .AspNetCore.Antiforgery.Ecw3POK6AOE=CfDJ8BrRSekVSMFAsv2lVQp6vT51XNrvdCpcp_g7hS5o2J5LkM9aqkmxqe580VAoOcmxruXKOixEQmKWGCdMgbZ5X3hup3qALpFXqn8kmRsVbF4RAvUZR5pmZzGvia159sP6Mu2-UEmxzFhw70ffcrvqAns; XSRF-TOKEN=CfDJ8BrRSekVSMFAsv2lVQp6vT78-6gPAu0a0VIuWS7l26vlroStBjuuXQR1YdHvQt2JdqmQCSwpiYCOTNTnhlL16VSKkZrtzlKD0hChWWk64wl-YliRQA_hoNw3ViilZwVrc62OfYsNWOeTedsRYAc63kw'.format(tenant),
            'Proxy-Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
            'X-XSRF-TOKEN': 'CfDJ8BrRSekVSMFAsv2lVQp6vT78-6gPAu0a0VIuWS7l26vlroStBjuuXQR1YdHvQt2JdqmQCSwpiYCOTNTnhlL16VSKkZrtzlKD0hChWWk64wl-YliRQA_hoNw3ViilZwVrc62OfYsNWOeTedsRYAc63kw',
            'Referer': '{}/swagger/index.html'.format(apihost),
            'Origin': apihost,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
    elif '丹霞' in tenancyname:
        url = '{}/api/services/app/OriginalResult/TestJobBS360s?id={}'.format(apihost, original)
        headers = {
            'Host': apihost.split('//', -1)[1],
            'Connection': 'keep-alive',
            'accept': 'text/plain',
            'Authorization': 'null',
            'Cookie': 'jenkins-timestamper-offset=-28800000; tenantId={}; vue_admin_template_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA2IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjExMUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6WyJBZG1pbiIsIuWuoeaguCJdLCJodHRwOi8vd3d3LmFzcG5ldGJvaWxlcnBsYXRlLmNvbS9pZGVudGl0eS9jbGFpbXMvdGVuYW50SWQiOiIzIiwic3ViIjoiMTAwMDYiLCJqdGkiOiIzZGM2ZDQ0Ny1kMGYzLTQ1YTAtYmNhMS00MjVkNjBiNGI4NTAiLCJpYXQiOjE2NzUzODUzMDgsIm5iZiI6MTY3NTM4NTMwOCwiZXhwIjoxNjc1NDcxNzA4LCJpc3MiOiJNa0NoZWNrU3lzdGVtIiwiYXVkIjoiTWtDaGVja1N5c3RlbSJ9.efmyDdUajVz_c3TqvmzIxKv8Y7ZcfmwnJLI-Xcetv2A; UserId=10006; .AspNetCore.Antiforgery.rJ0iyJ2b1Ow=CfDJ8BrRSekVSMFAsv2lVQp6vT5TKZfJ2sNlPOEbZsGeLwQzXtCbmk9Xld3qmPyHUxQF0haApgqLUiI47Csk-9fPdooUNnaMHUoBo7bFcqsBmHeNuMXQ43uo7FSeW-lqO9loPqKyZACThK3lbJkkxK5iZ7o; XSRF-TOKEN=CfDJ8BrRSekVSMFAsv2lVQp6vT5V9zFlNOzNLyFpj2H8ce-dJJL4RPPfGEruH0PgaWVQ_K4hI3vp22uv67vor2X8-siNH3ncmd6ZY-Z_-0tPMSbuYItrrkb8npjggEvuxs6l1VTxdG4TUm2eXnRuLebJ92o'.format(tenant),
            'Proxy-Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
            'X-XSRF-TOKEN': 'CfDJ8BrRSekVSMFAsv2lVQp6vT5V9zFlNOzNLyFpj2H8ce-dJJL4RPPfGEruH0PgaWVQ_K4hI3vp22uv67vor2X8-siNH3ncmd6ZY-Z_-0tPMSbuYItrrkb8npjggEvuxs6l1VTxdG4TUm2eXnRuLebJ92o',
            'Referer': '{}/swagger/index.html'.format(apihost),
            'Origin': apihost,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
    elif '卫伦' in tenancyname:
        url = '{}/api/services/app/OriginalResult/TestJobKHZY?id={}'.format(apihost, original)
        headers = {
            'Host': apihost.split('//', -1)[1],
            'Connection': 'keep-alive',
            'accept': 'text/plain',
            'Authorization': 'null',
            'Cookie': 'jenkins-timestamper-offset=-28800000; screenResolution=1600x900; JSESSIONID.92fd64e8=node0uoclcyoxtilz1vtc7h7rpnj7834.node0; tenantId={}; vue_admin_template_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1laWRlbnRpZmllciI6IjEwMDA1IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZSI6Im1rcG1hZG1pbiIsImh0dHA6Ly9zY2hlbWFzLnhtbHNvYXAub3JnL3dzLzIwMDUvMDUvaWRlbnRpdHkvY2xhaW1zL2VtYWlsYWRkcmVzcyI6IjU4MzgzMTM1NUBxcS5jb20iLCJBc3BOZXQuSWRlbnRpdHkuU2VjdXJpdHlTdGFtcCI6ImY5Zjg0YmQ1LTViNTktZTg5Yy01Njg0LTM5ZmJkN2M1ZjZlMSIsImh0dHA6Ly9zY2hlbWFzLm1pY3Jvc29mdC5jb20vd3MvMjAwOC8wNi9pZGVudGl0eS9jbGFpbXMvcm9sZSI6IkFkbWluIiwiaHR0cDovL3d3dy5hc3BuZXRib2lsZXJwbGF0ZS5jb20vaWRlbnRpdHkvY2xhaW1zL3RlbmFudElkIjoiMiIsInN1YiI6IjEwMDA1IiwianRpIjoiZTNkZjM5ZTItZjgwZi00NTk3LTlhMGYtNzJkNjI2ZjAyNjRmIiwiaWF0IjoxNjc5NTU1NTk4LCJuYmYiOjE2Nzk1NTU1OTgsImV4cCI6MTY3OTY0MTk5OCwiaXNzIjoiTWtDaGVja1N5c3RlbSIsImF1ZCI6Ik1rQ2hlY2tTeXN0ZW0ifQ.UoLQOBztPlKHEJobNwU5LRKZmGPa_J2yvSUZ_Hd0Q98; UserId=10005; .AspNetCore.Antiforgery.rJ0iyJ2b1Ow=CfDJ8BrRSekVSMFAsv2lVQp6vT5Rt-YDolqkDzbYbtCmrJQf9sWgN6JlAYFh2kI0RoyOWuD9sU0GKAr6saUz5lAOpG8oZ-vI_w_k270Vg928Gxh3Yq9s2ksGZUYfdI6GEE4CevSU8YwShXoB4ljhH-zuxbY; .AspNetCore.Antiforgery.Ecw3POK6AOE=CfDJ8BrRSekVSMFAsv2lVQp6vT51XNrvdCpcp_g7hS5o2J5LkM9aqkmxqe580VAoOcmxruXKOixEQmKWGCdMgbZ5X3hup3qALpFXqn8kmRsVbF4RAvUZR5pmZzGvia159sP6Mu2-UEmxzFhw70ffcrvqAns; .AspNetCore.Antiforgery.Qa5FbsRvkVY=CfDJ8BrRSekVSMFAsv2lVQp6vT5dtFgjGdbPEUMpNLGLqRN7u7LWQRBzEGLV_kG6zCUJtqcdk3iOjjqG1tLqZBPJmIOGEPE0DfsJk8UviUGy3PiRMgXZzseOQhl9wHFJiTtl5f0m_EE8nrRuZ8Wd7KQVsWE; XSRF-TOKEN=CfDJ8BrRSekVSMFAsv2lVQp6vT6_e3-p9LKYD6XCHUFlLuDPKMGGLBVDuVlD3qA10FY1Nf0Or2qCCPB5e_ECKFFZskY0uDuIZ9im2UKGoQw7gBgdAHc8mxhEsG0AVGu-rVMLHbxsephYUxhfTaEYKNbMy04'.format(tenant),
            'Proxy-Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.0.0 Safari/537.36',
            'X-XSRF-TOKEN': 'CfDJ8BrRSekVSMFAsv2lVQp6vT6_e3-p9LKYD6XCHUFlLuDPKMGGLBVDuVlD3qA10FY1Nf0Or2qCCPB5e_ECKFFZskY0uDuIZ9im2UKGoQw7gBgdAHc8mxhEsG0AVGu-rVMLHbxsephYUxhfTaEYKNbMy04',
            'Referer': '{}/swagger/index.html'.format(apihost),
            'Origin': apihost,
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
    r = requests.post(url, headers=headers)
    if r.json()['success']:
        log = '解析成功'
    else:
        log = r.json()['result']
    return log








