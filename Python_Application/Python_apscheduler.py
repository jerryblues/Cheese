# coding=utf-8
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import pytz


def job():
    print("=== current time:", datetime.now(pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S"), "===")


# 定时任务 每周一到周五 每天8点到20点 每整点0分 运行一次
scheduler = BlockingScheduler()
scheduler.add_job(job, 'cron', max_instances=65535, day_of_week='mon,tue,wed,thu,fri', hour='8-20', minute='0', timezone="Asia/Shanghai",
                  next_run_time=datetime.now())
scheduler.start()
