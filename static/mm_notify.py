#!/usr/bin/env python3
import os

import requests

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
team_id = os.getenv('TEAM_ID')
mm_host = os.getenv('MM_HOST')
# sc_key = os.getenv('SC_KEY')
alert_from = os.getenv('ALERT_FROM')
alert_to = os.getenv('ALERT_TO')
mm_cookie = os.getenv('MM_COOKIE')


class MSGCounter:
    __slots__ = ['mention_count', 'p_msg_count']

    def __init__(self, mention_count=0, p_msg_count=0):
        self.mention_count = mention_count
        self.p_msg_count = p_msg_count

    @property
    def max_count(self):
        # return max(self.mention_count, self.p_msg_count)
        return self.mention_count

    def __repr__(self):
        return '@you: {}, private channel: {}'.format(self.mention_count, self.p_msg_count)


def http_get(url):
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
    rsp = requests.get(url, headers=headers)
    if rsp.ok:
        return rsp.json()


def calc_msg_count():
    counter = MSGCounter()
    url = '{}/api/v4/users/me/teams/unread'.format(mm_host)
    for item in http_get(url):
        counter.mention_count += item.get('mention_count', 0)
    url = mm_host + '/api/v4/users/me/teams/{}/channels?include_deleted=false'.format(team_id)
    for channel in http_get(url):
        if channel.get('type') == 'P':  # private channel
            url = mm_host + '/api/v4/users/me/channels/{}/unread'.format(channel.get("id"))
            counter.mention_count += http_get(url).get('mention_count', 0)
            counter.p_msg_count += http_get(url).get('msg_count', 0)
    return counter


def send_notify(title, msg):
    # requests.get('https://sc.ftqq.com/{}.send?text={}&desp={}'.format(sc_key, title, msg))
    requests.post(
        "https://api.alertover.com/v1/alert",
        data={
            "source": alert_from,
            "receiver": alert_to,
            "title": title,
            "content": msg
        }
    )


def main():
    try:
        counter = calc_msg_count()
    except Exception as exp:
        send_notify('Exception occurred, Maybe you should update your MM cookie', str(exp))
    else:
        if counter.max_count > 0:
            send_notify('Unread Msg Notification from MM', str(counter))


if __name__ == '__main__':
    main()
