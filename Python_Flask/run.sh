nohup python3 -u FB_effort.py > FB_effort.log 2>&1 &
tail -200f ./FB_effort.log
