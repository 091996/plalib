

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
        sql = '''select distinct a.BillNo, iif(b.PlateNo is null, iif(c.m is null ,0,c.m) + ROW_NUMBER() OVER (ORDER BY (SELECT 1)), b.PlateNo) row
                from (select a.BillNo
                      from Specimen a
                               join TestItem b on 1 = 1 and b.Type in (1, 2)
                               left join SampleResults c on c.SpecimenBillNo = a.BillNo and b.Id = c.TestItemId and c.BillStatus = 3
                      where (b.Name like '%TP%' or b.Name like '%ALT%')
                        and a.TenantId = {}
                        and b.TenantId = {}
                        and datediff(day, a.CreationTime, getdate()) = 0 and c.Id is null
                      group by a.BillNo) a
                         left join SampleResults b on a.BillNo = b.SpecimenBillNo and b.BillStatus = 3
                         outer apply (select max(SampleResults.PlateNo) m from SampleResults where datediff(day, CreationTime, getdate()) = 0 and BillStatus = 3) c
                order by row'''.format(tenant, tenant)
    else:
        sql = '''select a.BillNo, ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS row
                from (select a.BillNo
                      from Specimen a
                               join TestItem b on 1 = 1 and b.Type in (1, 2)
                               left join SampleResults c on c.SpecimenBillNo = a.BillNo and b.Id = c.TestItemId and c.BillStatus = 3
                      where (b.Code like '%TP%' or b.Code like '%ALT%')
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
    sql = "select BillNo,SampleTestType,Gender,IsAnticoagulant,PlasmaType from Specimen where BillNo = '{}'".format(date['Code'])
    return sql


def sampleresults(tenant, tenancyName, date, base):
    SampleTestType = base[1]
    IsAnticoagulant = base[3]
    print(type(SampleTestType), type(IsAnticoagulant), type(float(date['TP'])))
    print(SampleTestType, IsAnticoagulant, float(date['TP']))

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
        altsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['ALT'] + "', '" + altResults + "', '" + date['ALT'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Code like '%ALT%' and Type = 1), null, 3, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
        tpsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['TP'] + "', '" + tpResults + "', '" + date['TP'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Code like '%TP%' and Type = 2), null, 3, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
    else:
        altsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['ALT'] + "', '" + altResults + "', '" + date['ALT'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Name like '%ALT%' and Type = 1), null, 0, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
        tpsql = "INSERT INTO dbo.SampleResults (SpecimenBillNo, OriginalResults, Results, Proportion, TestItemId, OriginalResultId, BillStatus, SamplePlateNumber, ManualNumber, TenantId, CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId, AuditTime, IsTempResult) VALUES ( '" + date['Code'] + "', '" + date['TP'] + "', '" + tpResults + "', '" + date['TP'] + "', (select top 1 Id from TestItem where TenantId = " + tenant + " and Name like '%TP%' and Type = 2), null, 0, null, null, " + tenant + ", getdate(), null, getdate(), null, null, 0);"
    return altsql, tpsql

def findbillno(tenant, billno):
    sql = "select BillNo from Specimen where Code = '{}' and TenantId = {}".format(billno, tenant)
    return sql



