from flask import Blueprint, Response, request, url_for
from . import feeds

app = Blueprint('feed', __name__)


def get_links():
    return {
        url_for('feed.notifications'): 'DJU notifications feed',
        url_for('feed.postg_notifications'): 'POSTG notifications feed',
    }


@app.route('/postg_notifications')
def postg_notifications():
    feed = feeds.postg_notifications(request.url)
    return Response(
        feed,
        mimetype='application/xml')


@app.route('/notifications')
def notifications():
    feed = feeds.dju_notifications(request.url)
    return Response(
        feed,
        mimetype='application/xml')
