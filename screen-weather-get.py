#!/usr/bin/python

import json
import requests
import datetime
import codecs
import os.path
import time
import sys
import os
import html
import pytz
import logging
from astral import LocationInfo
from astral.sun import sun

logging.basicConfig(level=logging.INFO)

# Map Climacell icons to local icons
# Reference: https://docs.climacell.co/reference/data-layers-core
def get_icon_by_weathercode(weathercode, is_daytime):


    icon_dict = {
           0: 'unknown',
        1000: 'clear_sky_day' if is_daytime else 'clearnight',
        1001: 'climacell_cloudy' if is_daytime else 'overcast',
        1100: 'few_clouds' if is_daytime else 'partlycloudynight',
        1101: 'scattered_clouds' if is_daytime else 'partlycloudynight',
        1102: 'mostly_cloudy' if is_daytime else 'overcast',
        2000: 'climacell_fog',
        2100: 'climacell_fog_light',
        3000: 'wind',
        3001: 'wind',
        3002: 'wind',
        4000: 'climacell_drizzle' if is_daytime else 'rain_night',
        4001: 'climacell_rain' if is_daytime else 'rain_night',
        4200: 'climacell_rain_light' if is_daytime else 'rain_night',
        4201: 'climacell_rain_heavy' if is_daytime else 'rain_night',
        5000: 'snow',
        5001: 'climacell_flurries',
        5100: 'climacell_snow_light',
        5101: 'snow',
        6000: 'climacell_freezing_drizzle',
        6001: 'climacell_freezing_rain',
        6200: 'climacell_freezing_rain_light' ,
        6201: 'climacell_freezing_rain_heavy',
        7000: 'climacell_ice_pellets',
        7101: 'climacell_ice_pellets_heavy',
        7102: 'climacell_ice_pellets_light',
        8000: 'thundershower_rain',
        }


    icon = icon_dict[weathercode]
    logging.debug(
         "get_icon_by_weathercode({}, {}) - {}"
         .format(weathercode, is_daytime, icon))

    return icon

def get_description_by_weathercode(weathercode):

    description_dict = {
        0: "Unknown",
        1000: "Clear",
        1001: "Cloudy",
        1100: "Mostly Clear",
        1101: "Partly Cloudy",
        1102: "Mostly Cloudy",
        2000: "Fog",
        2100: "Light Fog",
        3000: "Light Wind",
        3001: "Wind",
        3002: "Strong Wind",
        4000: "Drizzle",
        4001: "Rain",
        4200: "Light Rain",
        4201: "Heavy Rain",
        5000: "Snow",
        5001: "Flurries",
        5100: "Light Snow",
        5101: "Heavy Snow",
        6000: "Freezing Drizzle",
        6001: "Freezing Rain",
        6200: "Light Freezing Rain",
        6201: "Heavy Freezing Rain",
        7000: "Ice Pellets",
        7101: "Heavy Ice Pellets",
        7102: "Light Ice Pellets",
        8000: "Thunderstorm"
    }

    description=description_dict[weathercode]

    logging.debug(
         "get_description_by_weathercode({}) - {}"
         .format(weathercode, description))

    return description



# Is it daytime? 
def is_daytime(location_lat, location_long):

    # adjust icon for sunrise and sunset
    dt = datetime.datetime.now(pytz.utc)
    city = LocationInfo(location_lat, location_long)
    s = sun(city.observer, date=dt)
    verdict = False
    if dt > s['sunset'] or dt < s['sunrise']:
        verdict = False
    else:
        verdict = True

    logging.debug(
        "is_daytime({}{}) - {}"
        .format(str(location_lat), str(location_long), str(verdict)))

    return verdict


# Get weather from Climacell
# Reference: https://docs.climacell.co/reference/retrieve-timelines-basic
def get_weather(climacell_apikey, location_latlong, filename, ttl):

    url = ("https://data.climacell.co/v4/timelines"
        + "?location={}&fields=temperatureMin&fields=temperatureMax&fields=weatherCode&timesteps=1d&apikey={}"
        .format(location_latlong, climacell_apikey))

    try:
        response_data = get_response_data(url, os.getcwd() + "/" + filename, ttl)
        weather = response_data['timelines'][0]['intervals'][0]['values']
        logging.debug("get_weather() - {}".format(weather))
    except Exception as error:
        logging.error(error)
        weather = False

    return weather

def get_response_data(url, filepath, ttl):

    response_json = False

    if (is_stale(filepath, ttl)):
        try:
            response_data = requests.get(url).text
            response_json = json.loads(response_data)['data']
            with open(filepath, 'w') as text_file:
                text_file.write(response_data)
        except Exception as error:
            logging.error(error)
            raise
    else:
        with open(filepath, 'r') as file:
            return json.loads(file.read())['data']
    return response_json

# Is the response file older than the TTL?
def is_stale(filepath, ttl): 

    verdict = True
    if (os.path.isfile(filepath)):
        verdict = time.time() - os.path.getmtime(filepath) > ttl

    logging.debug(
        "is_stale({}) - {}"
        .format(filepath, str(verdict)))

    return verdict

# utilize a template svg as a base for output of values
def update_svg(template_svg_filename, output_svg_filename, output_dict):
    #replace tags with values in SVG
    output = codecs.open(template_svg_filename, 'r', encoding='utf-8').read()

    for output_key in output_dict:
        logging.debug("output_weather() - {} -> {}".format(output_key, output_dict[output_key]))
        output = output.replace(output_key, output_dict[output_key])

    logging.debug("update_svg() - Write to SVG {}".format(output_svg_filename))

    codecs.open(output_svg_filename, 'w', encoding='utf-8').write(output)


def main():

    # gather relevant environment configs

    climacell_apikey=os.getenv("CLIMACELL_APIKEY","")

    if climacell_apikey=="":
        logging.error("CLIMACELL_APIKEY is missing")
        sys.exit(1)

    weather_format=os.getenv("WEATHER_FORMAT", "CELSIUS")

    template_svg_filename = 'screen-template.svg'
    output_svg_filename = 'screen-output-weather.svg'

    # json response files
    weather_timelines_filename = 'climacell-timelines-response.json'

    location_lat = os.getenv("WEATHER_LATITUDE","51.3656") 
    location_long = os.getenv("WEATHER_LONGITUDE","-0.1963") 

    location_latlong = (
        "{0:.2f},{1:.2f}"
        .format(float(location_lat), float(location_long)))

    # TTL for refetching of JSON
    ttl = float(os.getenv("WEATHER_TTL", 1 * 60 * 60))

    logging.info("Gathering weather")

    weather = get_weather(climacell_apikey, location_latlong, weather_timelines_filename, ttl)

    if (weather == False):
        logging.error("Unable to fetch weather payload. SVG will not be updated.")
        return

    output_dict = {
        'LOW_ONE': str(round(weather['temperatureMin']))+"°C" if weather_format == "CELSIUS" else str(round(weather['temperatureMin'] * 1.8) + 32)+"°F", 
        'HIGH_ONE': str(round(weather['temperatureMax']))+"°C" if weather_format == "CELSIUS" else str(round(weather['temperatureMax'] * 1.8) + 32)+"°F", 
        'ICON_ONE': get_icon_by_weathercode(weather['weatherCode'], is_daytime(location_lat, location_long)),
        'WEATHER_DESC': get_description_by_weathercode(weather['weatherCode']),
        'TIME_NOW': datetime.datetime.now().strftime("%-I:%M %p"),
        'DAY_ONE': datetime.datetime.now().strftime("%d %b %Y"),
        'DAY_NAME': datetime.datetime.now().strftime("%A"),
        'ALERT_MESSAGE': "" # unused
    }

    logging.debug("main() - {}".format(output_dict))

    logging.info("Updating SVG")
    update_svg(template_svg_filename, output_svg_filename, output_dict)


if __name__ == "__main__":
    main()
