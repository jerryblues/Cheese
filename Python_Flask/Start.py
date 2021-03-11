from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz
import os


def job():
    print("=== current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")
    os.system("sudo kill -9 `ps -ef|grep FB_effort.py |grep -v grep|awk '{print$2}'`")
    os.system('python3 FB_effort.py')


scheduler = BlockingScheduler()
scheduler.add_job(job, 'cron', max_instances=65535, day_of_week='mon,tue,wed,thu,fri', hour='8-20', minute='0, 30',
                  timezone="Asia/Shanghai", next_run_time=datetime.now())
scheduler.start()
