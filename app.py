import requests
from flask import Flask, send_from_directory, request, render_template

import dbu2cal


app = Flask(__name__)


@app.route('/')
def url_form():
    return render_template('url-form.html')


@app.route('/', methods=['POST'])
def host_cal():
    url = request.form['text']

    cal = dbu2cal.build_calendar(url)
    filename = dbu2cal.save_calendar(cal, url) + '.ics'

    ip = requests.get('https://api.ipify.org').text

    explanation = 'Paste the following link into your calendar program (or click to download): '
    link = 'http://{}:5000/{}'.format(ip, filename)

    return explanation + '<br><br>' + '<a href="{}"> {} </a>'.format(filename, link)


@app.route('/<path:filename>')
def download(filename):

    return send_from_directory('./calendars/', filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
