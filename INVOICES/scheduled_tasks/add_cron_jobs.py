from apscheduler.schedulers.background import BackgroundScheduler

from merge_integration.helper_functions import api_log
from .daily_get_merge_invoice import main


def start():
    api_log(msg="Starting Invoice Cron Jobs")
    scheduler = BackgroundScheduler()
    scheduler.add_job(main, "interval", minutes=1)
    scheduler.start()
