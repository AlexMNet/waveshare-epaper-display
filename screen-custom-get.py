import logging
import os
import requests
from utility import update_svg, configure_logging

configure_logging()


def main():
    output_svg_filename = 'screen-custom.svg'

    # If you make changes to this file be sure to make a backup in case you ever update!

    # Add custom code here like getting PiHole Status, car charger status, API calls.
    # Assign the value you want to display to custom_value_1, and it will replace CUSTOM_DATA_1 in screen-custom.svg.
    # You can edit the screen-custom.svg to change appearance, position, font size, add more custom data.
    def get_messages():
        url = ("https://api.notion.com/v1/blocks/0e8f0aeccc7b4e08b9e67fc900e45b1c/children")
        notion_apikey = os.getenv("NOTION_KEY")
        try:
            response = requests.get(url, headers={"Authorization": f"Bearer {notion_apikey}"})
            print(f"NOTION RESPONSE: {str(response.json())}")
        except Exception as error:
            print('Something wrong has happened', error)


    get_messages()

    custom_value_1 = "testing...";

    logging.info("Updating SVG")
    output_dict = {
        'CUSTOM_DATA_1' : custom_value_1
    }
    update_svg('screen-custom.svg', 'screen-output-custom-temp.svg', output_dict)

if __name__ == "__main__":
    main()
