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

# webhook settings
WEBHOOK_HOST = 'https://romanychev.online'
WEBHOOK_PATH = config.path
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '127.0.0.1'  # or ip
WEBAPP_PORT = config.port

#logging.basicConfig(level=logging.INFO)

mongo_pass = config.mongo_pass
mongo_db = config.mongo_db
link = ('mongodb+srv://{}:{}@cluster0-e2dix.mongodb.net/{}?retryWrites=true&'
        'w=majority')
link = link.format("Leonid", mongo_pass, mongo_db)

client = MongoClient(link, connect=False)
db = client[config.mongo_db_name]

bot = Bot(token=config.token)
dp = Dispatcher(bot)
#dp.middleware.setup(LoggingMiddleware())
print("OK")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    #logging.warning('Shutting down..')
    await bot.delete_webhook()
    #logging.warning('Bye!')


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


@dp.message_handler(commands=["schedule_voice_chat"])
async def schedule(msg):
    print("schedule_voice_chat")
    if await check_chat(msg):
        return

    answer = ''
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})

    if voice == None:
        voice = {
            'chat_id': str(msg.chat.id),
            'heading': msg.text.split(' ', 1)[1],
            'status': 'offline',
            'link': '',
            'tags': []
        }
        db.groups.insert_one(voice)
        answer = 'Новый чат запланирован!'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'heading': msg.text.split(' ', 1)[1]}}
        )
        answer = 'Название чата изменено!'

    await bot.send_message(
        msg.chat.id,
        answer
    )


@dp.message_handler(commands=["add_tags"])
async def schedule(msg):
    print("add_tags")
    if await check_chat(msg):
        return
    answer = ''
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
    if voice == None:
        answer = 'Создайте чат по командe /schedule_voice_chat'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'tags': msg.text.split(' ', 1)[1].split()}}
        )
        answer = 'Теги добавлены'

    await bot.send_message(
        msg.chat.id,
        answer
    )


@dp.message_handler(commands=["add_link"])
async def schedule(msg):
    print("add_tags")
    if await check_chat(msg):
        return
    answer = ''
    voice = db.groups.find_one({'chat_id': str(msg.chat.id)})
    if voice == None:
        answer = 'Создайте чат по командe /schedule_voice_chat'
    else:
        db.groups.update_one(
            {'chat_id': str(msg.chat.id)},
            {"$set": {'link': msg.text.split(' ', 1)[1]}}
        )
        answer = 'Ссылка добавлена!'

    await bot.send_message(
        msg.chat.id,
        answer
    )


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
