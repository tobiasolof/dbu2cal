import os
import time
import re
from datetime import datetime, timedelta
from urllib.request import urlopen

import icalendar
import pandas as pd
from bs4 import BeautifulSoup


def build_calendar(url):

    # Set domain-specific paths
    if 'dbukoebenhavn' in url:
        domain = 'dbu'
        class_path = 'dbustandard stripes full srDefault srProgram1 srDefaultPadding'
        team_path = 'indhold_0_indholdbredvenstre_0_integrationwrapper_1_ctl01_PageTop_TopHeadline2'
        league_path = 'indhold_0_indholdbredvenstre_0_integrationwrapper_1_ctl01_PageTop_TopHeadline1'
        result_path = 'Res'
        date_path = 'Tidspunkt'
        date_format = '%d-%m-%yKl. %H:%M'
    elif 'dai-sport' in url:
        domain = 'dai'
        class_path = 'srDefault srProgramNormal'
        team_path = 'ctl00_ContentPlaceHolder1_Hold1_PageTop_MainHeadline'
        league_path = 'ctl00_ContentPlaceHolder1_Hold1_PageTop_TopHeadline'
        result_path = 'Resultat'
        date_path = 'Dato'
        date_format = '%d-%m-%y  kl. %H:%M'

    # Read table into dataframe
    df = pd.read_html(url, attrs={'class': class_path}, flavor='bs4')[0]

    # Remove first row if it is a duplicate of the header
    if df.iloc[0, 0] == 'Kamp':
        df.drop(index=0, inplace=True)
        df.reset_index(drop=True, inplace=True)

    # Correct column names
    if domain == 'dbu':
        new_header = df.columns.to_series().shift(1)
        new_header.iat[0] = 'Kampnr'
        df = df.rename(new_header, axis='columns')
    df.columns = [col.strip() for col in df.columns]

    # Read page into BeautifulSoup (used to get link to match page)
    page = urlopen(url)
    soup = BeautifulSoup(page, 'html.parser')

    # Create calendar object
    cal = icalendar.Calendar()

    # Give calendar a relevant name
    team = soup.find(attrs={'id': team_path}).text
    # "Kampprogram" is the header if not filtering by team
    team = team + ' ' if team != 'Kampprogram' else ''
    league = soup.find(attrs={'id': league_path}).text
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
        result = ' (' + row[1][result_path] + ')' if row[1][result_path] == row[1][result_path] else ''
        temp_event.add('summary', event_name + result)

        # Add link to match page
        if domain == 'dbu':
            link = soup.find('a', attrs={
                'title': 'Kampinformation for {}'.format(row[1]['Kampnr'])})['href']
            url_first_part = '/'.join(url.split('/')[:-1])
            match_url = '/'.join((url_first_part, link))
        elif domain == 'dai':
            link = soup.find('a', string=str(row[1]['Kampnr.']))['href']
            url_first_part = '/'.join(url.split('/')[:-3])
            match_url = ''.join((url_first_part, link))
        temp_event.add('description', match_url)

        # Get address from match page
        match_page = urlopen(match_url)
        match_soup = BeautifulSoup(match_page, 'html.parser')
        address = ', '.join(match_soup.find(
            'td', string=re.compile('\s*Spillested\s*')
        ).find_next_sibling().get_text('///').split('///')[1:3])
        temp_event.add('location', address)

        # Add start and end times
        start_time = datetime.strptime(
            row[1][date_path], date_format)
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
