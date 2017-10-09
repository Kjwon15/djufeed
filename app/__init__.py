from flask import Flask, render_template

from . import calendar
from . import feed


app = Flask(__name__)

app.register_blueprint(calendar.app, url_prefix='/calendar')
app.register_blueprint(feed.app, url_prefix='/feed')


@app.route('/')
def index():
    links = {
        **calendar.get_links(),
        **feed.get_links(),
    }
    return render_template(
        'index.html',
        links=links
    )
