import time
from datetime import datetime

import requests


def wl_findlist(tenant):
    sql = '''select a.Code,s.SerialNumber
from Specimen a
         join TestItem b on 1 = 1 and b.Type in (1, 2)
         join SpecimenBatchManagementDetail s on s.SpecimenBillNo = a.BillNo
         left join SampleResults c on a.BillNo = c.SpecimenBillNo and b.Id = c.TestItemId and c.BillStatus = 3
where (b.Name like '%TP%' or b.Name like '%ALT%')
  and a.TenantId = {}
  and b.TenantId = {}
  and datediff(day, a.CreationTime, getdate()) = 0
  and c.OriginalResults is null
group by a.Code,s.SerialNumber order by s.SerialNumber'''.format(tenant, tenant)
    return sql

def wl_builtsql(tenant, dictdate):
    if dictdate["ALT"] != '0' and dictdate["TP"] != '0':
        sql = '''INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES ('MR-BS360s', 'MSH|^~\&|||||''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''||ORU^R01|'''+dictdate["P"]+'''|P|2.3.1||||0||ASCII|||PID|'''+dictdate["P"]+'''|||||||O|||||||||||||||||||||||OBR|'''+dictdate["P"]+'''|'''+dictdate["S"]+'''|'''+dictdate["P"]+'''|^|N|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''||1^''' + dictdate["P"] + '''||||''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|???|||||||||||||||||||||||||||||||||OBX|1|NM|ALT|????????????|'''+dictdate["ALT"]+'''|U/L|-|N|||F||16.019993|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|||0||OBX|2|NM|TP|?????|'''+dictdate["TP"]+'''|g/L|-|N|||F||80.947677|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|||0||','', 0, ''' + tenant + ''', '{}', null, '{}', null);'''.format(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")), str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
    elif dictdate["ALT"] != '0' and dictdate["TP"] == '0':
        sql = '''INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES ('MR-BS360s', 'MSH|^~\&|||||''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''||ORU^R01|''' + dictdate["P"] + '''|P|2.3.1||||0||ASCII|||PID|''' + dictdate["P"] + '''|||||||O|||||||||||||||||||||||OBR|''' + dictdate["P"] + '''|''' + dictdate["S"] + '''|''' + dictdate["P"] + '''|^|N|''' + time.strftime("%Y%m%d%H%M%S",time.localtime()) + '''|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''||1^''' + dictdate["P"] + '''||||''' + time.strftime("%Y%m%d%H%M%S",time.localtime()) + '''|???|||||||||||||||||||||||||||||||||OBX|1|NM|ALT|????????????|''' + dictdate["ALT"] + '''|U/L|-|N|||F||16.019993|''' + time.strftime("%Y%m%d%H%M%S",time.localtime()) + '''|||0||','', 0, ''' + tenant + ''', '{}', null, '{}', null);'''.format(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")), str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
    else:
        sql = '''INSERT INTO dbo.OriginalResult (EquipmentName, DataSource, DataFlag, Status, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId) VALUES ('MR-BS360s', 'MSH|^~\&|||||''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''||ORU^R01|''' + dictdate["P"] + '''|P|2.3.1||||0||ASCII|||PID|''' + dictdate["P"] + '''|||||||O|||||||||||||||||||||||OBR|''' + dictdate["P"] + '''|''' + dictdate["S"] + '''|''' + dictdate["P"] + '''|^|N|''' + time.strftime("%Y%m%d%H%M%S",time.localtime()) + '''|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''|''' + time.strftime("%Y%m%d%H%M%S", time.localtime()) + '''||1^''' + dictdate["P"] + '''||||''' + time.strftime("%Y%m%d%H%M%S",time.localtime()) + '''|???|||||||||||||||||||||||||||||||||OBX|2|NM|TP|?????|''' + dictdate["TP"] + '''|g/L|-|N|||F||80.947677|''' + time.strftime("%Y%m%d%H%M%S",time.localtime()) + '''|||0||','', 0, ''' + tenant + ''', '{}', null, '{}', null);'''.format(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")), str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
    return sql

def wl_OriginalResult(tenant, apihost, original):
    url = '{}/api/services/app/OriginalResult/TestJobBS360s?id={}'.format(apihost,original)
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
    r = requests.post(url, headers=headers)
    if r.json()['success']:
        log = '解析成功'
    else:
        log = r.json()['result']
    return log







