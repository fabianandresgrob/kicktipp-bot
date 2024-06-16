# -*- coding: utf-8 -*-
import random
from datetime import datetime
from datetime import timedelta
from time import sleep
import requests
import json
import re

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Constants
BASE_URL = "https://www.kicktipp.de"
LOGIN_URL = "https://www.kicktipp.de/info/profil/login"

# read email, password and competition name from login_data.json file
with open('login_data.json') as json_file:
    data = json.load(json_file)
    EMAIL = data['EMAIL']
    PASSWORD = data['PASSWORD']
    NAME_OF_COMPETITION = data['KICKTIPP_NAME_OF_COMPETITION']
    ZAPIER_URL = data['ZAPIER_URL']

# set up dictionary to get english names
country_mapping = {
    'Deutschland': 'germany',
    'Ungarn': 'hungary',
    'Schweiz': 'switzerland',
    'Schottland': 'scotland',
    'Spanien': 'spain',
    'Kroatien': 'croatia',
    'Italien': 'italy',
    'Albanien': 'albania',
    'Slowenien': 'slovenia',
    'Dänemark': 'denmark',
    'Serbien': 'serbia',
    'England': 'england',
    'Polen': 'poland',
    'Niederlande': 'netherlands',
    'Österreich': 'austria',
    'Frankreich': 'france',
    'Belgien': 'belgium',
    'Slowakei': 'slovakia',
    'Rumänien': 'romania',
    'Ukraine': 'ukraine',
    'Türkei': 'turkey',
    'Georgien': 'georgia',
    'Portugal': 'portugal',
    'Tschechien': 'czech'
}


def execute(post_to_zapier: bool = True, headless: bool = True, debug_mode: bool = False):
    # create driver
    if headless and debug_mode:
        raise ValueError('Cannot be headless and debug mode!')
    elif headless:
        driver = webdriver.Chrome(
            options=set_chrome_options())  # for docker
    elif debug_mode:
        print('Debug Mode\n')
        driver = webdriver.Chrome()  # debug

    # login
    driver.get(LOGIN_URL)

    # enter email
    driver.find_element(by=By.ID, value="kennung").send_keys(EMAIL)

    # enter password
    driver.find_element(by=By.ID, value="passwort").send_keys(PASSWORD)

    # send login
    driver.find_element(by=By.NAME, value="submitbutton").click()

    # accept AGB
    try:
        driver.find_element(
            by=By.XPATH, value='//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]').click()
    except NoSuchElementException:
        pass

    # entry form
    driver.get(F"https://www.kicktipp.de/{NAME_OF_COMPETITION}/tippabgabe")

    # saw the AGB here again, so check and accept
    try:
        driver.find_element(
            by=By.XPATH, value='//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]').click()
    except NoSuchElementException:
        pass

    count = driver.find_elements(by=By.CLASS_NAME, value="datarow").__len__()

    # iterate over rows of the form
    for i in range(1, count + 1):
        try:
            # get Team names
            homeTeam = driver.find_element(
                by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[2]').get_attribute('innerHTML')
            awayTeam = driver.find_element(
                by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[3]').get_attribute('innerHTML')
            
            # find entry, enter if empty
            homeTipEntry = driver.find_element(by=By.XPATH,
                                               value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[4]/input[2]')
            awayTipEntry = driver.find_element(by=By.XPATH,
                                               value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[4]/input[3]')

            # only calc tip and enter, when not entered already
            if homeTipEntry.get_attribute('value') == '' and awayTipEntry.get_attribute('value') == '':

                try:
                    # time of game
                    time = datetime.strptime(
                        driver.find_element(
                            by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[1]').get_property('innerHTML'),
                        '%d.%m.%y %H:%M')
                except ValueError:
                    pass

                # print time and team names
                print(homeTeam + " - " + awayTeam +
                      "\nTime: " + str(time.strftime('%d.%m.%y %H:%M')))

                # time until start of game
                timeUntilGame = time - datetime.now()
                print("Time until game: " + str(timeUntilGame))

                # only tip if game starts in less than 2 hours
                if timeUntilGame < timedelta(hours=2):
                    print("Game starts in less than 2 hours. Tipping now...")

                    # find quotes
                    quotes = driver.find_element(
                        by=By.XPATH, value='//*[@id="tippabgabeSpiele"]/tbody/tr[' + str(i) + ']/td[5]/a').get_property('innerHTML').split(sep=" / ")
                    quotes = process_quotes(quotes)

                    # print quotes
                    print("Quotes:" + str(quotes))

                    # store original window
                    original_window = driver.current_window_handle

                    # get xG for home and away
                    xG_home, xG_away = get_xG(driver, homeTeam, awayTeam, time)

                    # switch back to original window
                    driver.switch_to.window(original_window)

                    # calculate tips bases on quotes and print them
                    tip = compute_game_prediction(xG_home, xG_away, quotes)
                    print("Tip: " + str(tip))
                    print()

                    # send tips
                    homeTipEntry.send_keys(tip[0])
                    awayTipEntry.send_keys(tip[1])

                    # custom webhook to zapier
                    try:
                        if post_to_zapier:
                            # convert time to hh:mm
                            time_hours = time.strftime('%H:%M')
                            url = ZAPIER_URL
                            message = f"""🎉 EURO 24 Vorhersage-Alarm! 🎉\n\nHeute um {time_hours} Uhr ist es soweit: {homeTeam} trifft auf {awayTeam}! 🏆⚽\nUnser Bot hat gesprochen:\n{homeTeam} {tip[0]}:{tip[1]} {awayTeam}! 🔮\nHolt die Snacks und Getränke raus, macht es euch bequem und lasst uns gemeinsam die Tore feiern! 🍿🎉🍻"""
                            payload = {
                                'message': message
                                }
                            files = []
                            headers = {}

                            response = requests.request(
                                "POST", url, headers=headers, data=payload, files=files)
                    except IndexError:
                        pass

                else:
                    print("Game starts in more than 2 hours. Skipping...")
                    print()
            else:
                # print out the tipped game
                print(homeTeam + " - " + awayTeam)
                
                print("Game already tipped! Tip: " + homeTipEntry.get_attribute('value') + " - " + awayTipEntry.get_attribute('value'))
                print()

        except NoSuchElementException:
            continue
    sleep(10 if debug_mode else 2)

    # submit all tips
    driver.find_element(by=By.NAME, value="submitbutton").submit()

    # print Quotes
    try:
        print("Total bet: " + str(driver.find_element(by=By.XPATH,
              value='//*[@id="kicktipp-content"]/div[3]/div[2]/a/div/div[1]/div[1]/div[1]/div[2]/span[2]')
                                  .get_property('innerHTML')
                                  .replace('&nbsp;', ''))
              + "\n")
    except NoSuchElementException:
        print("Total bet not found")

    try:
        if debug_mode:
            print("Sleeping for 20secs to see the result - Debug Mode\n")
            sleep(20)
    except IndexError:
        pass

    driver.quit()

def get_xG(driver, homeTeam, awayTeam, time):
    """
    This method gets the expected goals for both teams from https://xgscore.io/.
    """
    # switch to a new tab in the browser
    driver.switch_to.new_window('tab')
    # build url to get xG from
    # url has format https://xgscore.io/euro/$homeTeam-$awayTeam-$dd-$mm-$yy/xgscore
    date = time.strftime('%d-%m-%y')
    url = F"https://xgscore.io/euro/{country_mapping[homeTeam]}-{country_mapping[awayTeam]}-{date}/xgscore"

    # go to that link
    driver.get(url)

    # get by xpath the home expected goals valuex
    xG_home = driver.find_element(by=By.XPATH, value='//*[@id="xgs-game-result"]/div[2]/div/mark[1]')
    xG_away = driver.find_element(by=By.XPATH, value='//*[@id="xgs-game-result"]/div[2]/div/mark[2]')
    # actual float values
    xG_home_value = float(remove_tags(xG_home.get_property('innerHTML')))
    xG_away_value = float(remove_tags(xG_away.get_property('innerHTML')))
    
    # close tab
    driver.close()

    return xG_home_value, xG_away_value

def process_quotes(quotes):
    """
    Quotes are displayed as strings and the first value has `Quote: ` in front of it.
    This function processes the quotes and returns them as floats.
    """
    home = float(quotes[0].split(sep=" ")[1])
    draw = float(quotes[1])
    away = float(quotes[2])
    return home, draw, away


def remove_tags(text):
    tag_re = re.compile(r'<[^>]+>')
    return tag_re.sub('', text)

# now build new prediction based on xG values and quotes for this game
def compute_game_prediction(xG_home, xG_away, quotes):
    # if home win quote is lower than away win quote, factor this onto the xG.
    # if away win quote is lower, weight away xG.
    home, draw, away = quotes
    total_quote = sum(quotes)
    prob_home = 1 - (home / total_quote)
    prob_away = 1 - (away / total_quote)
    prob_draw = 1 - (draw / total_quote)
    factor_home = random.uniform(0, 1 + prob_home)
    factor_draw = random.uniform(0, 1 + prob_draw)
    factor_away = random.uniform(0, 1 + prob_away)
    # maybe also include a error margin here
    if not draw == min(quotes):
        # weight home and away goals
        pred_home = round(xG_home * factor_home)
        pred_away = round(xG_away * factor_away)
    else:
        # draw is the most likely, multiply both xG by factor
        pred_home = round(xG_home * factor_draw)
        pred_away = round(xG_away * factor_draw)

    return pred_home, pred_away

def set_chrome_options() -> None:
    """Sets chrome options for Selenium.
    Chrome options for headless browser is enabled.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    return chrome_options


if __name__ == '__main__':
    while True:
        now = datetime.now().strftime('%d.%m.%y %H:%M')
        print(now + ": The script will execute now!\n")
        try:
            execute()
        except Exception as e:
            print("An error occured: " + str(e) + "\n")
        now = datetime.now().strftime('%d.%m.%y %H:%M')
        print(now + ": The script has finished. Sleeping for 1 hour...\n")
        sleep(60*60)
