from merge_integration.helper_functions import api_log


def start():
    api_log(msg="CRON:INVOICE : Starting Invoice POST cron job")
    # scheduler = BackgroundScheduler()
    # scheduler.add_job(main, "interval", minutes=1)
    # scheduler.start()
