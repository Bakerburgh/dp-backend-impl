from connexion import App, Api
from flask import g

# keyFile = os.path.join('..', '..', '..', 'keys.json')
# if os.path.exists(keyFile):
#     with open(keyFile, 'r') as json_file:
#         keys = json.load(json_file)
#     app.app.config['MYSQL_DATABASE_USER'] = keys['db']['user']
#     app.app.config['MYSQL_DATABASE_PASSWORD'] = keys['db']['pass']
#     app.app.config['MYSQL_DATABASE_DB'] = keys['db']['db']
#     app.app.config['MYSQL_DATABASE_HOST'] = 'localhost'
#     mysql = MySQL()
#     mysql.init_app(app.app)
#     db.init(mysql)
# else:
#     print("WARNING: No key file found")


def _save_paths(api: Api):
    if 'paths' not in g:
        g.paths = {
            'base_path': api.base_path
        }


def init_hook(app: App, api: Api):
    print("Custom initialization...")
    _save_paths(api)

    return
