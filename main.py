import random
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QApplication

from Authenticate import tokenauth

from GetAllTenant import tenantlist
from IPConfig import getapihost
from SqlServer import sqlselect, sqlup
from hbanalysis import hblist, hbno, hbins
from infectioussql import findbill, wl_save
from shenghua import findlist, sampleresults, findbillno, baseinfo

from untitled import Ui_Form


class QmyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)  # 调用父类构造函数
        self.host = None  # 全局host
        self.api = None  # 全局api
        self.tenantid = None  # 全局租户id
        self.tenancyName = None  # 全局租户名
        self.user = None  # 全局用户Id
        self.sqlhost = None  # 全局数据库连接
        self.sqluser = None  # 全局数据库用户名
        self.sqlpwd = None  # 全局数据库密码
        self.sqldb = None  # 全局数据库库名
        self.token = None  # 全局登录token
        self.ac = None  # 全局登录AC
        self.tenantlist = []
        self.ui = Ui_Form()  # 创建UI对象
        self.ui.setupUi(self)  # 构造UI
        # 设置默认值
        self.ui.lineEdit.setText('http://192.168.1.112:1001')
        self.ui.pushButton_2.clicked.connect(self.pushButton_2)  # 获取租户信息
        self.ui.lineEdit_2.setText('mkpmadmin')
        self.ui.lineEdit_3.setText('Maike123!@#')
        self.ui.lineEdit_4.setText('192.168.1.197:49307')
        self.ui.lineEdit_6.setText('sa')
        self.ui.lineEdit_7.setText('maike123!@#+1s')
        database = ['JYXT20210608', 'JYXT20210608KF', 'JYXT20210608WG_TEMP', 'JYXT20210608WGKF', 'JYXT20210608WL',
            'JYXT20210608WLKF']
        for i in range(0, len(database)):
            self.ui.comboBox_2.addItem(database[i])

        # 添加点击事件
        self.ui.pushButton.clicked.connect(self.pushButton)
        self.ui.pushButton_6.clicked.connect(self.newrow)
        self.ui.pushButton_3.clicked.connect(self.shenghua)
        self.ui.pushButton_9.clicked.connect(self.joinshdata)
        self.ui.pushButton_10.clicked.connect(self.analysishb)
        self.ui.pushButton_7.clicked.connect(self.newhbtable)
        self.ui.pushButton_4.clicked.connect(self.inshb)
        self.ui.pushButton_11.clicked.connect(self.billnolist)
        self.ui.pushButton_8.clicked.connect(self.newinfectious)
        self.ui.pushButton_5.clicked.connect(self.insinfectious)

    def sqlsel(self, statement):  # 封装查询方法
        outcome = sqlselect(statement, self.sqlhost, self.sqluser, self.sqlpwd, self.sqldb)
        return outcome

    def sqlupdate(self, statement):  # 封装增删改数据库方法
        outcome = sqlup(statement, self.sqlhost, self.sqluser, self.sqlpwd, self.sqldb)
        return outcome

    def pushButton_2(self):  # 获取租户信息
        self.ui.comboBox.clear()  # 清除列表
        dns = self.ui.lineEdit.text()
        api = getapihost(dns)
        if len(api[1]) == 0:
            self.ui.textBrowser.append(api[0])
        else:
            self.ui.textBrowser.append(api[0])
            self.api = api[1]
            self.host = dns
            print(self.host, self.api)
            Tenant = tenantlist(self.host, self.api)
            for i in range(0, len(Tenant)):
                self.tenantlist.append([Tenant[i]['tenancyName'], str(Tenant[i]['id'])])
                self.ui.comboBox.addItem(Tenant[i]['tenancyName'], Tenant[i]['id'])

    def pushButton(self):  # 登录按钮
        userName = self.ui.lineEdit_2.text()
        password = self.ui.lineEdit_3.text()
        tenantname = self.ui.comboBox.currentText()

        for i in range(0, len(self.tenantlist)):
            if tenantname == self.tenantlist[i][0]:
                self.tenantid = self.tenantlist[i][1]

        to = tokenauth(self.host, self.api, userName, password, self.tenantid)
        self.ui.textBrowser.append(to[0])
        if len(to[1]) > 0:
            self.sqlhost = self.ui.lineEdit_4.text()
            self.sqluser = self.ui.lineEdit_6.text()
            self.sqlpwd = self.ui.lineEdit_7.text()
            self.sqldb = self.ui.comboBox_2.currentText()
            self.user = to[1]['userId']
            self.token = to[1]['accessToken']
            self.ac = to[1]['encryptedAccessToken']
            sql = "select TenancyName from AbpTenants where Id = {} and TenancyName = '{}'".format(str(self.tenantid), tenantname)

            tenancyName = self.sqlsel(sql)
            # 连接成功且登录成功后初始化面板
            if len(tenancyName) > 0:

                print(tenancyName)
                self.ui.textBrowser.append(
                    '{} {} 数据库连接成功'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.sqldb))
                if '丹霞' in tenancyName[0][0]:
                    self.danxia()
                else:
                    self.weilun()
                self.buildhbtable()
                self.infectious()
                self.ui.textBrowser.append(
                    '{} {} 解析初始化成功'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), tenantname))
                self.tenancyName = tenancyName[0][0]
            else:
                self.ui.tableWidget.clear()
                self.ui.textBrowser.append(
                    '{} {} 数据库连接失败'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.sqldb))
                self.ui.textBrowser.append('{} 解析初始化失败'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    def danxia(self):  # 初始化丹霞生化解析框架
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setRowCount(1)
        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setColumnHidden(4, True)
        self.ui.tableWidget.setHorizontalHeaderLabels(['排序号', '流水号', 'ALT', 'TP'])
        self.ui.tableWidget.setColumnWidth(0, 50)
        self.ui.tableWidget.setColumnWidth(1, 145)
        self.ui.tableWidget.setColumnWidth(2, 50)
        self.ui.tableWidget.setColumnWidth(3, 50)
        self.ui.tableWidget.setItem(0, 2, QtWidgets.QTableWidgetItem(format(random.uniform(10, 49), '.1f')))
        self.ui.tableWidget.setItem(0, 3, QtWidgets.QTableWidgetItem(format(random.uniform(45, 80), '.2f')))

    def weilun(self):  # 初始化卫伦生化解析框架
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setRowCount(1)
        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setColumnHidden(4, True)
        self.ui.tableWidget.setHorizontalHeaderLabels(['上机号', '流水号', 'ALT', 'TP'])
        self.ui.tableWidget.setColumnWidth(0, 50)
        self.ui.tableWidget.setColumnWidth(1, 145)
        self.ui.tableWidget.setColumnWidth(2, 50)
        self.ui.tableWidget.setColumnWidth(3, 50)
        self.ui.tableWidget.setItem(0, 2, QtWidgets.QTableWidgetItem(format(random.uniform(10, 49), '.1f')))
        self.ui.tableWidget.setItem(0, 3, QtWidgets.QTableWidgetItem(format(random.uniform(45, 80), '.2f')))

    def buildhbtable(self):  # 初始化HB解析面板
        self.ui.tableWidget_2.clear()
        self.ui.tableWidget_2.setRowCount(1)
        self.ui.tableWidget_2.setColumnCount(3)
        self.ui.tableWidget_2.setColumnHidden(2, True)
        self.ui.tableWidget_2.setHorizontalHeaderLabels(['流水号', 'HB'])
        self.ui.tableWidget_2.setColumnWidth(0, 150)
        self.ui.tableWidget_2.setColumnWidth(1, 50)
        self.ui.tableWidget_2.setItem(0, 1, QtWidgets.QTableWidgetItem(str(random.randint(110, 200))))

    def newrow(self):  # 生化通用行创建
        row_count = self.ui.tableWidget.rowCount()  # 返回当前行数
        self.ui.tableWidget.insertRow(row_count)  # 尾部插入一行
        self.ui.tableWidget.setItem(row_count, 2, QtWidgets.QTableWidgetItem(format(random.uniform(10, 49), '.1f')))
        self.ui.tableWidget.setItem(row_count, 3, QtWidgets.QTableWidgetItem(format(random.uniform(45, 80), '.2f')))

    def joinshdata(self):  # 创建生化数据
        # self.ui.tableWidget.clear()
        self.ui.tableWidget.setRowCount(1)
        shdata = findlist(self.tenantid, self.tenancyName)
        # print(shdata)
        try:
            date = self.sqlsel(shdata)
            if len(date) < 1:
                self.ui.textBrowser.append('{} 缺少可用数据'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            # print(date)
            for i in range(0, len(date)):
                # print(date[i])
                self.ui.tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(str(date[i][1])))
                self.ui.tableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(str(date[i][0].split('-', 2)[-1])))
                self.ui.tableWidget.setItem(i, 2, QtWidgets.QTableWidgetItem(format(random.uniform(10, 49), '.1f')))
                self.ui.tableWidget.setItem(i, 3, QtWidgets.QTableWidgetItem(format(random.uniform(50, 80), '.2f')))
                self.ui.tableWidget.setItem(i, 4, QtWidgets.QTableWidgetItem(str(date[i][0])))
                if i + 1 < len(date):
                    self.newrow()
        except:
            self.ui.textBrowser.append(
                '{} 缺少可用数据，请确认标本已接收/排序'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    def shenghua(self):  # 获取表单中的生化数据
        row_num = self.ui.tableWidget.rowCount()
        tabledate = []
        for i in range(0, row_num):
            if self.ui.tableWidget.item(i, 0) is not None and self.ui.tableWidget.item(i, 1) is not None:
                BillNo = self.ui.tableWidget.item(i, 1).text()
                try:
                    Code = self.ui.tableWidget.item(i, 4).text()
                except:
                    try:
                        No = findbillno(self.tenantid, BillNo)
                        # print(No)
                        BN = self.sqlsel(No)
                        if len(BN) > 0:
                            BillNo = BN[0][0].split('-', 2)[-1]
                            Code = BN[0][0]
                        else:
                            self.ui.textBrowser.append(
                                '{} 无法找到流水号为 {} 的标本'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                            BillNo))
                            break
                    except:
                        self.ui.textBrowser.append(
                            '{} 无法找到流水号为 {} 的标本'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), BillNo))
                        break
                tabledate.append({'BillNo': BillNo, 'PlateNo': self.ui.tableWidget.item(i, 0).text(), 'ALT': self.ui.tableWidget.item(i, 2).text(),
                                     'TP': self.ui.tableWidget.item(i, 3).text(), 'Code': Code})
            else:
                self.ui.textBrowser.append(
                    '{} 第 {} 行中出现空值，无法解析'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), i + 1))
        if len(tabledate) > 0:
            state = self.insertsql(self.tenantid, tabledate)
            if state == 1:
                if '丹霞' in self.tenancyName:
                    self.danxia()
                else:
                    self.weilun()

    def insertsql(self, tenant, date):  # 执行生化数据插入
        for i in range(0, len(date)):
            status = 0
            try:
                basesql = baseinfo(date[i])
                base = self.sqlsel(basesql)
                # print(base[0])
                sql = sampleresults(tenant, self.tenancyName, date[i], base[0])
                # print(sql)
                status = 0
                for ii in range(0, len(sql)):
                    r = self.sqlupdate(sql[ii])
                    if r == 'success':
                        self.ui.textBrowser.append(
                            '{} 流水号 {} 生化数据插入成功'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                        date[i]["BillNo"]))
                        status = 1
                    else:
                        self.ui.textBrowser.append(
                            '{} 执行流水号 {} 生化数据插入时出现错误 {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                                date[i]["BillNo"], r))
                        status = 0
                        break
            except:
                self.ui.textBrowser.append(
                    '{} 操作 {} 时发生未知错误'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), date[i]["BillNo"]))
        return status

    def newhbtable(self):  # HB增加行
        row_count = self.ui.tableWidget_2.rowCount()  # 返回当前行数
        self.ui.tableWidget_2.insertRow(row_count)  # 尾部插入一行
        self.ui.tableWidget_2.setItem(row_count, 1, QtWidgets.QTableWidgetItem(str(random.randint(110, 200))))

    def analysishb(self):  # 构造HB数据
        self.ui.tableWidget_2.setRowCount(1)
        hbsql = hblist(self.tenantid, self.tenancyName)
        try:
            hbdate = self.sqlsel(hbsql)
            if len(hbdate) < 1:
                self.ui.textBrowser.append('{} 缺少可用数据'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            for i in range(0, len(hbdate)):
                # print(date[i])
                self.ui.tableWidget_2.setItem(i, 0, QtWidgets.QTableWidgetItem(str(hbdate[i][0].split('-', 2)[-1])))
                self.ui.tableWidget_2.setItem(i, 1, QtWidgets.QTableWidgetItem(str(random.randint(110, 200))))
                self.ui.tableWidget_2.setItem(i, 2, QtWidgets.QTableWidgetItem(str(hbdate[i][0])))
                if i + 1 < len(hbdate):
                    self.newhbtable()
        except:
            self.ui.textBrowser.append('{} 发生未知错误'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    def inshb(self):  # 执行HB数据插入
        row_num = self.ui.tableWidget_2.rowCount()
        hbdate = []
        for i in range(0, row_num):
            if self.ui.tableWidget_2.item(i, 0) is not None:
                try:
                    billno = self.ui.tableWidget_2.item(i, 2).text()
                except:
                    bill = self.ui.tableWidget_2.item(i, 0).text()
                    try:
                        billsql = hbno(self.tenantid, bill)
                        billii = self.sqlsel(billsql)
                        billno = billii[0][0]
                    except:
                        self.ui.textBrowser.append(
                            '{} 无法找到流水号为 {} 的标本'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), bill))
                        break
                hbdate.append({'BillNo': billno, 'HB': self.ui.tableWidget_2.item(i, 1).text(),
                                  'Code': self.ui.tableWidget_2.item(i, 0).text()})
                hbinssql = hbins(self.tenantid, self.tenancyName, hbdate[i])
                r = self.sqlupdate(hbinssql)
                if r == 'success':
                    self.ui.textBrowser.append(
                        '{} 流水号 {} HB数据插入成功'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                    hbdate[i]["BillNo"].split('-', 2)[-1]))
                else:
                    self.ui.textBrowser.append(
                        '{} 执行流水号 {} HB数据插入时出现错误 {}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                                                            hbdate[i]["BillNo"].split('-', 2)[-1], r))
                    break
            else:
                self.ui.textBrowser.append(
                    '{} 第 {} 行中出现空值，无法解析'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), i + 1))
        self.buildhbtable()

    def infectious(self):  # 初始化传染4项面板
        self.ui.tableWidget_3.clear()
        self.ui.tableWidget_3.setRowCount(1)
        self.ui.tableWidget_3.setColumnCount(7)
        self.ui.tableWidget_3.setColumnHidden(0, True)
        self.ui.tableWidget_3.setHorizontalHeaderLabels(['Code', '孔位', '流水号', 'HBsAg', 'HCVAb', 'HIVAb', '梅毒'])
        self.ui.tableWidget_3.setColumnWidth(1, 80)
        self.ui.tableWidget_3.setColumnWidth(2, 145)
        self.ui.tableWidget_3.setColumnWidth(3, 50)
        self.ui.tableWidget_3.setColumnWidth(4, 50)
        self.ui.tableWidget_3.setColumnWidth(5, 50)
        self.ui.tableWidget_3.setColumnWidth(6, 50)
        self.ui.tableWidget_3.setItem(0, 3, QtWidgets.QTableWidgetItem('-'))
        self.ui.tableWidget_3.setItem(0, 4, QtWidgets.QTableWidgetItem('-'))
        self.ui.tableWidget_3.setItem(0, 5, QtWidgets.QTableWidgetItem('-'))
        self.ui.tableWidget_3.setItem(0, 6, QtWidgets.QTableWidgetItem('-'))

    def newinfectious(self):  # 传染病增加行
        row_count = self.ui.tableWidget_3.rowCount()  # 返回当前行数
        self.ui.tableWidget_3.insertRow(row_count)  # 尾部插入一行
        self.ui.tableWidget_3.setItem(row_count, 3, QtWidgets.QTableWidgetItem('-'))
        self.ui.tableWidget_3.setItem(row_count, 4, QtWidgets.QTableWidgetItem('-'))
        self.ui.tableWidget_3.setItem(row_count, 5, QtWidgets.QTableWidgetItem('-'))
        self.ui.tableWidget_3.setItem(row_count, 6, QtWidgets.QTableWidgetItem('-'))

    def billnolist(self):  # 传染数据生成
        self.ui.tableWidget_3.setRowCount(1)
        sql = findbill(self.tenantid)
        try:
            billlist = self.sqlsel(sql)

            row = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            col = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
            bi = 0
            for c in range(1, len(col)):
                for r in range(0, len(row)):
                    if bi < len(billlist):
                        self.ui.tableWidget_3.setItem(bi, 0, QtWidgets.QTableWidgetItem(str(billlist[bi][0])))
                        self.ui.tableWidget_3.setItem(bi, 1,
                                                      QtWidgets.QTableWidgetItem(str('{}{}'.format(row[r], col[c]))))
                        self.ui.tableWidget_3.setItem(bi, 2, QtWidgets.QTableWidgetItem(
                            str(billlist[bi][0].split('-', 2)[-1])))
                        if bi + 1 < len(billlist):
                            self.newinfectious()
                        bi += 1
            self.ui.textBrowser.append('{} 传染4项数据加载完成'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
        except:
            self.ui.textBrowser.append('{} 传染4项没有可用数据'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))

    def insinfectious(self):  # 传染解析
        row_num = self.ui.tableWidget_3.rowCount()
        infdate = []
        for i in range(0, row_num):
            if self.ui.tableWidget_3.item(i, 1) is not None and self.ui.tableWidget_3.item(i, 2) is not None:
                infdate.append({'BillNo': self.ui.tableWidget_3.item(i, 2).text(),
                                'PositionNo': self.ui.tableWidget_3.item(i, 1).text(),
                                'HBsAg': self.ui.tableWidget_3.item(i, 3).text(),
                                'HCVAb': self.ui.tableWidget_3.item(i, 4).text(),
                                'HIVAb': self.ui.tableWidget_3.item(i, 5).text(),
                                'TPAb': self.ui.tableWidget_3.item(i, 6).text()})
            else:
                self.ui.textBrowser.append('{} 第 {} 行中出现空值，无法解析'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), i + 1))
        if len(infdate) > 0:
            try:
                re = wl_save(self.host, self.api, self.tenantid, self.token, infdate)
                for ii in range(0, len(re)):
                    try:
                        self.sqlupdate(re[ii][2])
                        self.ui.textBrowser.append('{} {}项目解析完成'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), re[ii][0]))
                        self.infectious()
                    except:
                        self.ui.textBrowser.append('{} 在解析时发生未知错误'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
            except:
                self.ui.textBrowser.append('{} 在解析时发生未知错误'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))


if __name__ == "__main__":  # 用于当前窗体测试
    app = QApplication(sys.argv)  # 创建GUI应用程序
    form = QmyWidget()  # 创建窗体
    form.show()
    sys.exit(app.exec_())
