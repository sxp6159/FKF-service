# -*- coding: utf-8 -*-
"""
Container entrypoint: schedules FKF.run() to fire once a day at
FKF_RUN_TIME (24h "HH:MM", default "09:24", interpreted in the
container's local time -> set TZ env var to your zone, e.g. TZ=Europe/Budapest).
"""

import logging
import os
import time

import schedule

from fkf import FKF

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fkf.scheduler")


def job():
    try:
        FKF().run()
    except Exception:
        logger.exception("Unhandled error during FKF run")


def main():
    run_time = os.environ.get("FKF_RUN_TIME", "09:24")
    run_on_start = os.environ.get("FKF_RUN_ON_START", "false").lower() == "true"

    logger.info("FKF scheduler starting. Daily run time: %s (container TZ: %s)",
                run_time, os.environ.get("TZ", "not set - defaults to UTC"))

    schedule.every().day.at(run_time).do(job)

    if run_on_start:
        logger.info("FKF_RUN_ON_START=true, running once immediately")
        job()

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
