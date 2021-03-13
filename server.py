from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, 'bot')

import config


app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

mongo_pass = config.mongo_pass
mongo_db = config.mongo_db
link = ('mongodb+srv://{}:{}@cluster0-e2dix.mongodb.net/{}?retryWrites=true&'
        'w=majority')
link = link.format("Leonid", mongo_pass, mongo_db)

client = MongoClient(link, connect=False)
db = client[config.mongo_db_name]

def correct_view(obj):
    res = {}
    res['id'] = obj['chat_id']
    res['title'] = obj['title']
    res['admins'] = obj['admins']
    res['participants'] = obj['participants']
    res['inviteLink'] = obj['inviteLink']
    res['logo'] = obj['logo']

    status = obj['status']
    res['status'] = status
    if status == 'offline':
        print(obj['date'])
        res['date'] = (obj['date'] - 3600)* 1000

    res['subcategories'] = obj['subcategories']
    category_id = obj['category_id']
    res['category_id'] = category_id

    return res


@app.route('/home', methods=['GET'])
def get_home():
    try:
        n = 13
        # https://romanychev.online/nethub/home
        #groups_data = db.groups.find({}, {'_id': False})
        groups_data = db.groups.find({}).sort('participants.1', -1)
        groups = []
        for group in groups_data:
            groups.append(correct_view(group))

        categories = [[] for i in range(n)]

        for i in range(n):
            groups_data = db.groups.find(
                {'category_id': i}
            ).sort('participants.1', -1)
            j = 0
            for obj in groups_data:
                categories[i].append(correct_view(obj))
                j += 1
                if j == 3:
                    break

        return jsonify({'top': groups, 'categories': categories})
    except:
        return jsonify({'server': 'error'}), 400


@app.route('/category', methods=['GET'])
def get_category():
    try:
        # https://romanychev.online/nethub/category?id=3&amount=10
        category_id = int(request.args.get('id'))
        category_amount = int(request.args.get('amount'))
        groups_data = db.groups.find(
            {'category_id': category_id}
        ).limit(category_amount)

        category = []
        for obj in groups_data:
            category.append(correct_view(obj))

        return jsonify(category)
    except:
        return jsonify({'server': 'error'}), 400


@app.route('/room', methods=['GET'])
def get_room():
    try:
        room_id = request.args.get('id')
        room = db.groups.find_one({'chat_id': room_id})

        return jsonify(correct_view(room))
    except:
        return jsonify({'server': 'error'}), 400


@app.route('/search', methods=['GET'])
def search():
    try:
        # https://romanychev.online/nethub/search?text=Кто
        text = request.args.get('text').lower()
        groups_data = db.groups.find(
            {'title': {'$regex': text, '$options':'$i'}}
        )

        res = []
        for obj in groups_data:
            res.append(correct_view(obj))

        return jsonify(res)
    except:
        return jsonify({'server': 'error'}), 400


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=config.server_port,
        debug=True,
        threaded=True,
    )
