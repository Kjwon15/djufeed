import requests
import pytz

from datetime import datetime

from pyatom import AtomFeed
from lxml import etree, html
from fake_useragent import FakeUserAgent

from ..decorators import cache

ua = FakeUserAgent()

localzone = pytz.timezone('Asia/Seoul')

session = requests.session()
session.headers.update({
    'User-Agent': ua.chrome,
})


@cache(60 * 5)  # Cache 5 minutes
def get_content(url, xpath):

    resp = session.get(url)
    tree = html.fromstring(resp.content.decode(resp.apparent_encoding))
    return etree.tostring(
        tree.xpath(xpath)[0]
    ).decode()

def postg_notifications(location):
    url = 'http://office.dju.kr/postg/board/board1.htm'
    resp = session.get(url)
    tree = html.fromstring(resp.content.decode(resp.apparent_encoding))
    tree.make_links_absolute(url)
    table = tree.xpath('//*/table//table//table//table//table[2]')[0]

    feed = AtomFeed(
        title='DJU postg notification',
        url=location,
        author='Kjwon15')

    for tr in table.xpath('tr[position() mod 2 = 1 and position() != last()]'):
        number = tr.xpath('td[1]')[0].text_content().strip()
        title = tr.xpath('td[2]')[0].text_content().strip()
        is_new = bool(tr.xpath('td[2]')[0].xpath('img'))
        author = tr.xpath('td[3]')[0].text_content().strip()
        date = tr.xpath('td[4]')[0].text_content().strip()
        date = datetime.strptime(date, '%Y-%m-%d')
        link = tr.xpath('td[2]/a')[0].attrib['href']

        feed.add(
            title='{}{} {}'.format(number, ' [new]' if is_new else '', title),
            author=author,
            url=link,
            updated=date,
        )

    return feed.to_string()


def dju_notifications(location):
    url = 'https://www.dju.ac.kr/kor/html/subp.htm?page_code=01050100'
    resp = session.get(url)
    tree = html.fromstring(resp.content.decode(resp.apparent_encoding))
    tree.make_links_absolute(url)
    table = tree.xpath('//*/table[contains(@class, "bbs")]')[0]

    feed = AtomFeed(
        title='DJU notification',
        url=location,
        author='Kjwon15')

    for tr in table.xpath('tbody/tr'):
        print(tr)
        number = tr.xpath('td[1]')[0].text_content().strip()
        title = tr.xpath('td[2]')[0].text_content().strip()
        is_new = bool(tr.xpath('td[2]')[0].xpath('img'))
        author = tr.xpath('td[3]')[0].text_content().strip()
        date = tr.xpath('td[5]')[0].text_content().strip()
        date = datetime.strptime(date, '%Y.%m.%d')
        link = tr.xpath('td[2]/a')[0].attrib['href']

        content = get_content(link, '//*/div[contains(@class, "core")]')

        feed.add(
            title='{}{} {}'.format(number, ' [new]' if is_new else '', title),
            author=author,
            url=link,
            updated=date,
            content=content,
            content_type='html',
        )

    return feed.to_string()
