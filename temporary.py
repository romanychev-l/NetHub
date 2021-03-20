from pymongo import MongoClient
import sys
import time
sys.path.insert(1, 'bot')

import config
import func


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


def update_home():
    while True:
        print('update_home')
        try:
            n = 13
            groups_data = db.groups.find({}, {'_id' : 0}).sort('members', -1).limit(10)
            groups = list(map(func.correct_view, groups_data))
            categories = [[] for i in range(n)]

            for i in range(n):
                groups_data = list(db.groups.find(
                    {'category_id': i}, {'_id' : 0}
                ).sort('members', -1).limit(3))
                categories[i].extend(list(map(func.correct_view, groups_data)))

            obj = db.temporary.find_one({'name': 'home'})
            post = {'name': 'home', 'top': groups,
                    'categories': categories}
            if obj == None:
                db.temporary.insert_one(post)
            else:
                db.temporary.update_one({'name': 'home'}, {'$set': post})
        except Exception as e:
            print('Error update_home')
            print(e)

        time.sleep(5)


if __name__ == '__main__':
    update_home()
