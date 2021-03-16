from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient
import sys
import asyncio
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, 'bot')

import config


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
client = MongoClient('localhost', 27017)
db = client[config.mongo_db_name]


def correct_view(obj):
    res = {}
    res['id'] = obj['chat_id']
    res['title'] = obj['title']
    res['admins'] = obj['admins']
    res['members'] = obj['members']
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
            {'category_id': category_id}
        ).sort('members', -1).limit(category_amount)

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


async def main():
    try:
        app.run(
            host='127.0.0.1',
            port=config.server_port,
            debug=True,
            threaded=True,
        )
    except:
        print('Error main')


async def update_home():
    while True:
        try:
            n = 13
            groups_data = db.groups.find({}, {'_id' : 0}).sort('members', -1).limit(10)
            groups = list(map(correct_view, groups_data))
            categories = [[] for i in range(n)]

            for i in range(n):
                groups_data = list(db.groups.find(
                    {'category_id': i}, {'_id' : 0}
                ).sort('members', -1).limit(3))
                categories[i].extend(list(map(correct_view, groups_data)))

            obj = db.temporary.find_one({'name': 'home'})
            post = {'name': 'home', 'top': groups,
                    'categories': categories}
            if obj == None:
                db.temporary.insert_one(post)
            else:
                db.temporary.update_one({'name': 'home'}, post)
        except:
            print('Error update_home')

        await asyncio.sleep(5)


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.create_task(main()),
            loop.create_task(update_home())
        ]
        wait_tasks = asyncio.wait(tasks)
        loop.run_until_complete(wait_tasks)
        loop.close()

    except Exception as e:
        print(e)
