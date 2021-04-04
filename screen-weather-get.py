#!/usr/bin/python

import datetime
import sys
import os
import json
import logging
from weather_providers import climacell, openweathermap, metofficedatahub, accuweather
from utility import is_stale, update_svg, configure_logging
import textwrap

configure_logging()


def get_cached_weather(filename, ttl):
    if is_stale(filename, ttl):
        logging.info("Weather cache is stale.")
        return None

    logging.info("Found in cache")
    with open(filename, 'r') as file:
        return json.loads(file.read())


def cache_weather_data(filename, weather_data):
    if weather_data:
        with open(filename, 'w') as text_file:
            json.dump(weather_data, text_file)


def format_weather_description(weather_description):
    if len(weather_description) < 20:
        return {1: weather_description, 2: ''}

    splits = textwrap.fill(weather_description, 20, break_long_words=False,
                           max_lines=2, placeholder='...').split('\n')
    weather_dict = {1: splits[0]}
    weather_dict[2] = splits[1] if len(splits) > 1 else ''
    return weather_dict


def main():

    # gather relevant environment configs
    climacell_apikey = os.getenv("CLIMACELL_APIKEY")
    openweathermap_apikey = os.getenv("OPENWEATHERMAP_APIKEY")
    metoffice_clientid = os.getenv("METOFFICEDATAHUB_CLIENT_ID")
    metoffice_clientsecret = os.getenv("METOFFICEDATAHUB_CLIENT_SECRET")
    accuweather_apikey = os.getenv("ACCUWEATHER_APIKEY")
    accuweather_locationkey = os.getenv("ACCUWEATHER_LOCATIONKEY")

    if (
        not climacell_apikey
        and not openweathermap_apikey
        and not metoffice_clientid
        and not accuweather_apikey
    ):
        logging.error("API Key for weather is missing (Climacell, OpenWeatherMap, MetOffice, AccuWeather...)")
        sys.exit(1)

    weather_format = os.getenv("WEATHER_FORMAT", "CELSIUS")
    if (weather_format == "CELSIUS"):
        units = "metric"
    else:
        units = "imperial"

    location_lat = os.getenv("WEATHER_LATITUDE", "51.3656")
    location_long = os.getenv("WEATHER_LONGITUDE", "-0.1963")

    # TTL for refetching of JSON
    ttl = float(os.getenv("WEATHER_TTL", 1 * 60 * 60))
    cache_weather_file = "weather-cache.json"

    weather = get_cached_weather(cache_weather_file, ttl)

    if not weather:
        if accuweather_apikey:
            logging.info("Getting weather from Accuweather")
            weather = accuweather.get_weather(
                                                accuweather_apikey, location_lat,
                                                location_long,
                                                accuweather_locationkey,
                                                units)
            logging.debug(weather)

        elif metoffice_clientid:
            logging.info("Getting weather from Met Office Weather Datahub")
            weather = metofficedatahub.get_weather(
                                                    metoffice_clientid,
                                                    metoffice_clientsecret,
                                                    location_lat,
                                                    location_long,
                                                    units)
            logging.debug(weather)

        elif openweathermap_apikey:
            logging.info("Getting weather from OpenWeatherMap")
            weather = openweathermap.get_weather(
                                                openweathermap_apikey,
                                                location_lat,
                                                location_long,
                                                units)
            logging.debug(weather)

        elif climacell_apikey:
            logging.info("Getting weather from Climacell")
            weather = climacell.get_weather(
                                            climacell_apikey,
                                            location_lat,
                                            location_long,
                                            units)

        cache_weather_data(cache_weather_file, weather)

    logging.info("weather - {}".format(weather))

    if not weather:
        logging.error("Unable to fetch weather payload. SVG will not be updated.")
        return

    degrees = "°C" if units == "metric" else "°F"

    weather_desc = format_weather_description(weather["description"])

    output_dict = {
        'LOW_ONE': "{}{}".format(str(round(weather['temperatureMin'])), degrees),
        'HIGH_ONE': "{}{}".format(str(round(weather['temperatureMax'])), degrees),
        'ICON_ONE': weather["icon"],
        'WEATHER_DESC_1': weather_desc[1],
        'WEATHER_DESC_2': weather_desc[2],
        'TIME_NOW': datetime.datetime.now().strftime("%-I:%M %p"),
        'DAY_ONE': datetime.datetime.now().strftime("%b %-d, %Y"),
        'DAY_NAME': datetime.datetime.now().strftime("%A"),
        'ALERT_MESSAGE': ""  # unused, see: https://github.com/mendhak/waveshare-epaper-display/issues/13
    }

    logging.debug("main() - {}".format(output_dict))

    logging.info("Updating SVG")
    template_svg_filename = 'screen-template.svg'
    output_svg_filename = 'screen-output-weather.svg'
    update_svg(template_svg_filename, output_svg_filename, output_dict)


if __name__ == "__main__":
    main()
