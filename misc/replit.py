import subprocess

# A plague upon Replit and all who have built it
replit_cmd = "killall -q python3 > /dev/null 2>&1; pip install -r requirements.txt && ./run"
subprocess.run(replit_cmd, shell=True)
