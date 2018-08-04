import os
import time
from datetime import datetime, timedelta
from urllib.request import urlopen

import icalendar
import pandas as pd
from bs4 import BeautifulSoup


def build_calendar(url):
    # Read table into dataframe
    df = pd.read_html(url, attrs={
        'class': 'dbustandard stripes full srDefault srProgram1 srDefaultPadding'})[0]

    # Remove first row if it is a duplicate of the header
    if df.iloc[0, 0] == 'Kamp':
        df.drop(index=0, inplace=True)
        df.reset_index(drop=True, inplace=True)

    # Correct column names
    new_header = df.columns.to_series().shift(1)
    new_header.iat[0] = 'Kampnr'
    df = df.rename(new_header, axis='columns')

    # Read page into BeautifulSoup (used to get link to match page)
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    # Create calendar object
    cal = icalendar.Calendar()

    # Give calendar a relevant name
    team = soup.find('h1', attrs={
        'id':
            'indhold_0_indholdbredvenstre_0_integrationwrapper_1_ctl01_PageTop_TopHeadline2'}).text
    # "Kampprogram" is the header if not filtering by team
    team = team + ' ' if team != 'Kampprogram' else ''
    league = soup.find('h4', attrs={
        'id':
            'indhold_0_indholdbredvenstre_0_integrationwrapper_1_ctl01_PageTop_TopHeadline1'}).text
    league = league.replace(',', '')
    cal.add('X-WR-CALNAME', team + league)

    # Define timezone
    cal.add('X-WR-TIMEZONE', 'Europe/Copenhagen')

    # Loop through
    for row in df.iterrows():
        # Create event object
        temp_event = icalendar.Event()

        # Add title (including result if available)
        event_name = row[1]['Hjemmehold'] + ' - ' + row[1]['Udehold']
        result = ' (' + row[1]['Res'] + ')' if row[1]['Res'] == row[1]['Res'] else ''
        temp_event.add('summary', event_name + result)

        # Add link to match page
        link = soup.find('a', attrs={
            'title': 'Kampinformation for {}'.format(row[1]['Kampnr'])})['href']
        url_first_part = '/'.join(url.split('/')[:-1])
        match_url = '/'.join((url_first_part, link))
        temp_event.add('description', match_url)

        # Get address from match page
        match_page = urlopen(match_url)
        match_soup = BeautifulSoup(match_page, 'html.parser')
        address = ', '.join(match_soup.find(
            'td', string='Spillested').find_next_sibling().get_text('///').split('///')[1:3])
        temp_event.add('location', address)

        # Add start and end times
        start_time = datetime.strptime(
            row[1]['Tidspunkt'], '%d-%m-%yKl. %H:%M')
        end_time = start_time + timedelta(hours=2)
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

                # Read DBU url
                dbu_url = open(txt_path).read()

                # Update and overwrite calendar file
                updated_cal = build_calendar(dbu_url)
                filename = save_calendar(updated_cal, dbu_url, filename=main_filename)

                # Print result
                print('Updated {}'.format(filename))
