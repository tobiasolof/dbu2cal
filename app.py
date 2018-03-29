import ipgetter
from flask import Flask, send_from_directory
from webargs import fields
from webargs.flaskparser import use_kwargs

import dbu2cal

app = Flask(__name__)


@app.route('/host')
@use_kwargs({
    'TeamId': fields.Str(required=True),
    'PoolId': fields.Str(),
    'DateFrom': fields.Str(),
    'DateTo': fields.Str(),
    'HomeMatch': fields.Str(),
    'AwayMatch': fields.Str()
})
def host_cal(TeamId, PoolId, DateFrom, DateTo, HomeMatch, AwayMatch):
    """Parse url and save calendar to file."""

    # Define DBU url
    url = 'https://www.dbukoebenhavn.dk/turneringer_og_resultater/resultatsoegning/programTeam.aspx?'
    url += 'TeamId={}&'.format(TeamId)
    url += 'PoolId={}&'.format(PoolId)
    url += 'DateFrom={}&'.format(DateFrom)
    url += 'DateTo={}&'.format(DateTo)
    url += 'HomeMatch={}&'.format(HomeMatch)
    url += 'AwayMatch={}&'.format(AwayMatch)
    print(url)

    cal = dbu2cal.build_calendar(url)
    filename = dbu2cal.save_calendar(cal)

    ip = ipgetter.myip()

    explanation = 'Paste the following link into your calendar program: '

    return explanation + '{}:5000/{}'.format(ip, filename)


@app.route('/')
def bost_cal():
    return 'hej'





@app.route('/<path:filename>')
def download(filename):

    return send_from_directory('./calendars/', filename, as_attachment=True)


if __name__ == '__main__':
    app.run()
