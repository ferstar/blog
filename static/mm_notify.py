#!/usr/bin/env python3
import os

import aiohttp
import asyncio

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
team_id = os.getenv('TEAM_ID')
mm_host = os.getenv('MM_HOST')
# sc_key = os.getenv('SC_KEY')
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


class MSGCounter:
    __slots__ = ['mention_count', 'p_msg_count']

    def __init__(self, mention_count=0, p_msg_count=0):
        self.mention_count = mention_count
        self.p_msg_count = p_msg_count

    @property
    def max_count(self):
        return max(self.mention_count, self.p_msg_count)

    def __repr__(self):
        return '提及: {}, 私信: {}'.format(self.mention_count, self.p_msg_count)


async def http_get(session, url):
    async with session.get(url) as rsp:
        if rsp.status == 200:
            return await rsp.json()


async def calc_msg_count():
    counter = MSGCounter()
    async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
        url = '{}/api/v4/users/me/teams/unread'.format(mm_host)
        for item in await http_get(session, url):
            counter.mention_count += item.get('mention_count', 0)
        url = mm_host + '/api/v4/users/me/teams/{}/channels?include_deleted=false'.format(team_id)
        for channel in await http_get(session, url):
            url = mm_host + '/api/v4/users/me/channels/{}/unread'.format(channel.get("id"))
            if channel.get('type') == 'P':  # private channel
                counter.mention_count += (await http_get(session, url)).get('mention_count', 0)
            if channel.get('type') == 'D':  # discuss channel
                counter.p_msg_count += (await http_get(session, url)).get('msg_count', 0)
    print(counter)
    return counter


async def send_notify(title, msg):
    # requests.get('https://sc.ftqq.com/{}.send?text={}&desp={}'.format(sc_key, title, msg))
    url = "https://api.alertover.com/v1/alert"
    data = {
        "source": alert_from,
        "receiver": alert_to,
        "title": title,
        "content": msg
    }
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=data):
            pass


async def main():
    try:
        counter = await calc_msg_count()
    except Exception as exp:
        await send_notify('Exception occurred, Maybe you should update your MM cookie', str(exp))
    else:
        if counter.max_count > 0:
            await send_notify('MM有人给你发消息', str(counter))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
