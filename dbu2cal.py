import os
import time
import re
from urllib.request import urlopen

import icalendar
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup


def build_calendar(url):

    # Define domain
    dbu = 'www.dbukoebenhavn.dk' in url
    dai = 'resultater.dai-sport.dk' in url

    # Read page
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    # Create dataframe for xls(x) file
    if dbu:
        xlsx_url = soup.find(attrs={'title': 'Download EXCEL'}).get('onclick')
        xlsx_url = re.findall(r"(?<=window.open\(').*(?=',)", xlsx_url)[0]
        df = pd.read_excel('https://www.dbukoebenhavn.dk' + xlsx_url)
    if dai:
        xlsx_url = soup.find(attrs={'id': 'ctl00_ContentPlaceHolder1_Hold1_PageTop_PagePrint_WordLinkRight'}).get('href')
        df = pd.read_html('http://resultater.dai-sport.dk' + xlsx_url, header=0)[0]
        df = df.rename(columns={'Kl.': 'Tid', 'Hjemmehold': 'Hjemme', 'Udehold': 'Ude'})
    
    # Format date column
    df['Dato'] = pd.to_datetime(df['Dato'], dayfirst=True).astype(str)

    # Create calendar object
    cal = icalendar.Calendar()
    cal.add('X-WR-CALNAME', url)
    cal.add('X-WR-TIMEZONE', 'Europe/Copenhagen')

    # Loop through fixtures
    for _, row in df.iterrows():

        # Create event object
        temp_event = icalendar.Event()

        # Add event title (including result if available)
        event_name = row['Hjemme'] + ' - ' + row['Ude']
        if dbu:
            if not np.isnan(row['Score hjemme']) and not np.isnan(row['Score ude']):
                result = ' (' + str(int(row['Score hjemme'])) + '-' + str(int(row['Score ude'])) + ')'
            else:
                result = ''
        if dai:
            if isinstance(row['Resultat'], str):
                result = ' (' + row['Resultat'] + ')'
            else:
                result = ''
        temp_event.add('summary', event_name + result)

        # Add link to match page
        if dbu:
            league_id = re.findall(r'(?<=%C2%).+(?=/)', url)[0]
            match_url = 'https://www.dbukoebenhavn.dk/resultater/kamp/{}%C2%{}'.format(row['Kampnr'], league_id)
        if dai:
            match_url = url
        temp_event.add('description', match_url)

        # Add location
        temp_event.add('location', row['Spillested'])

        # Add start and end times
        start_time = pd.Timestamp(' '.join((row['Dato'], row['Tid'])))
        end_time = start_time + pd.Timedelta(hours=2)
        temp_event.add('dtstart', start_time)
        temp_event.add('dtend', end_time)

        # Add event to calendar
        cal.add_component(temp_event)

    return cal


def save_calendar(cal, url, path_prefix='./calendars/', filename=None):

    # If filename not defined, use timestamp
    if not filename:
        timestamp = time.strftime('%Y%m%d-%H%M')
        filename = 'dbu_game_cal_{}'.format(timestamp)
    whole_path = os.path.join(path_prefix, filename)

    # Write url to txt file
    with open(whole_path + '.txt', 'w') as f:
        f.write(url)

    # Write calendar to iCal file
    with open(whole_path + '.ics', 'wb') as f:
        f.write(cal.to_ical())
    print('Calendar saved to {}'.format(whole_path + '.ics'))

    return filename


def update_calendars():

    # Loop all files in calendar directory
    print(os.path.abspath('./'))
    for filename in os.listdir('./calendars/'):

        # If iCal file, check if there is a complementary txt file
        if filename.endswith('.ics'):
            main_filename = filename.split('.ics')[0]
            txt_path = os.path.join('./calendars/', main_filename + '.txt')
            if os.path.isfile(txt_path):

                # Read URL
                url = open(txt_path).read()

                # Update and overwrite calendar file
                try:
                    updated_cal = build_calendar(url)
                    filename = save_calendar(updated_cal, url, filename=main_filename)
                    print('Updated {}'.format(filename))
                except:
                    print('Error: {}'.format(url))
