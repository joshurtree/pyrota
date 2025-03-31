#!/usr/local/bin/use-venv .venv
import argparse
import caldav
import calendar
from datetime import datetime, timedelta
import itertools
import logging
import sys
import yaml

SUMMARY=''

def parse_days(days: str) :
    for day in days.split(",") : 
        if len(day) == 1 :
            yield int(day)
        else :
            for d in range(int(day[0]), int(day[2]) + 1) :
                yield d
    
def parse_rota(cal, rota, holidays, summary) :
    week_start = datetime.combine(rota['start-date'], datetime.min.time())
    logging.info(f"Rota based on weeks starting on a {calendar.day_name[week_start.weekday()]}")
    rota_loop = iter(itertools.cycle(rota['weeks']))

    logging.debug(rota)
    logging.debug(holidays)
    while week_start.date() < rota['end-date'] :
        for day in parse_days(next(rota_loop)) :
            if day > 6 :
                logging.warn(f"Day with value {day} used. This will run into the next week.")
            start = week_start + timedelta(days=day, seconds=rota['start-time'])

            if start.date() not in holidays :
                logging.info("Adding date: " + start.date().strftime("%d/%m/%y"))
                cal.save_event(dtstart=start,
                                dtend=start + timedelta(hours=rota['duration']),
                                summary=summary)

        week_start += timedelta(weeks=1)

parser = argparse.ArgumentParser(
                    prog='pyrota',
                    description='Upload rota defined in a yaml file to Caldav server')
parser.add_argument("-d", "--debug")
parser.add_argument("file")
args = parser.parse_args()

if  args.debug :
    logging.basicConfig(level=logging.DEBUG)
else :
    logging.basicConfig(level=logging.INFO)

file = args.file if hasattr(args, "file") else "config.yml"

with open(args.file, 'r') as file :
    config = yaml.safe_load(file)
    with caldav.DAVClient(url=config['server'], username=config['username'], password=config['password']) as client:
        cal = client.calendar(url=config['server'] + config['calendar'])
        for event in cal.events() :
            event.delete()

        for rota in config['rota'] :
            parse_rota(cal, rota, config.get('holidays', []), config.get('summary', 'Josh at work'))
