import requests
import pytz

from datetime import datetime

from pyatom import AtomFeed
from lxml import html
from fake_useragent import FakeUserAgent

ua = FakeUserAgent()

localzone = pytz.timezone('Asia/Seoul')

session = requests.session()
session.headers.update({
    'User-Agent': ua.chrome,
})


def postg_notifications():
    url = 'http://office.dju.kr/postg/board/board1.htm'
    resp = session.get(url)
    tree = html.fromstring(resp.content.decode(resp.apparent_encoding))
    table = tree.xpath('//*/table//table//table//table//table[2]')[0]

    feed = AtomFeed(
        title='DJU postg notification',
        url='http://localhost/',
        author='Kjwon15')

    for tr in table.xpath('tr[position() mod 2 = 1 and position() != last()]'):
        number = tr.xpath('td[1]')[0].text_content().strip()
        title = tr.xpath('td[2]')[0].text_content().strip()
        is_new = bool(tr.xpath('td[2]')[0].xpath('img'))
        author = tr.xpath('td[3]')[0].text_content().strip()
        date = tr.xpath('td[4]')[0].text_content().strip()
        date = datetime.strptime(date, '%Y-%m-%d')
        link = url + tr.xpath('td[2]/a')[0].attrib['href']

        feed.add(
            title='{}{} {}'.format(number, ' [new]' if is_new else '', title),
            author=author,
            url=link,
            updated=date
        )

    return feed.to_string()
