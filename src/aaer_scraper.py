import datetime
import os
import re
import sys
import time
from urllib.request import urlopen

from bs4 import BeautifulSoup
import pymysql
import requests

SEC_FRIACTIONS_URL = "https://www.sec.gov/divisions/enforce/friactions"


def add_to_db(rds_cursor, values):
    string = ""
    for value in values:
        string += '("' + '","'.join(
            [
                "https://www." + value[0],
                re.sub("'", "", value[1]),
                re.sub('"', "", value[2]),
            ]
        ) + '",0),'
    if len(string) == 0:
        return

    string = string[:-1]  # removes trailing comma
    rds_cursor.execute(
        f"""INSERT IGNORE INTO {os.environ["TABLE"]} (url, publish_date, respondents, scraped) VALUES {string};"""
    )


def get_old_urls(year, urls):
    url = SEC_FRIACTIONS_URL + f"/friactions{year}.shtml"
    response = urlopen(url)
    soup = BeautifulSoup(response, 'lxml')

    table = soup.findAll("table")
    if table is None:
        return

    rows = table[-2].find_all("tr")[1:]
    for row in rows:
        if len(row) == 6:
            temp = row.find_all("td")
            new_urls = [
                "sec.gov" + str(row.find("a").get("href")),
                temp[1].text.strip(),
                temp[2].text.splitlines()[0].strip()
            ]
            urls.append(new_urls)


def get_2010_urls(urls):
    url = SEC_FRIACTIONS_URL + "/friactions2010.htm"
    response = urlopen(url)
    soup = BeautifulSoup(response, 'lxml')

    table = soup.find("table")
    if table is None:
        return

    rows = table.find_all("tr")[1:]
    for row in rows:
        if len(row) == 7:
            temp = row.find_all("td")
            new_urls = [
                "sec.gov" + str(temp[0].find_all("a")[0].get("href")),
                temp[1].text.strip(),
                temp[2].text.replace("\t", "").replace("\n", "").strip()
            ]
            urls.append(new_urls)


def get_recent_urls(year, urls):
    url = SEC_FRIACTIONS_URL + f"/friactions{year}.htm"
    if year == datetime.date.today().year:
        url = SEC_FRIACTIONS_URL + ".htm"  # the current year's URL doesnt have /fractions____
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find("table", attrs={"class": "tablesorter"})
    if table is None:
        return

    rows = table.tbody.find_all("tr")[1:]
    for row in rows:
        if len(row.find_all("td")) > 1:
            temp = row.find_all("td")
            new_urls = [
                "sec.gov" + str(temp[0].find_all("a")[0].get("href")),
                temp[1].text,
                temp[2].text.splitlines()[0]
            ]
            urls.append(new_urls)


def AAER_scraper(rds_cursor, start_year=1999, end_year=2022):
    # Function that returns dataframe of all AAER links, their date issued, and their respondents from 1999-2021

    # The US SEC website has different formats for different AAER years.
    # Therefore the process for scraping will be broken into three sections:1999-2009, 2010, 2011-2021
    urls = []
    year = start_year
    while year <= end_year:
        if year < 2010:
            get_old_urls(year, urls)
        elif year == 2010:
            get_2010_urls(urls)
        else:
            get_recent_urls(year, urls)

        time.sleep(1)  # needed to scrape from website without timing out
        year += 1

    add_to_db(rds_cursor, urls)


if __name__ == "__main__":
    conn = pymysql.connect(
        host=os.environ["ENDPOINT"],
        user=os.environ["USER"],
        password=os.environ["PASSWORD"],
        database=os.environ["DATABASE"],
        autocommit=True,
    )
    cursor = conn.cursor()

    if len(sys.argv) == 3:
        AAER_scraper(cursor, start_year=int(sys.argv[1]), end_year=int(sys.argv[2]))
    else:
        AAER_scraper(cursor)
