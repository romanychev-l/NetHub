from flask import Flask
from pymongo import MongoClient

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, 'bot')

import config

app = Flask(__name__)


mongo_pass = config.mongo_pass
mongo_db = config.mongo_db
link = ('mongodb+srv://{}:{}@cluster0-e2dix.mongodb.net/{}?retryWrites=true&'
        'w=majority')
link = link.format("Leonid", mongo_pass, mongo_db)

client = MongoClient(link, connect=False)
db = client[config.mongo_db_name]


@app.route('/rooms', methods=['GET'])
def get_rooms():
    '''
    users_ids = []
    users = db.groups.find()
    for user in users:
        users_ids.append(int(user['vk_id']))
    '''

    return "hello"


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port='7777',
        debug=True,
        threaded=True,
     )
