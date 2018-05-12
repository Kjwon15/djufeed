import datetime
import re

import fake_useragent
from flask import Blueprint, Response, url_for
import icalendar
import lxml.html
import requests

from ..decorators import cache


app = Blueprint('calendar', __name__)


def get_links():
    return {
        url_for('calendar.djucal'): 'DJU calendar',
        url_for('calendar.postgcal'): 'POSTG calendar',
    }


@app.route('/dju.ical')
def djucal():
    cal = make_djucal()
    response = Response(
        cal.to_ical().decode('utf-8'),
        mimetype='text/calendar')

    return response


@app.route('/postg.ical')
def postgcal():
    cal = make_postgcal()
    response = Response(
        cal.to_ical().decode('utf-8'),
        mimetype='text/calendar')

    return response


def extract_dju_schedule(year, schedule):
    pattern = re.compile(
        r'(?P<from>\d{1,2}/\d{1,2})'
        r'(?: ~(?P<to>\d{1,2}/\d{1,2}))?'
        r'\s*(?:\d{4}학년도\s+)?(?P<content>.*)')

    event = icalendar.Event()
    matched = pattern.match(schedule)

    from_date = matched.group('from')
    to_date = matched.group('to')
    content = matched.group('content')

    event.add('dtstart', datetime.date(year, *map(int, from_date.split('/'))))
    if to_date:
        event.add('dtend', datetime.date(year, *map(int, to_date.split('/'))))

    event.add('summary', content)

    return event


def extract_postg_schedule(year, datestring, comment):
    pattern = re.compile(
        r'(?P<frommonth>\d+)\.\s*(?P<fromdate>\d+)\(.*?\)'
        r'(?:\s*~\s*(?P<tomonth>\d+)\.\s*(?P<todate>\d+)\(.*?\))?')

    event = icalendar.Event()
    matched = pattern.match(datestring)

    frommonth, fromdate = matched.group('frommonth'), matched.group('fromdate')
    event.add('dtstart', datetime.date(year, int(frommonth), int(fromdate)))

    tomonth, todate = matched.group('tomonth'), matched.group('todate')
    if tomonth and todate:
        event.add('dtend', datetime.date(year, int(tomonth), int(todate)))

    event.add('summary', comment)

    return event


@cache(60 * 60)  # An hour
def make_djucal():
    session = make_session()

    current_year = datetime.date.today().year

    cal = icalendar.Calendar()

    for year in [current_year-1, current_year]:
        resp = session.get('http://www.dju.ac.kr/kor/html/subp.htm', params={
            'page_code': '01040100',
            'listYear': year,
        })

        tree = lxml.html.fromstring(resp.content.decode('cp949'))

        for month in tree.xpath('//*[@class="sch-box"]'):
            year_month = month.find('*/*[@class="year"]').text_content()
            year = int(year_month.split('/')[0])
            for schedule in month.findall('*[@class="schList-box"]/ul/li'):
                t = schedule.text_content()
                event = extract_dju_schedule(year, t)
                cal.add_component(event)

    return cal


@cache(60 * 60)  # An hour
def make_postgcal():
    session = make_session()

    resp = session.get(
        'http://office.dju.ac.kr/postg/schedule/schedule1_04.htm')
    tree = lxml.html.fromstring(resp.content.decode('cp949'))

    cal = icalendar.Calendar()

    year_month_pattern = re.compile(
        r'^(?:(?P<year>\d{4}).*\s+)?(?P<month>\d{1,2})$')
    # Failsafe year.
    year = datetime.datetime.today().year - 1

    for month in tree.xpath('//table[@class="table-c"]/tr'):
        matched = year_month_pattern.match(month.find('td').text_content())
        if not matched:
            continue

        year_str = matched.group('year')
        if year_str:
            year = int(year_str)

        dates = map(
            lambda x: x.strip(),
            month.find('td[3]').text_content().split('\n'))
        contents = map(
            lambda x: x.strip(),
            month.find('td[4]').text_content().split('\n'))

        for date, content in zip(dates, contents):
            if not date or not content:
                continue
            event = extract_postg_schedule(year, date, content)
            cal.add_component(event)

    return cal


def make_session():
    ua = fake_useragent.UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')  # noqa
    session = requests.session()
    session.headers['User-Agent'] = ua.best_browser
    return session
