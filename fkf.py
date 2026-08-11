# -*- coding: utf-8 -*-
"""
FKF waste-collection tracker.

This is the AppDaemon `hass.Hass` app rewritten as a plain Python class so it
can run standalone in Docker. All `self.log(...)` calls became `logger`
calls, and email is sent via `email_utils.send_email` (SMTP creds read from
environment variables) instead of the AppDaemon `commonfunctions` module.
"""

import datetime
import json
import os
import logging
import random
import traceback

import requests
from bs4 import BeautifulSoup

from email_utils import send_email

logger = logging.getLogger("fkf")

# ANSI escape codes for colored console logging
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
RESET = "\033[0m"

# Days before an event to start sending notification emails
NOTIFICATION_PERIOD = int(os.environ.get("NOTIFICATION_PERIOD", "2"))

LOCATIONS = [
    {
        "district": "1037",
        "publicPlace": "Királylaki---út",
        "houseNumber": "11",
        "recipients": ["srecko_podvinski@yahoo.com", "sapij17@gmail.com"],
    },
    {
        "district": "1037",
        "publicPlace": "Solymárvölgyi---út",
        "houseNumber": "13",
        "recipients": ["srecko_podvinski@yahoo.com"],
    },
]


def print_colored(text: str, color: str) -> None:
    logger.info(f"{color}{text}{RESET}")


class FKF:
    def __init__(self, locations=None):
        self.locations = locations if locations is not None else LOCATIONS

    def run(self):
        logger.info("FKF run")
        for location in self.locations:
            self.process_location(location)

    def process_location(self, location):
        try:
            url = "https://mohubudapest.hu/hulladeknaptar"

            # First POST request
            data = {"district": location["district"]}
            headers = {
                "X-OCTOBER-REQUEST-HANDLER": "onSelectDistricts",
                "X-OCTOBER-REQUEST-PARTIALS": "ajax/publicPlaces",
                "X-Requested-With": "XMLHttpRequest",
            }
            response = requests.post(url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            cookie = response.cookies.get_dict()

            # Second POST request
            data = {"publicPlace": location["publicPlace"]}
            headers["X-OCTOBER-REQUEST-HANDLER"] = "onSavePublicPlace"
            headers["X-OCTOBER-REQUEST-PARTIALS"] = "ajax/houseNumbers"
            response = requests.post(url, data=data, headers=headers, cookies=cookie, timeout=30)
            response.raise_for_status()

            # Third POST request
            data = {"houseNumber": location["houseNumber"]}
            headers["X-OCTOBER-REQUEST-HANDLER"] = "onSearch"
            headers["X-OCTOBER-REQUEST-PARTIALS"] = "ajax/calSearchResults"
            response = requests.post(url, data=data, headers=headers, cookies=cookie, timeout=30)
            response.raise_for_status()

            response_data = json.loads(response.text)
            html_table = response_data.get("ajax/calSearchResults") or response_data.get(".results")

            if html_table is None:
                raise KeyError(f"Unexpected response keys: {list(response_data.keys())}")

            self.process_html_table(html_table, location)

        except requests.exceptions.RequestException as e:
            place = location["publicPlace"].replace("---", " ")

            details = f"""
            HTTP error occurred:
            Type: {type(e).__name__}
            Message: {str(e)}
            """

            if e.request:
                details += f"""
            Request:
            Method: {e.request.method}
            URL: {e.request.url}
            """

            if e.response is not None:
                details += f"""
            Response:
            Status code: {e.response.status_code}
            Reason: {e.response.reason}
            Body: {e.response.text[:1000]}
            """

            logger.error(f"{details}\nLocation: {place}")

            send_email(
                "FKF error",
                f"""
                <h1>{place}</h1>
                <pre>{details}</pre>
                """,
                location["recipients"],
            )

        except json.JSONDecodeError as e:
            place = location["publicPlace"].replace("---", " ")

            snippet_start = max(0, e.pos - 50)
            snippet_end = e.pos + 50
            snippet = e.doc[snippet_start:snippet_end]

            logger.error(
                f"JSON error: {e.msg}, line={e.lineno}, col={e.colno}, pos={e.pos}\nNear: {snippet}"
            )

            send_email(
                "FKF error",
                f"""
                <h1>{place}</h1>
                <p><b>JSON decoding error:</b> {e.msg}</p>
                <p><b>Line:</b> {e.lineno}</p>
                <p><b>Column:</b> {e.colno}</p>
                <p><b>Position:</b> {e.pos}</p>
                """,
                location["recipients"],
            )

        except KeyError as e:
            place = location["publicPlace"].replace("---", " ")

            details = (
                f"KeyError occurred\n"
                f"Missing key: {e.args[0] if e.args else str(e)}\n"
                f"Exception type: {type(e).__name__}"
            )

            logger.error(f"{details} - {place}")

            send_email("FKF error", f"<h1>{place}</h1><pre>{details}</pre>", location["recipients"])

        except Exception as e:
            place = location["publicPlace"].replace("---", " ")

            details = (
                f"Unexpected error occurred\n"
                f"Type: {type(e).__name__}\n"
                f"Message: {str(e)}\n\n"
                f"Traceback:\n{traceback.format_exc()}"
            )

            logger.error(f"{details}\nLocation: {place}")

            send_email("FKF error", f"<h1>{place}</h1><pre>{details}</pre>", location["recipients"])

    def process_html_table(self, html_table, location):
        soup = BeautifulSoup(html_table, "html.parser")
        table_rows = soup.find_all("tr")
        current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        recipients = location["recipients"]

        for row in table_rows:
            tds = row.find_all("td")
            if any("Szelektív" in td.get_text() for td in tds):
                date_str = tds[1].get_text().strip()
                day = tds[0].get_text().strip()
                event_date = datetime.datetime.strptime(date_str, "%Y.%m.%d")

                address = location["publicPlace"].replace("---", " ")
                house_number = location["houseNumber"]

                print_colored(
                    f"Next selective collection for {address} {house_number} is on {date_str}", GREEN
                )
                time_difference = event_date - current_date
                days = "days" if time_difference.days != 1 else "day"

                print_colored(f"Next selective collection for {address} {house_number} is in {time_difference.days} {days} on {date_str}", GREEN)

                image_url = (
                    "https://mohubudapest.hu/storage/app/media/csempe%20k%C3%A9pek/"
                    "cropped-images/szelekt%C3%ADv%20kep-0-0-0-0-1728393471.jpg"
                )
                image_url = random.choice([image_url, image_url])

                if event_date > current_date:
                    if time_difference.days <= NOTIFICATION_PERIOD:
                        if time_difference.days == 1:
                            print_colored("Sending email one day before", BLUE)
                            send_email(
                                f"Szelektív hulladék holnap {address} {house_number} - {date_str}, {day}",
                                f"<h1>Szelektív hulladék {address} {house_number} holnap "
                                f"<b>({date_str}, {day})</b></h1>"
                                f"<img src='{image_url}' alt='Hulladékgazdálkodás' title='Hulladékgazdálkodás'>",
                                recipients,
                            )
                        else:
                            print_colored(f"Sending email {time_difference.days} days before", BLUE)
                            send_email(
                                f"Szelektív hulladék {address} {house_number} - {date_str}, {day}",
                                f"<h1>Szelektív hulladék {address} {house_number} in "
                                f"{time_difference.days} {days} <b>({date_str}, {day})</b></h1>",
                                recipients,
                            )
                    break
                elif event_date == current_date:
                    logger.info(f"Next 'Szelektív' on: {tds[2].get_text().strip()}")
                elif event_date < current_date:
                    logger.info(f"Last 'Szelektív' was on: {date_str}")
