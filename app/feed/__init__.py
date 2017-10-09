from flask import Blueprint, Response, url_for
from . import feeds

app = Blueprint('feed', __name__)


def get_links():
    return {
        url_for('feed.postg_notifications'): 'POSTG notifications feed',
    }


@app.route('/postg_notifications')
def postg_notifications():
    feed = feeds.postg_notifications()
    return Response(
        feed,
        mimetype='application/xml')
