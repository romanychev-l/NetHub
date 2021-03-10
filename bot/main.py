import config
import messages
import requests
import base64
import json
import time
from time import sleep
import json
import pymongo
from pymongo import MongoClient
from multiprocessing import Process
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
import asyncio
from aiogram.utils.executor import start_webhook

from aiogram.utils.helper import Helper, HelperMode, ListItem

from aiogram.contrib.fsm_storage.memory import MemoryStorage
#from aiogram.contrib.middlewares.logging import LoggingMiddleware
import categories_module

# webhook settings
WEBHOOK_HOST = 'https://romanychev.online'
WEBHOOK_PATH = config.path
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '127.0.0.1'  # or ip
WEBAPP_PORT = config.port


mongo_pass = config.mongo_pass
mongo_db = config.mongo_db
link = ('mongodb+srv://{}:{}@cluster0-e2dix.mongodb.net/{}?retryWrites=true&'
        'w=majority')
link = link.format("Leonid", mongo_pass, mongo_db)

client = MongoClient(link, connect=False)
db = client[config.mongo_db_name]


bot = Bot(token=config.token)
dp = Dispatcher(bot, storage=MemoryStorage())
#dp.middleware.setup(LoggingMiddleware())


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    #logging.warning('Shutting down..')
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    #logging.warning('Bye!')


class TestStates(Helper):
    mode = HelperMode.snake_case

    TEST_STATE_0 = ListItem()
    TEST_STATE_1 = ListItem()
    TEST_STATE_2 = ListItem()
    TEST_STATE_3 = ListItem()
    TEST_STATE_4 = ListItem()

OK = '✅'
NOK = '❌'

async def base_categories_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    index = 100
    '''
    for category in categories_module.categories:
        word = list(category.keys())[0]
        but = types.InlineKeyboardButton(text=word, callback_data=str(index))
        keyboard.add(but)
        index += 100
    '''
    i = 0
    categories = categories_module.categories
    while i < len(categories):
        word = list(categories[i].keys())[0]
        but0 = types.InlineKeyboardButton(text=word, callback_data=str(index))
        index += 100
        i += 1

        if i < len(categories):
            word = list(categories[i].keys())[0]
            but1 = types.InlineKeyboardButton(text=word, callback_data=str(index))
            index += 100
            i += 1

            keyboard.row(but0, but1)
        else:
            keyboard.add(but0)


    but = types.InlineKeyboardButton(text='Завершить', callback_data='Завершить')
    keyboard.add(but)

    return keyboard

async def base_categories():
    result = []
    for category in categories_module.categories:
        d = {}
        d['name'] = list(category.keys())[0]
        d['subcategories'] = []
        for subcategory in list(category.values())[0]:
            d['subcategories'].append({'name': subcategory, 'status': 0})
        result.append(d)
    return result


async def check_chat(msg):
    chat_id = msg.chat.id
    if chat_id < 0:
        return False
    else:
        await bot.send_message(
            chat_id,
            'Добавьте бота в чат, чтобы использовать его'
        )
        return True


async def check_member(msg):
    admins = await bot.get_chat_administrators(msg.chat.id)
    for admin in admins:
        if admin['user']['id'] == msg['from']['id']:
            return False
    return True


async def get_admins(chat_id):
    result = []
    admins = await bot.get_chat_administrators(chat_id)
    for admin in admins:
        #print(admin)
        if admin['user']['is_bot'] == False:
            result.append(admin['user']['first_name'] + ' ' + admin['user']['last_name'])
    return result


async def get_participants(chat_id):
    admins = len(await get_admins(chat_id))
    members = await bot.get_chat_members_count(chat_id)
    if admins == None:
        admins = 0
    if members == None:
        members = 0
    return [admins, members]


async def get_keyboard(chat_id, index):
    keyboard = types.InlineKeyboardMarkup()
    if chat_id < 0:
        group = db.groups.find_one({'chat_id' : str(chat_id)})
        group_categories = group['category']
        obj = group_categories[index // 100 - 1]

        if index % 100 == 0:
            i = 1
            j = 0
            subcat = obj['subcategories']
            while j < len(subcat):
                text = subcat[j]['name']
                if subcat[j]['status']:
                    text = OK + ' ' + text
                else:
                    text = NOK + ' ' + text

                but0 = types.InlineKeyboardButton(
                    text=text,
                    callback_data=str(index + i)
                )
                i += 1
                j += 1

                if j < len(subcat):
                    text = subcat[j]['name']
                    if subcat[j]['status']:
                        text = OK + ' ' + text
                    else:
                        text = NOK + ' ' + text

                    but1 = types.InlineKeyboardButton(
                        text=text,
                        callback_data=str(index + i)
                    )
                    keyboard.row(but0, but1)
                    i += 1
                    j += 1
                else:
                    keyboard.add(but0)

        else:
            status = 0
            i = 1
            j = 0
            subcat = obj['subcategories']
            while j < len(subcat):
                text = subcat[j]['name']
                if index % 100 == i:
                    if subcat[j]['status']:
                        text = NOK + ' ' + text
                        status = 0
                    else:
                        text = OK + ' ' + text
                        status = 1
                else:
                    if subcat[j]['status']:
                        text = OK + ' ' + text
                    else:
                        text = NOK + ' ' + text

                but0 = types.InlineKeyboardButton(
                    text=text,
                    callback_data=str(index // 100 * 100 + i)
                )
                i += 1
                j += 1

                if j < len(subcat):
                    text = subcat[j]['name']
                    if index % 100 == i:
                        if subcat[j]['status']:
                            text = NOK + ' ' + text
                            status = 0
                        else:
                            text = OK + ' ' + text
                            status = 1
                    else:
                        if subcat[j]['status']:
                            text = OK + ' ' + text
                        else:
                            text = NOK + ' ' + text

                    but1 = types.InlineKeyboardButton(
                        text=text,
                        callback_data=str(index // 100 * 100 + i)
                    )
                    i += 1
                    j += 1

                    keyboard.row(but0, but1)
                else:
                    keyboard.add(but0)
            group_categories[index // 100 - 1]['subcategories'][index % 100 - 1]['status'] = status
            db.groups.update_one({'chat_id': str(chat_id)},
                                {"$set": {'category': group_categories,
                                          'category_id': index // 100 - 1}})

    but = types.InlineKeyboardButton(
        text='Назад',
        callback_data='Назад'
    )
    keyboard.add(but)

    but = types.InlineKeyboardButton(
        text='Завершить',
        callback_data='Завершить'
    )
    keyboard.add(but)

    return keyboard


@dp.callback_query_handler(lambda c:True)
async def inline(c):
    print('inline')
    chat_id = c.message.chat.id

    d = c.data
    #print(c)
    if d == 'Завершить':
        if chat_id < 0:
            state = dp.current_state(user=c.message.chat.id)
            await state.set_state(TestStates.all()[2])
            await bot.send_message(
                chat_id,
                messages.datetime
            )
        else:
            pass
    elif d == 'Назад':
        db.groups.update_one({'chat_id': str(chat_id)},
                            {"$set": {'category': await base_categories(),
                                      'category_id': -1}})

        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=c.message.message_id,
            reply_markup=await base_categories_keyboard()
        )
    else:
        await bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=c.message.message_id,
            reply_markup=await get_keyboard(chat_id, int(d))
        )


@dp.message_handler(state='*', commands=['start'])
async def start(msg):
    print('start')
    print(msg)
    chat_id = msg.chat.id
    if chat_id > 0:
        button = types.InlineKeyboardButton('Перейти в Хаб', url='https://nethub.club/#/')
        keyboard = types.InlineKeyboardMarkup().add(button)

        await bot.send_message(
            chat_id,
            messages.start_in_chat,
            reply_markup=keyboard
        )
    else:
        await bot.send_message(
            chat_id,
            messages.start_in_group
        )


@dp.message_handler(state='*', commands=['help'])
async def help(msg):
    print('help')
    await bot.send_message(
        msg.chat.id,
        messages.help_in_group
    )


async def delete_command(text):
    if text[0] == '/':
        text = text.split(' ', 1)
        if len(text) > 1:
            return text[1]

    return text


async def title(msg):
    text = await delete_command(msg.text)
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    answer = ''
    if voice == None:
        chat = await bot.get_chat(msg.chat.id)
        file_id = chat['photo']['big_file_id']
        file_ = await bot.get_file(file_id)
        file_path = file_.file_path

        with open(file_path, 'wb') as f:
            photo = await bot.download_file(file_path)
            f.write(photo.read())

        res = 0
        with open(file_path, 'rb') as f:
            url = "https://api.imgbb.com/1/upload"
            payload = {
                "key": '0fed957c70c9bd1193587969d205dd2b',
                "image": base64.b64encode(f.read()),
            }
            res = requests.post(url, payload).json()

        await bot.export_chat_invite_link(msg.chat.id)
        chat = await bot.get_chat(msg.chat.id)
        voice = {
            'chat_id': str(msg.chat.id),
            'title': text,
            'status': 'offline',
            'inviteLink': chat.invite_link,
            #'tags': [],
            'date': 0,
            'admins': await get_admins(msg.chat.id),
            'participants': await get_participants(msg.chat.id),
            'category': await base_categories(),#await base_categories(),
            'category_id': -1,
            'logo': res['data']['url'],
            'language_code': msg['from']['language_code']
        }
        db.groups.insert_one(voice)
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'title': text}}
        )


@dp.message_handler(state='*', commands=['change_title'])
async def change_title(msg):
    print('change_title')
    if await check_chat(msg) or await check_member(msg):
        return

    await title(msg)

    await bot.send_message(
        msg.chat.id,
        answer.change_title,
        #reply_markup=await base_categories()
    )

'''
@dp.message_handler(commands=['add_tags'])
async def add_tags(msg):
    print("add_tags")
    if await check_chat(msg) or await check_member(msg):
        return

    answer = ''
    text = await delete_command(msg.text)
    print(text)
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    if voice == None:
        answer = 'Создайте чат по командe /schedule_voice_chat'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'tags': text.split()}}
        )
        answer = 'Теги добавлены'

    await bot.send_message(
        msg.chat.id,
        answer
    )
'''
'''
@dp.message_handler(commands=['add_admins'])
async def add_admins(msg):
    print('add_admins')
    if await check_chat(msg) or await check_member(msg):
        return

    answer = ''
    text = await delete_command(msg.text)
    admins = text.split()
    admins.append(msg['from']['username'])
    admins = list(set(admins))
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    if voice == None:
        answer = 'Создайте чат по командe /schedule_voice_chat'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'admins': admins}}
        )
        answer = 'Админы добавлены'

    await bot.send_message(
        msg.chat.id,
        answer
    )
'''

@dp.message_handler(state='*', commands=['show_room'])
async def show_room(msg):
    print('show_room')
    if await check_chat(msg) or await check_member(msg):
        return

    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    if voice == None:
        answer = messages.room_is_none
    else:
        answer = (
            'Название:\n' + voice['title'] + '\n' +
            'Ссылка:\n' + voice['inviteLink']
        )

    await bot.send_message(
        msg.chat.id,
        answer
    )


@dp.message_handler(state='*', commands=['delete_room'])
async def delete_room(msg):
    print('delete_room')
    db.groups.delete_one({'chat_id': str(msg.chat.id)})
    await bot.send_message(
        msg.chat.id,
        'Комната удалена'
    )


async def change_state(msg, num):
    print('change_state')
    print(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(TestStates.all()[num])


@dp.message_handler(state='*', commands=['new_room'])
async def state_0(msg):
    print('new_room')
    if await check_chat(msg) or await check_member(msg):
        return

    db.groups.delete_one({'chat_id': str(msg.chat.id)})

    await bot.send_message(
        msg.chat.id,
        messages.new_room,
    )
    await change_state(msg, 1)


@dp.message_handler(state=TestStates.TEST_STATE_1)
async def state_1(msg):
    print('state_1')
    if await check_chat(msg) or await check_member(msg):
        return

    await title(msg)
    await bot.send_message(
        msg.chat.id,
        messages.title,
        reply_markup=await base_categories_keyboard()
    )
    await change_state(msg, 2)


@dp.message_handler(state=TestStates.TEST_STATE_2)
async def state_2(msg):
    print('state_2')
    if await check_chat(msg) or await check_member(msg):
        return

    datetime_object = datetime.strptime(msg.text, '%d %m %Y %H:%M')
    timestamp = datetime.timestamp(datetime_object) + 10800

    db.groups.update_one({'chat_id': str(msg.chat.id)},
                        {"$set": {'date': timestamp}})

    await bot.send_message(
        msg.chat.id,
        messages.complete
    )
    await change_state(msg, 0)


'''
@dp.message_handler(state=TestStates.TEST_STATE_2)
async def state_2(msg):
    if await check_chat(msg) or await check_member(msg):
        return

    await add_tags(msg)
    await change_state(msg, 0)
'''
'''
@dp.message_handler(state=TestStates.TEST_STATE_4)
async def state_4(msg):
    if await check_chat(msg) or await check_member(msg):
        return

    await add_admins(msg)
    await change_state(msg, 0)
'''


@dp.message_handler(state='*', content_types=['voice_chat_started'])
async def voice_chat_started(msg):
    print(msg)
    print('voice_chat_started')


@dp.message_handler(state='*', content_types=['voice_chat_started'])
async def main_logic(msg):
    print('main_logic')
    if msg.text == 'Voice Chat started':
        voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
        if voice != None:
            db.groups.update_one(
                {'chat_id': str(msg.chat.id)},
                {"$set": {'status': 'online'}}
            )
    elif msg.text == 'Voice Chat ended':

        '''
        voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
        if voice != None:
            db.groups.update_one(
                {'chat_id': str(msg.chat.id)},
                {"$set": {'status': 'offline'}}
            )
        '''
    else:
        print('text in group')
        #update admins and users
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set":
                {'admins': await get_admins(msg.chat.id),
                'participants': await get_participants(msg.chat.id)}
            }
        )


def main():
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )


if __name__ == '__main__':
    main()
