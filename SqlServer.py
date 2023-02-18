import pymssql


class MSSQL:
    def __init__(self, host, user, pwd, db):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.db = db

    def __GetConnect(self):
        if not self.db:
            raise (NameError, "没有设置数据库信息")
        self.conn = pymssql.connect(host=self.host, user=self.user, password=self.pwd, database=self.db, charset="utf8")
        cur = self.conn.cursor()
        if not cur:
            raise (NameError, "连接数据库失败")
        else:
            return cur

    def ExecQuery(self, sql):
        cur = self.__GetConnect()
        cur.execute(sql)
        resList = cur.fetchall()
        self.conn.close()
        return resList

    def ExecNonQuery(self, sql):
        cur = self.__GetConnect()
        try:
            cur.execute(sql)
        except Exception as e:
            log = "执行{}有错，错误是{}，需要回滚".format(sql, e)
            self.conn.rollback()
        #     增删改操作有误时回滚操作
        else:
            self.conn.commit()
            log = "success"
        self.conn.close()
        return log


def sqlselect(sql, host, user, pwd, db):
    ms = MSSQL(host=host, user=user, pwd=pwd, db=db)
    resList = ms.ExecQuery(sql)
    return resList

def sqlup(sql, host, user, pwd, db):
    ms = MSSQL(host=host, user=user, pwd=pwd, db=db)
    log = ms.ExecNonQuery(sql)
    return log

