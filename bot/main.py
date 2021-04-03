import config
import messages
import texts
import requests
import base64
import json
import time
from time import sleep
import json
import pymongo
from pymongo import MongoClient
from multiprocessing import Process
#from datetime import datetime, timedelta, date
import datetime
from contextlib import suppress

from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import text, bold, italic, code, pre
import asyncio
from aiogram.utils.executor import start_webhook
from aiogram.utils.exceptions import MessageNotModified

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

bot = Bot(token=config.token)
dp = Dispatcher(bot, storage=MemoryStorage())


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
    TEST_STATE_5 = ListItem()
    TEST_STATE_6 = ListItem()
    TEST_STATE_7 = ListItem()
    TEST_STATE_8 = ListItem()

OK = '✅'
NOK = '❌'

days = ['1_day', '2_day', '3_day', '4_day', '5_day', '6_day', '7_day']

async def get_msg(msg, text):
    chat_id = str(msg.chat.id)
    if int(chat_id) < 0:
        chat_id = str(msg['from']['id'])

    user = db.users.find_one({'chat_id': chat_id})

    code = 'en'
    if user != None:
        code = user['language_code']

    if code == 'ru':
        return messages.messages['ru'][text]
    else:
        return messages.messages['en'][text]


async def get_text(msg, o, t):
    # o - first var, t - second var
    chat_id = str(msg.chat.id)
    if int(chat_id) < 0:
        chat_id = str(msg['from']['id'])

    user = db.users.find_one({'chat_id': chat_id})

    code = 'en'
    if user != None:
        code = user['language_code']

    if code == 'ru':
        return texts.text[o]['ru'][t]
    else:
        return texts.text[o]['en'][t]


async def get_cat(msg):
    print('get_cat')
    chat_id = str(msg.chat.id)
    if int(chat_id) < 0:
        chat_id = str(msg['from']['id'])

    user = db.users.find_one({'chat_id': chat_id})

    code = 'en'
    if user != None:
        code = user['language_code']

    if code == 'ru':
        return categories_module.categories_ru
    else:
        return categories_module.categories


async def get_chat_id(user_id):
    chat_id = str(db.active_group.find_one({'user_id': user_id})['chat_id'])
    return chat_id


async def onetime_keyboard(msg):
    but0 = types.KeyboardButton(await get_text(msg, 'buttons', 'to_hub'))
    #but1 = types.KeyboardButton(await get_text(msg, 'buttons',
    #    'create_room_in_group'))
    but2 = types.KeyboardButton(await get_text(msg, 'buttons',
        'create_room_in_channel'))
    but3 = types.KeyboardButton(await get_text(msg, 'buttons', 'settings'))

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
        one_time_keyboard=True).add(but0).add(but2).add(but3)
    return keyboard


async def everytime_keyboard(msg):
    but0 = types.KeyboardButton(await get_text(msg, 'buttons', 'to_hub'))
    #but1 = types.KeyboardButton(await get_text(msg, 'buttons',
    #    'create_room_in_group'))
    but2 = types.KeyboardButton(await get_text(msg, 'buttons',
        'create_room_in_channel'))
    but3 = types.KeyboardButton(await get_text(msg, 'buttons', 'settings'))

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
        but0).add(but2).add(but3)
    return keyboard


async def base_categories_keyboard(msg):
    keyboard = types.InlineKeyboardMarkup()
    index = 100
    i = 0
    categories = await get_cat(msg)
    while i < len(categories):
        word = list(categories[i].keys())[0]
        but0 = types.InlineKeyboardButton(text=word, callback_data=str(index))
        index += 100
        i += 1

        if i < len(categories):
            word = list(categories[i].keys())[0]
            but1 = types.InlineKeyboardButton(
                text=word, callback_data=str(index))
            index += 100
            i += 1

            keyboard.row(but0, but1)
        else:
            keyboard.add(but0)

    but = types.InlineKeyboardButton(
        text=await get_text(msg, 'buttons', 'complete'),
        callback_data='Завершить'
    )
    keyboard.add(but)

    return keyboard


async def change_state(msg, num):
    print('change_state' + str(num))
    if msg['from']['id'] == config.bot_id:
        state = dp.current_state(chat=msg['chat']['id'])
        #print(msg['chat']['id'])
    else:
        state = dp.current_state(chat=msg['from']['id'])
        #print(msg['from']['id'])
    await state.set_state(TestStates.all()[num])


async def check_chat(msg):
    chat_id = msg.chat.id
    if chat_id > 0:
        return False
    else:
        return True


async def check_member(msg):
    admins = await bot.get_chat_administrators(msg.chat.id)
    for admin in admins:
        if admin['user']['id'] == msg['from']['id']:
            return False

    await bot.send_message(
        msg.chat.id,
        await get_msg(msg, 'check_member')
    )

    return True


async def get_admins(chat_id):
    result = []
    admins = await bot.get_chat_administrators(chat_id)
    for admin in admins:
        if admin['user']['is_bot'] == False:
            full_name = admin['user']['first_name']
            if 'last_name' in admin['user']:
                 full_name += ' ' + admin['user']['last_name']
            result.append(full_name)
    return result


async def check_bot_privilege(msg):
    admins = await bot.get_chat_administrators(msg.chat.id)
    for admin in admins:
        if admin['user']['id'] == config.bot_id:
            if (admin['status'] == 'administrator' and
                admin['can_invite_users'] == True and
                admin['can_pin_messages'] == True):
                return False
            break

    await bot.send_message(
        msg['from']['id'],
        await get_msg(msg, 'check_bot_privilege')
    )

    return True


async def check_member_channel(msg):
    admins = await bot.get_chat_administrators(msg.forward_from_chat.id)
    for admin in admins:
        if admin['user']['id'] == msg['from']['id']:
            return False

    await bot.send_message(
        msg['from']['id'],
        await get_msg(msg, 'check_member')
    )

    return True


async def check_bot_privilege_channel(msg):
    admins = await bot.get_chat_administrators(msg.forward_from_chat.id)
    for admin in admins:
        if admin['user']['id'] == bot.id:
            if (admin['status'] == 'administrator' and
                admin['can_invite_users'] == True and
                admin['can_post_messages'] == True):
                return False
            break

    await bot.send_message(
        msg['from']['id'],
        await get_msg(msg, 'check_bot_privilege_channel')
    )

    return True


async def check_active_group(msg, chat_id, user_id):
    group = db.active_group.find_one({'chat_id': chat_id})
    if group == None or group['user_id'] == user_id:
        return False

    if msg.forward_from_chat != None:
        chat_id = user_id

    await bot.send_message(
        chat_id,
        await get_msg(msg, 'check_active_group')
    )
    return True

async def get_members(chat_id):
    members = await bot.get_chat_members_count(chat_id)
    if members == None:
        members = 0
    return members


async def change_language(msg):
    code = 'en'
    if msg.text == 'Русский':
        code = 'ru'
    db.users.update_one({'chat_id': str(msg.chat.id)},
        {'$set' : {'language_code': code}})


async def language_keyboard():
    but1 = types.KeyboardButton('English')
    but2 = types.KeyboardButton('Русский')
    return types.ReplyKeyboardMarkup(resize_keyboard=True,
        ).add(but1).add(but2)


async def get_keyboard(msg, index):
    user_id = str(msg.chat.id)
    chat_id = await get_chat_id(user_id)
    keyboard = types.InlineKeyboardMarkup()
    if int(chat_id) < 0:
        group = db.groups.find_one({'chat_id' : chat_id})
        group_categories = group['subcategories']
        categories = await get_cat(msg)
        subcat = list(categories[index // 100 - 1].values())[0]
        if index % 100 == 0:
            i = 1
            j = 0
            while j < len(subcat):
                but0 = types.InlineKeyboardButton(
                    text=NOK + ' ' + subcat[j],
                    callback_data=str(index + i)
                )
                i += 1
                j += 1

                if j < len(subcat):
                    but1 = types.InlineKeyboardButton(
                        text=NOK + ' ' + subcat[j],
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
            while j < len(subcat):
                text = subcat[j]
                if index % 100 == i:
                    if subcat[j] in group_categories:
                        text = NOK + ' ' + text
                        status = 0
                        group_categories.remove(subcat[j])
                    else:
                        text = OK + ' ' + text
                        status = 1
                        group_categories.append(subcat[j])
                else:
                    if subcat[j] in group_categories:
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
                    text = subcat[j]
                    if index % 100 == i:
                        if subcat[j] in group_categories:
                            text = NOK + ' ' + text
                            status = 0
                            group_categories.remove(subcat[j])
                        else:
                            text = OK + ' ' + text
                            status = 1
                            group_categories.append(subcat[j])
                    else:
                        if subcat[j] in group_categories:
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
            db.groups.update_one({'chat_id': chat_id},
                                {"$set": {'subcategories': group_categories,
                                          'category_id': index // 100 - 1}})

    but = types.InlineKeyboardButton(
        text=await get_text(msg, 'buttons', 'back'),
        callback_data='Назад'
    )
    keyboard.add(but)

    but = types.InlineKeyboardButton(
        text=await get_text(msg, 'buttons', 'complete'),
        callback_data='Завершить'
    )
    keyboard.add(but)

    return keyboard


async def get_keyboard_reg(msg, index):
    user_id = str(msg.chat.id)
    keyboard = types.InlineKeyboardMarkup()
    if int(user_id) > 0:
        group = db.users.find_one({'chat_id' : user_id})
        group_categories = group['subcategories']
        index_cat = index // 100 - 1
        categories = await get_cat(msg)
        subcat = list(categories[index_cat].values())[0]

        if index % 100 == 0:
            i = 1
            j = 0
            while j < len(subcat):
                status = 1
                ok = 0
                if subcat[j] in group_categories[index_cat]:
                    ok = OK
                else:
                    ok = NOK
                but0 = types.InlineKeyboardButton(
                    text=ok + ' ' + subcat[j],
                    callback_data=str(index + i)
                )
                i += 1
                j += 1

                if j < len(subcat):
                    status = 1
                    if subcat[j] in group_categories[index_cat]:
                        ok = OK
                    else:
                        ok = NOK
                    but1 = types.InlineKeyboardButton(
                        text=ok + ' ' + subcat[j],
                        callback_data=str(index + i)
                    )
                    keyboard.row(but0, but1)
                    i += 1
                    j += 1
                else:
                    keyboard.add(but0)

        else:
            status = 0
            index_cat = index // 100 - 1
            i = 1
            j = 0
            while j < len(subcat):
                text = subcat[j]
                if index % 100 == i:
                    if subcat[j] in group_categories[index_cat]:
                        text = NOK + ' ' + text
                        status = 0
                        group_categories[index_cat].remove(subcat[j])
                    else:
                        text = OK + ' ' + text
                        status = 1
                        group_categories[index_cat].append(subcat[j])
                else:
                    if subcat[j] in group_categories[index_cat]:
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
                    text = subcat[j]
                    if index % 100 == i:
                        if subcat[j] in group_categories[index_cat]:
                            text = NOK + ' ' + text
                            status = 0
                            group_categories[index_cat].remove(subcat[j])
                        else:
                            text = OK + ' ' + text
                            status = 1
                            group_categories[index_cat].append(subcat[j])
                    else:
                        if subcat[j] in group_categories[index_cat]:
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
            db.users.update_one({'chat_id': user_id},
                                {"$set": {'subcategories': group_categories}})

    but = types.InlineKeyboardButton(
        text=await get_text(msg, 'buttons', 'back'),
        callback_data='Назад'
    )
    keyboard.add(but)

    but = types.InlineKeyboardButton(
        text=await get_text(msg, 'buttons', 'complete'),
        callback_data='Завершить'
    )
    keyboard.add(but)

    return keyboard


@dp.callback_query_handler(lambda c: c.data in days, state=TestStates.TEST_STATE_3)
async def date_inline(c):
    print('date_inline')
    user_id = str(c.message.chat.id)
    chat_id = await get_chat_id(user_id)

    msg = c.message

    d = c.data
    dt = datetime.datetime.now() + datetime.timedelta(hours=3)
    dt = dt.replace(hour=0, minute=0, second=0)

    for day in days:
        if d == day:
            break
        dt += datetime.timedelta(days=1)

    timestamp = int(datetime.datetime.timestamp(dt)) - 3 * 60 * 60

    db.groups.update_one({'chat_id': chat_id},
                        {"$set": {'date': timestamp}})

    with suppress(MessageNotModified):
        await bot.edit_message_reply_markup(
            user_id,
            message_id=c.message.message_id
        )

    await bot.send_message(user_id, await get_msg(msg, 'time'))
    await change_state(c, 4)


async def get_data_str(msg, data):
    data = data.split()
    day = data[0]
    month = data[1]
    month = await get_text(msg, 'month', month)

    result = day + ' ' + month
    if len(data) == 3:
        result += ' ' + data[2]

    return result


@dp.callback_query_handler(lambda c:True, state=TestStates.TEST_STATE_2)
async def inline(c):
    print('inline')
    user_id = str(c.message.chat.id)
    chat_id = await get_chat_id(user_id)
    msg = c.message

    d = c.data
    if d == 'Завершить':
        with suppress(MessageNotModified):
            await bot.edit_message_reply_markup(
                user_id,
                message_id=c.message.message_id
            )
        group = db.groups.find_one({'chat_id': chat_id})
        list_categories = ''
        if group['category_id'] != 13:
            categories = await get_cat(msg)
            list_categories = list(
                categories[group['category_id']].keys())[0]

        answer = text(
            bold(await get_text(msg, 'show_room', 'category')),
            list_categories,
            bold(await get_text(msg, 'show_room', 'tags')),
            ' '.join(group['subcategories']) + '\n',
            await get_msg(c.message, 'date'), sep='\n'
        ).replace('_', '\\n')

        dt = datetime.datetime.now() + datetime.timedelta(hours=3)

        buts = []
        global days

        for day in days:
            data_str = await get_data_str(msg, dt.strftime('%-d %B'))
            but = types.InlineKeyboardButton(data_str, callback_data=day)
            buts.append(but)
            dt += datetime.timedelta(days=1)

        keyboard = types.InlineKeyboardMarkup().row(buts[0], buts[1]).row(
            buts[2], buts[3]).row(buts[4], buts[5]).row(buts[6])

        await bot.send_message(
            user_id,
            answer,
            parse_mode=types.ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        await change_state(c, 3)
    elif d == 'Назад':
        db.groups.update_one({'chat_id': chat_id},
                            {"$set": {'subcategories': [],
                                      'category_id': 13}})

        await bot.edit_message_reply_markup(
            user_id,
            message_id=c.message.message_id,
            reply_markup=await base_categories_keyboard(c.message)
        )
    else:
        await bot.edit_message_reply_markup(
            user_id,
            message_id=c.message.message_id,
            reply_markup=await get_keyboard(c.message, int(d))
        )


@dp.callback_query_handler(lambda c:True, state=TestStates.TEST_STATE_5)
async def register(c):
    print('inline')
    user_id = str(c.message.chat.id)
    msg = c.message

    d = c.data
    if d == 'Завершить':
        with suppress(MessageNotModified):
            await bot.edit_message_reply_markup(
                user_id,
                message_id=c.message.message_id
            )

        await bot.send_message(
            user_id,
            await get_msg(msg, 'category_selected'),
            reply_markup=await everytime_keyboard(msg)
        )
        await change_state(c, 0)
    elif d == 'Назад':
        await bot.edit_message_reply_markup(
            user_id,
            message_id=c.message.message_id,
            reply_markup=await base_categories_keyboard(c.message)
        )
    else:
        await bot.edit_message_reply_markup(
            user_id,
            message_id=c.message.message_id,
            reply_markup=await get_keyboard_reg(c.message, int(d))
        )


@dp.message_handler(state='*', commands=['start'])
async def start(msg):
    print('start')
    if await check_chat(msg):
        return

    user_id = str(msg.chat.id)
    if int(user_id) > 0:
        user = db.users.find_one({'chat_id': user_id})
        if user == None:
            db.users.insert_one({
                'chat_id': user_id,
                'groups_ids': [],
                'subcategories': [[] for i in range(13)],
                'language_code': 'en'
            })

            await bot.send_message(
                user_id,
                await get_msg(msg, 'change_language'),
                reply_markup=await language_keyboard()
            )
            #await change_state(msg, 5)
        else:
            await bot.send_message(
                user_id,
                await get_msg(msg, 'start_in_chat_with_reg'),
                reply_markup=await everytime_keyboard(msg)
            )

'''
@dp.message_handler(state='*', commands=['help'])
async def help(msg):
    print('help')
    if await check_chat(msg):
        return

    await bot.send_message(
        msg.chat.id,
        await get_msg(msg, 'help_in_group')
    )
'''

async def delete_command(text):
    if text[0] == '/':
        text = text.split(' ', 1)
        if len(text) > 1:
            return text[1]

    return text


async def title(msg, chat_id):
    print(msg)
    voice = db.groups.find_one({'chat_id': chat_id})

    answer = ''
    if voice == None:
        chat = await bot.get_chat(chat_id)

        res = ''
        try:
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
                res = res['data']['url']
        except:
            res = ''

        try:
            await bot.export_chat_invite_link(chat_id)
        except Exception as e:
            print(e)

        type_chat = 'group'
        if msg.forward_from_chat != None:
            type_chat = 'channel'

        chat = await bot.get_chat(chat_id)
        voice = {
            'chat_id': chat_id,
            'status': 'offline',
            'inviteLink': chat.invite_link,
            'date': 0,
            'deadline': int(datetime.datetime.timestamp(datetime.datetime.now())),
            'admins': [],#await get_admins(chat_id),
            'members': 0,#await get_members(chat_id),
            'subcategories': [],
            'category_id': 13,
            'logo': res,
            'language_code': msg['from']['language_code'],
            'created': 0,
            'username': msg.forward_from_chat.username,
            'type': type_chat,
            'title': msg.forward_from_chat.title,
            'description': '',
            'message_id': msg.forward_from_message_id
        }
        db.groups.insert_one(voice)
    else:
        db.groups.update_one(
            {'chat_id': chat_id},
            {"$set": {'title': text}}
        )

'''
@dp.message_handler(state='*', commands=['change_title'])
async def change_title(msg):
    print('change_title')
    if await check_chat(msg):
        return

    await title(msg)

    await bot.send_message(
        msg.chat.id,
        answer.change_title,
    )
'''


async def get_room_text(msg, chat_id):
    group = db.groups.find_one({'chat_id': chat_id})

    list_categories = group['subcategories']

    if group['category_id'] != 13:
        categories = await get_cat(msg)
        category = list(
            categories[group['category_id']].keys())[0]
        list_categories.insert(0, category)

    list_categories = ['#' + c.replace(' ', '_').replace('-',
        '_') for c in list_categories]

    time = datetime.datetime.fromtimestamp(
        group['date'] + 3 * 60 * 60).strftime("%-d %B %H:%M")

    time = await get_data_str(msg, time)

    if group['status'] == 'online':
        time += await get_msg(msg, 'voicechat_started')

    post_link = 't.me/' + group['username']

    if group['message_id'] != 0:
        post_link += '/' + str(group['message_id'])

    answer = text(
        time,
        bold(group['title']),
        group['description'],
        post_link,
        't.me/' + group['username'] + '?voicechat',
        ' '.join(list_categories),

        sep='\n\n'
    ).replace('_', '\_')

    return answer


async def send_room(msg):
    print('send_room')

    chat_id = await get_chat_id(str(msg.chat.id))
    answer = await get_room_text(msg, chat_id)

    button = types.InlineKeyboardButton(
        await get_text(msg, 'buttons', 'to_hub'),
        url='https://nethub.club/#/?m=room&room=' + chat_id
    )
    keyboard = types.InlineKeyboardMarkup().add(button)
    res = await bot.send_message(
        chat_id,
        answer,
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    await bot.pin_chat_message(
        res.chat.id, res.message_id,
        disable_notification=True
    )

'''
@dp.message_handler(state='*', commands=['delete_room'])
async def delete_room(msg):
    print('delete_room')
    if await check_chat(msg):
        return
    chat_id = str(msg.chat.id)
    db.groups.delete_one({'chat_id': chat_id})
    await bot.send_message(
        chat_id,
        await get_msg(msg, 'room_is_delete')
    )
'''

@dp.message_handler(state='*', commands=['new_room'])
async def state_0(msg):
    print('new_room')
    if (not await check_chat(msg) or await check_member(msg) or
            await check_bot_privilege(msg)): return

    chat_id = str(msg.chat.id)
    user_id = str(msg['from']['id'])

    if await check_active_group(msg, chat_id, user_id):
        return

    db.groups.delete_one({'chat_id': chat_id})

    user = db.users.find_one({'chat_id': user_id})
    groups_ids = user['groups_ids']
    groups_ids.append(chat_id)
    groups_ids = list(set(groups_ids))
    db.users.update_one({'chat_id': user_id},
                        {'$set': {'groups_ids': groups_ids}})
    db.active_group.delete_one({'user_id': user_id})
    db.active_group.insert_one({'user_id': user_id, 'chat_id': chat_id})

    await title(msg, chat_id)

    if user == None:
        return

    await bot.send_message(
        chat_id,
        await get_msg(msg, 'go_to_bot')
    )

    await bot.send_message(
        user['chat_id'],
        await get_msg(msg, 'new_room'),
        reply_markup=types.ReplyKeyboardRemove()
    )
    await change_state(msg, 1)


@dp.message_handler(state=TestStates.TEST_STATE_1)
async def state_1(msg):
    print('state_1')
    if await check_chat(msg):
        return

    user_id = str(msg['from']['id'])
    chat_id = await get_chat_id(user_id)

    db.groups.update_one({'chat_id': chat_id},
                        {'$set': {'title': msg.text}})

    await bot.send_message(
        user_id,
        'Теперь введите описание комнаты.',
    )
    await change_state(msg, 7)


@dp.message_handler(state=TestStates.TEST_STATE_7)
async def state_1(msg):
    print('state_1')
    if await check_chat(msg):
        return

    user_id = str(msg['from']['id'])
    chat_id = await get_chat_id(user_id)

    db.groups.update_one({'chat_id': chat_id},
                        {'$set': {'description': msg.text}})

    await bot.send_message(
        user_id,
        await get_msg(msg, 'title'),
        reply_markup=await base_categories_keyboard(msg)
    )
    await change_state(msg, 2)


async def correct_time(user_time):
    try:
        if len(user_time) != 5 or user_time[2] != ':':
            return False
        h = int(user_time[:2])
        m = int(user_time[3:])
        if h < 0 or h > 23 or m < 0 or m > 59:
            return False

        return (h * 60 + m) * 60
    except:
        return False


@dp.callback_query_handler(lambda c: c.data == 'Опубликовать' or
    c.data == 'Отказать', state='*')
async def admin_callback(c):
    print(c)
    channel_id = -1001370003626
    admin_chat_id = -1001242007249

    if c.data == 'Опубликовать':
        await bot.send_message(
            channel_id,
            c.message.text
        )
    else:
        pass

    await bot.edit_message_reply_markup(
        admin_chat_id,
        message_id=c.message.message_id
    )


async def send_tginfo(msg, chat_id):
    admin_chat_id = -1001242007249
    group = db.groups.find_one({'chat_id': chat_id})

    but0 = types.InlineKeyboardButton('Опубликовать', callback_data='Опубликовать')
    but1 = types.InlineKeyboardButton('Отказать', callback_data='Отказать')
    keyboard = types.InlineKeyboardMarkup().add(but0).add(but1)

    await asyncio.sleep(20)

    db.groups.update_one({'chat_id': chat_id}, {'$set' : {'created': 1}})

    await bot.send_message(
        admin_chat_id,
        await get_room_text(msg, chat_id),
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )


@dp.message_handler(state=TestStates.TEST_STATE_4)
async def state_2(msg):
    print('state_2')
    if await check_chat(msg):
        return

    user_id = str(msg['from']['id'])
    chat_id = await get_chat_id(user_id)

    group = db.groups.find_one({'chat_id': chat_id})
    timestamp = group['date']

    user_time = await correct_time(msg.text)
    if user_time == False:
        await bot.send_message(
            user_id,
            await get_msg(msg, 'time_is_correct')
        )
        return

    timestamp += user_time

    time_now = int(datetime.datetime.timestamp(datetime.datetime.now()))
    if timestamp < time_now - 2*60*60:
        await bot.send_message(
            user_id,
            await get_msg(msg, 'past_tense')
        )
        return

    db.groups.update_one({'chat_id': chat_id},
                        {"$set": {'date': timestamp, 'deadline': timestamp,
                        'created': 0}})
    '''
    but1 = types.KeyboardButton(await get_text(msg, 'buttons',
        'ok_publish'))
    but2 = types.KeyboardButton(await get_text(msg, 'buttons',
        'nok_publish'))
    publish_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
        ).add(but1).add(but2)
    '''
    await bot.send_message(
        user_id,
        await get_msg(msg, 'wait'),
        reply_markup=await everytime_keyboard(msg)
    )
    db.active_group.delete_one({'user_id': str(msg.chat.id)})

    await send_tginfo(msg, chat_id)

    await bot.send_message(
        user_id,
        await get_msg(msg, 'complete'),
        reply_markup=await everytime_keyboard(msg)
    )

    await change_state(msg, 0)


@dp.message_handler(state=TestStates.TEST_STATE_6, content_types=['text'])
async def publish(msg):
    print('publish')
    if msg.text == await get_text(msg, 'buttons', 'ok_publish'):
        await send_room(msg)

    db.active_group.delete_one({'user_id': str(msg.chat.id)})

    await bot.send_message(
        msg.chat.id,
        await get_msg(msg, 'complete'),
        reply_markup=await everytime_keyboard(msg)
    )
    await change_state(msg, 0)


@dp.message_handler(state=TestStates.TEST_STATE_8, content_types=['text'])
async def is_announcement(msg):
    user_id = str(msg['from']['id'])

    if msg.text == await get_text(msg, 'buttons', 'no'):
        chat_id = await get_chat_id(user_id)

        db.groups.update_one({'chat_id': chat_id}, {'$set' : {'message_id': 0}})

    await bot.send_message(
        user_id,
        await get_msg(msg, 'description')
    )

    await change_state(msg, 7)


@dp.message_handler(lambda msg: msg.forward_from_chat,
    content_types=types.ContentTypes.ANY, state='*')
async def forward_from_chat(msg):
    print('forward_from_chat')
    #if (await check_chat(msg) or await check_member_channel(msg) or
    #    await check_bot_privilege_channel(msg)): return

    chat_id = str(msg.forward_from_chat.id)
    user_id = str(msg['from']['id'])

    if await check_active_group(msg, chat_id, user_id):
        return

    if db.groups.find_one({'chat_id': chat_id}):
        await bot.send_message(
            user_id,
            await get_msg(msg, 'room_created')
        )
        return

    db.groups.delete_one({'chat_id': chat_id})

    user = db.users.find_one({'chat_id': user_id})
    groups_ids = user['groups_ids']
    groups_ids.append(chat_id)
    groups_ids = list(set(groups_ids))
    db.users.update_one({'chat_id': user_id},
                        {'$set': {'groups_ids': groups_ids}})
    db.active_group.delete_one({'user_id': user_id})
    db.active_group.insert_one({'user_id': user_id, 'chat_id': chat_id})

    await title(msg, chat_id)

    if user == None:
        return

    but0 = types.KeyboardButton(await get_text(msg, 'buttons', 'yes'))
    but1 = types.KeyboardButton(await get_text(msg, 'buttons', 'no'))

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
        one_time_keyboard=True).add(but0).add(but1)

    await bot.send_message(
        user['chat_id'],
        await get_msg(msg, 'is_announcement'),
        reply_markup=keyboard
    )
    await change_state(msg, 8)


@dp.message_handler(state='*', content_types=['voice_chat_started'])
async def voice_chat_started(msg):
    print('voice_chat_started')
    group = db.groups.find_one({'chat_id': str(msg.chat.id)})
    if group != None:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'status': 'online'}}
        )


@dp.message_handler(state='*', content_types=['voice_chat_ended'])
async def voice_chat_ended(msg):
    print('voice_chat_ended')
    group = db.groups.find_one({'chat_id': str(msg.chat.id)})
    if group != None:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'status': 'offline'}}
        )


async def update_members_info(msg):
    db.groups.update_one(
        {'chat_id': str(msg.chat.id)},
        {"$set":
            {'admins': await get_admins(msg.chat.id),
            'members': await get_members(msg.chat.id)}
        }
    )


@dp.message_handler(state='*', content_types=['new_chat_members'])
async def joined_the_group(msg):
    print('new_chat_members')
    await update_members_info(msg)

    '''
    for member in message.new_chat_members:
        if member.id == bot.id:
            user = db.users.find_one({'chat_id': str(msg['from']['id'])})
            groups_ids = user.groups_ids
            groups_ids.append(str(msg.chat.id))
            db.users.update_one({'chat_id': str(msg['from']['id'])},
                {'$set': {'groups_ids': list(set(groups_id))}})
    '''


@dp.message_handler(state='*', content_types=['text'])
async def main_logic(msg):
    print('main_logic')
    print(msg)
    list_language = ['English', 'Русский']

    if msg.chat.id > 0:
        if msg.text == await get_text(msg, 'buttons', 'create_room_in_group'):
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'make_room_in_group')
            )
        elif msg.text == await get_text(msg, 'buttons', 'create_room_in_channel'):
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'make_room_in_channel')
            )
        elif msg.text == await get_text(msg, 'buttons', 'to_hub'):
            button = types.InlineKeyboardButton(
                await get_text(msg, 'buttons', 'to_hub'),
                url='https://nethub.club/#/'
            )
            keyboard = types.InlineKeyboardMarkup().add(button)

            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'greeting'),
                reply_markup=keyboard
            )
        elif msg.text == await get_text(msg, 'buttons', 'settings'):
            but1 = types.KeyboardButton(await get_text(msg, 'buttons',
                'change_category'))
            but2 = types.KeyboardButton(await get_text(msg, 'buttons',
                'change_language'))
            but3 = types.KeyboardButton(await get_text(msg, 'buttons',
                'feedback'))
            but4 = types.KeyboardButton(await get_text(msg, 'buttons',
                'back_to_general'))
            settings_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True,
                ).add(but1).add(but2).add(but3).add(but4)

            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'list_settings'),
                reply_markup=settings_keyboard
            )
        elif msg.text == await get_text(msg, 'buttons', 'change_language'):
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'change_language'),
                reply_markup=await language_keyboard()
            )
        elif msg.text in list_language:
            await change_language(msg)
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'change_language_success'),
                reply_markup=await everytime_keyboard(msg)
            )
        elif msg.text == await get_text(msg, 'buttons', 'change_category'):
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'settings'),
                reply_markup=await base_categories_keyboard(msg)
            )
            await change_state(msg, 5)
        elif msg.text == await get_text(msg, 'buttons', 'back_to_general'):
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'start_in_chat_with_reg'),
                reply_markup=await everytime_keyboard(msg)
            )
        elif msg.text == await get_text(msg, 'buttons', 'feedback'):
            await bot.send_message(
                msg.chat.id,
                await get_msg(msg, 'feedback'),
                reply_markup=await everytime_keyboard(msg)
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
