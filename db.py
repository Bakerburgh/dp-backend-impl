from flaskext.mysql import MySQL

from openapi_server.models import ProjectBrief, ProjectDetails

mysql = None


def init(sqlInstance: MySQL):
    global mysql
    mysql = sqlInstance


class Database:
    """
    A wrapper for accessing the database. This generaly contains only MySQL queries, but occasionally some error
    handling is also appropriate. If the return value is something that can be passed back to flask/connexion, then the
    method name starts with an 'h'. (As in, ready to be sent back over http(s))
    """
    def __init__(self):
        self.con = mysql.connect()
        self.cur = self.con.cursor()

    def hProjectList(self):
        self.cur.execute("SELECT tag, name, last_modified FROM project")
        ret = []
        for row in self.cur:
            print(row)
            ret.append(ProjectBrief(*row))

        self.con.close()
        return ret

    def hProjectDetails(self, tag):
        rows = self.cur.execute("SELECT tag, name, last_modified, description, api_spec_url FROM project WHERE tag = %s", tag)
        if rows == 0:
            return 'Not Found', 404

        data = self.cur.fetchone()
        return ProjectDetails(*data)

    def tagAvailable(self, tag):
        self.cur.execute("SELECT EXISTS(SELECT 1 FROM project WHERE tag = %s)", tag)
        result = self.cur.fetchone()
        return result[0] == 1
