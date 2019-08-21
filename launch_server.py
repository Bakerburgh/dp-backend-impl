from git import Repo, RemoteProgress
import os
import sys
from openapi_server.__main__ import main


class MyProgressPrinter(RemoteProgress):

    def update(self, op_code, cur_count, max_count=None, message=''):
        progress = 100.0 * cur_count / (max_count or 100.0)
        msg = message or ''
        print('%3.1f %s\r' % (progress, msg))
        # print(op_code, cur_count, max_count, cur_count / (max_count or 100.0), message or "NO MESSAGE")


self_dir = os.path.dirname(__file__)
gen_dir = os.path.join(self_dir, '..', 'backend-base')

repo = Repo(gen_dir)
if repo.is_dirty():
    print('You have uncommitted changes in the backend-base folder, skipping update of generated code...')
else:
    print('Updating generated code...')
    repo.remote().pull(progress=MyProgressPrinter())

if not 'PROJECT_DIR' in os.environ.keys():
    default = os.path.join(os.getcwd(), '..', 'projects')
    if not os.path.exists(default):
        print('PROJECT_DIR not set, and the default location does not exist.')
        sys.exit(2)
    else:
        print('PROJECT_DIR not set, assuming default (%s)' % default)
        os.environ['PROJECT_DIR'] = default

print('Starting server....')
main()