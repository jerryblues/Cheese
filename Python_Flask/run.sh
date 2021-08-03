nohup python3 -u ET_statistics.py > ET_statistics.log 2>&1 &
tail -200f ./ET_statistics.log
