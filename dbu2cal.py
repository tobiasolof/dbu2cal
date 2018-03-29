import os
import time
from datetime import datetime, timedelta
from urllib.request import urlopen

import icalendar
import pandas as pd
from bs4 import BeautifulSoup


def build_calendar(url):
    # Read table into dataframe
    df = pd.read_html(url, attrs={'class': 'dbustandard stripes full srDefault srProgram1 srDefaultPadding'})[0]

    # Correct column names
    new_header = df.columns.to_series().shift(1)
    new_header.iat[0] = 'Kampnr'
    df = df.rename(new_header, axis='columns')

    # Read page into BeautifulSoup (used to get link to match page)
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    # Create calendar object
    cal = icalendar.Calendar()

    # Loop through
    for row in df.iterrows():
        # Create event object
        temp_event = icalendar.Event()

        # Add title
        event_name = row[1]['Hjemmehold'] + ' - ' + row[1]['Udehold']
        temp_event.add('summary', event_name)

        # Add link to match page
        link = soup.find('a', attrs={'title': 'Kampinformation for {}'.format(row[1]['Kampnr'])})['href']
        url_first_part = '/'.join(url.split('/')[:-1])
        match_url = '/'.join((url_first_part, link))
        temp_event.add('description', match_url)

        # Get address from match page
        match_page = urlopen(match_url)
        match_soup = BeautifulSoup(match_page, 'html.parser')
        address = ', '.join(
            match_soup.find('td', string='Spillested').find_next_sibling().get_text('///').split('///')[1:3])
        temp_event.add('location', address)

        # Add start and end times
        start_time = datetime.strptime(row[1]['Tidspunkt'], '%d-%m-%yKl. %H:%M')
        end_time = start_time + timedelta(hours=2)
        temp_event.add('dtstart', start_time)
        temp_event.add('dtend', end_time)

        # Add event to calendar
        cal.add_component(temp_event)

    return cal


def save_calendar(cal, path_prefix='./calendars/'):

    # Get timestamp and concatenate path
    timestamp = time.strftime('%Y%m%d-%H%M')
    filename = 'dbu_game_cal_{}.ics'.format(timestamp)
    whole_path = os.path.join(path_prefix, filename)

    # Write calendar to iCal file
    with open(whole_path, 'wb') as f:
        f.write(cal.to_ical())
    print('Calendar saved to {}'.format(whole_path))

    return filename
