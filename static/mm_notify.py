#!/usr/bin/env python3
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import aiohttp
import asyncio

from multidict import CIMultiDict

user_agent = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/83.0.4103.116 Safari/537.36'
)
user_id = os.getenv('USER_ID')
team_id = os.getenv('TEAM_ID')
mm_host = os.getenv('MM_HOST')
alert_from = os.getenv('ALERT_FROM')
alert_to = os.getenv('ALERT_TO')
mm_cookie = os.getenv('MM_COOKIE')
headers = {
    'authority': mm_host.split('//')[1],
    'pragma': 'no-cache',
    'cache-control': 'no-cache',
    'accept-language': 'zh-CN',
    'user-agent': user_agent,
    'x-requested-with': 'XMLHttpRequest',
    'accept': '*/*',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'cookie': mm_cookie,
}
timeout = aiohttp.ClientTimeout(total=60)


class Session(aiohttp.ClientSession):
    def __init__(self, *args, **kwargs):
        super(Session, self).__init__(*args, **kwargs)
        self.counter = Counter()
        self._times = 0
        self._start_at = datetime.now()

    async def a_get(self, url):
        self._times += 1
        async with self.get(url) as rsp:
            if rsp.status == 200:
                return await rsp.json()

    async def a_post(self, url, *, data=None, **kwargs):
        self._times += 1
        async with self.post(url, data=data, **kwargs) as rsp:
            if rsp.status == 200:
                return await rsp.json()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        print(f'Total requests: {self._times}, cost: {(datetime.now() - self._start_at).seconds}s.')


async def calc_msg_count(session):
    # rsp = await http_get(session, f'{mm_host}/api/v4/users/me/teams/unread')
    # for item in rsp:
    #     counter.mention_count += item.get('mention_count', 0)
    channels = await session.a_get(f'{mm_host}/api/v4/users/me/teams/{team_id}/channels?include_deleted=false')
    for channel in channels:
        rsp = await session.a_get(f'{mm_host}/api/v4/users/me/channels/{channel.get("id")}/unread')
        if channel.get('type') in ('O', 'P', 'G') and rsp.get('mention_count', 0) > 0:  # open/private/group channel
            session.counter.update([channel['display_name']] * rsp['mention_count'])
        if channel.get('type') == 'D' and rsp.get('msg_count', 0) > 0:  # discuss channel
            uid = channel['name'].replace(user_id, '').strip('__')
            user_info = await session.a_get(f'{mm_host}/api/v4/users/{uid}')
            session.counter.update([user_info['nickname'] or user_info['last_name'] + user_info['first_name']] * rsp['msg_count'])
    return session.counter


async def send_notify(session: Session, title, msg):
    data = {"source": alert_from, "receiver": alert_to, "title": title, "content": msg}
    session._default_headers = CIMultiDict({})
    await session.a_post("https://api.alertover.com/v1/alert", json=data)


async def main():
    async with Session(headers=headers, timeout=timeout) as session:
        try:
            counter = await calc_msg_count(session)
        except Exception as exp:
            msg = 'Exception occurred, Maybe you should update your MM cookie'
            print(msg)
            await send_notify(session, msg, str(exp))
        else:
            if counter:
                print(counter)
                await send_notify(session, 'MM有人给你发消息', '\n'.join(f'{k}=>{v}' for k, v in counter.items()))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

