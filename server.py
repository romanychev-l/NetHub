from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient
import sys
import asyncio
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, 'bot')

import config
import func


app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}})

'''
mongo_pass = config.mongo_pass
mongo_db = config.mongo_db
link = ('mongodb+srv://{}:{}@cluster0-e2dix.mongodb.net/{}?retryWrites=true&'
        'w=majority')
link = link.format("Leonid", mongo_pass, mongo_db)

client = MongoClient(link, connect=False)
db = client[config.mongo_db_name]
'''
#client = MongoClient('localhost', 27017)
client = MongoClient('mongodb://admin:Factor_9@localhost:27017')
db = client[config.mongo_db_name]


@app.route('/home', methods=['GET'])
def get_home():
    try:
        res = db.temporary.find_one({'name': 'home'}, {'_id': 0, 'name': 0})
        return jsonify(res)
    except:
        return jsonify({'server': 'error'}), 400


@app.route('/category', methods=['GET'])
def get_category():
    try:
        # https://romanychev.online/nethub/category?id=3&amount=10
        category_id = int(request.args.get('id'))
        category_amount = int(request.args.get('amount'))
        groups_data = db.groups.find(
            {'category_id': category_id, 'created': 1}
        ).sort('members', -1).limit(category_amount)

        category = []
        for obj in groups_data:
            category.append(func.correct_view(obj))

        return jsonify(category)
    except:
        return jsonify({'server': 'error'}), 400


@app.route('/room', methods=['GET'])
def get_room():
    try:
        room_id = request.args.get('id')
        room = db.groups.find_one({'chat_id': room_id, 'created': 1})

        return jsonify(func.correct_view(room))
    except:
        return jsonify({'server': 'error'}), 400


@app.route('/search', methods=['GET'])
def search():
    try:
        # https://romanychev.online/nethub/search?text=Кто
        text = request.args.get('text').lower()
        groups_data = db.groups.find(
            {'title': {'$regex': text, '$options':'$i'}, 'created': 1}
        )

        res = []
        for obj in groups_data:
            res.append(func.correct_view(obj))

        return jsonify(res)
    except:
        return jsonify({'server': 'error'}), 400


def main():
    while True:
        try:
            app.run(
                host='127.0.0.1',
                port=config.server_port,
                debug=True,
                threaded=True,
            )
        except Exception as e:
            print('Error main')
            print(e)

if __name__ == '__main__':
    main()
