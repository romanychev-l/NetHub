import config
import messages
import requests
import time
from time import sleep
import json
import pymongo
from pymongo import MongoClient
from multiprocessing import Process

from aiogram import Bot, Dispatcher, executor, types
import asyncio
from aiogram.utils.executor import start_webhook

from aiogram.utils.helper import Helper, HelperMode, ListItem

from aiogram.contrib.fsm_storage.memory import MemoryStorage
#from aiogram.contrib.middlewares.logging import LoggingMiddleware


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


@dp.message_handler(commands=['start'])
async def start(msg):
    chat_id = msg.chat.id
    if chat_id > 0:
        await bot.send_message(
            chat_id,
            "messages.command_start"
        )
    else:
        await bot.send_message(
            chat_id,
            "mes"
        )


async def delete_command(text):
    if text[0] == '\\':
        return text.split(' ', 1)[1]
    else:
        return text


@dp.message_handler(commands=['schedule_voice_chat'])
async def schedule(msg):
    print("schedule_voice_chat")
    if await check_chat(msg):
        return

    text = await delete_command(msg.text)
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    answer = ''
    if voice == None:
        voice = {
            'chat_id': str(msg.chat.id),
            'heading': text,
            'status': 'offline',
            'link': '',
            'tags': [],
            'admins': []
        }
        db.groups.insert_one(voice)
        answer = 'Новый чат запланирован!'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'heading': text}}
        )
        answer = 'Название чата изменено!'

    await bot.send_message(
        msg.chat.id,
        answer
    )


@dp.message_handler(commands=['add_tags'])
async def add_tags(msg):
    print("add_tags")
    if await check_chat(msg):
        return

    answer = ''
    text = await delete_command(msg.text)
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


@dp.message_handler(commands=['add_link'])
async def add_link(msg):
    print("add_tags")
    if await check_chat(msg):
        return

    answer = ''
    text = await delete_command(msg.text)
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
    if voice == None:
        answer = 'Создайте чат по командe /schedule_voice_chat'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'link': text}}
        )
        answer = 'Ссылка добавлена!'

    await bot.send_message(
        msg.chat.id,
        answer
    )


@dp.message_handler(commands=['add_admins'])
async def add_admins(msg):
    print('add_admins')
    if await check_chat(msg):
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


@dp.message_handler(commands=['show_event'])
async def show_event(msg):
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    if voice == None:
        answer = 'Создайте чат по командe /schedule_voice_chat'
    else:
        answer = (
            'Название:\n' + voice['heading'] +
            'Теги:\n' + voice['tags'] +
            'Ссылка:\n' + voice['link']
        )

    await bot.send_message(
        msg.chat.id,
        answer
    )



async def change_state(msg, num):
    state = dp.current_state(user=msg.from_user.id)
    await state.set_state(TestStates.all()[num])


@dp.message_handler(commands=['new_event'])
async def state_0(msg):
    print(bot.get_administrators(msg.chat.id))
    await bot.send_message(
        msg.chat.id,
        'В ответ на это сообщение пришлите название конференции'
    )
    await change_state(msg, 1)


@dp.message_handler(state=TestStates.TEST_STATE_1)
async def state_1(msg):
    await schedule(msg)
    await change_state(msg, 2)


@dp.message_handler(state=TestStates.TEST_STATE_2)
async def state_2(msg):
    await add_tags(msg)
    await change_state(msg, 3)


@dp.message_handler(state=TestStates.TEST_STATE_3)
async def state_3(msg):
    await add_link(msg)
    await change_state(msg, 4)


@dp.message_handler(state=TestStates.TEST_STATE_4)
async def state_4(msg):
    await add_admins(msg)
    await change_state(msg, 1)




@dp.message_handler(content_types=['text'])
async def main_logic(msg):
    if msg.text == 'Voice Chat started':
        print("OOO")
        voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
        if voice != None:
            print("P")
            db.groups.update_one(
                {'chat_id': str(msg.chat.id)},
                {"$set": {'status': 'online'}}
            )
    elif msg.text == 'Voice Chat ended':
        voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
        if voice != None:
            db.groups.update_one(
                {'chat_id': str(msg.chat.id)},
                {"$set": {'status': 'offline'}}
            )

    print("2")
    print(msg)


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
