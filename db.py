from flaskext.mysql import MySQL

from openapi_server.models import ProjectBrief

mysql = None


def init(sqlInstance: MySQL):
    global mysql
    mysql = sqlInstance


class Database:
    def __init__(self):
        self.con = mysql.connect()
        self.cur = self.con.cursor()

    def projectList(self):
        self.cur.execute("SELECT tag, name, last_modified FROM project")
        ret = []
        for row in self.cur:
            print(row)
            ret.append(ProjectBrief(*row))

        self.con.close()
        return ret

    def tagAvailable(self, tag):
        self.cur.execute("SELECT EXISTS(SELECT 1 FROM project WHERE tag = %s)", tag)
        result = self.cur.fetchone()
        return result[0] == 1
