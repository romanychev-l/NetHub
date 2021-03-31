import api_config
import asyncio
import datetime
import config
import base64
import requests
import os
import time

from pymongo import MongoClient
from multiprocessing import Process

from telethon import TelegramClient, sync, events
from telethon import functions, types


db_client = MongoClient('mongodb://admin:Factor_9@localhost:27017')
db = db_client[config.mongo_db_name]


client = TelegramClient('session_name', api_config.api_id, api_config.api_hash)


@client.on(events.NewMessage(chats=('tgbroadcasting')))
async def tg_fm(event):
    print(event)
    msg = event.message.message
    if msg.find('активен голосовой чат'):
        channel_username = msg.split()[2][1:]
        channel = await client(functions.channels.GetFullChannelRequest(
            channel=channel_username
        ))
        channel_id = '-100' +  str(channel.full_chat.id)
        if channel.chats[0].call_active == False:
            return

        call = channel.full_chat.call

        group_call = await client(functions.phone.GetGroupCallRequest(
            call=call
        ))
        #print(group_call.stringify())


        res = ''
        try:
            with open('avatar', 'wb') as f:
                photos = await client.get_profile_photos(channel_username)
                photo = await client.download_media(photos[-1], channel_username)

            res = 0
            with open(channel_username + '.jpg', 'rb') as f:
                url = "https://api.imgbb.com/1/upload"
                payload = {
                    "key": '0fed957c70c9bd1193587969d205dd2b',
                    "image": base64.b64encode(f.read()),
                }
                res = requests.post(url, payload).json()
                res = res['data']['url']

            os.remove(channel_username + '.jpg')
        except:
            res = ''

        now_time = int(datetime.datetime.timestamp(datetime.datetime.now()))
        title = group_call.call.title
        if title == None:
            title = channel.chats[0].title
        group = {
            'chat_id': channel_id,
            'status': 'online',
            'inviteLink': '@' + channel_username,
            'date': now_time,
            'deadline': now_time,
            'admins': '',
            'members': group_call.call.participants_count,
            'subcategories': [],
            'category_id': -1,
            'logo': res,
            'language_code': 'en',
            'created': 1,
            'title': title,
            'type': 'tgfm',
            'username': channel_username
        }
        db.groups.delete_one({'chat_id': channel_id})
        db.groups.insert_one(group)


async def check():
    while True:
        print('check')
        groups = db.groups.find({'type': 'tgfm'})
        for group in groups:
            channel = await client(functions.channels.GetFullChannelRequest(
                channel=group['username']
            ))
            if channel.chats[0].call_active == False:
                db.groups.delete_one({'chat_id': group['chat_id']})
            else:
                call = channel.full_chat.call

                group_call = await client(functions.phone.GetGroupCallRequest(
                    call=call
                ))

                db.groups.update_one({'chat_id': group['chat_id']}, {'$set' :
                    {'members': group_call.call.participants_count}})

        await asyncio.sleep(10)


async def run():
    await client.run_until_disconnected()


if __name__ == '__main__':
    client.start()

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(run()),
        loop.create_task(check())
    ]
    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)
    loop.close()


