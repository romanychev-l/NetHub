from flask import Flask, request, jsonify, make_response
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

@app.route('/home', methods=['GET'])
def get_home():
    try:
        # https://romanychev.online/nethub/home
        groups_data = db.groups.find({}, {'_id': False})
        groups = []
        for group in groups_data:
            groups.append(group)

        categories = {}
        for group in groups:
            categories[group['category']] = [group]

        return jsonify({'top': groups, 'categories': categories})
    except:
        return jsonify({'server': 'error'}), 400

@app.route('/category', methods=['GET'])
def get_category():
    try:
        # https://romanychev.online/nethub/category?id=3&amount=10
        category_id = int(request.args.get('id'))
        category_amount = int(request.args.get('amount'))
        groups_data = db.groups.find({'category': category_id }, {'_id': False}).limit(category_amount)
        category = []
        for group in groups_data:
            category.append(group)

        return jsonify(category)
    except:
        return jsonify({'server': 'error'}), 400

@app.route('/search', methods=['GET'])
def search():
    try:
        # https://romanychev.online/nethub/search?text=Кто
        text = request.args.get('text')
        groups_data = db.groups.find({'title': {'$regex': text}}, {'_id': False})
        category = []
        for group in groups_data:
            category.append(group)

        return jsonify(category)
    except:
        return jsonify({'server': 'error'}), 400

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port='7777',
        debug=True,
        threaded=True,
     )
