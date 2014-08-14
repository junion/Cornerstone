import subprocess

# subprocess.call("python ../env/DSTCV1/offline_tracker.py --dataset=train3.half2 --dataroot=/Users/junion/Development/DSTC-DATA --asrmode=live --trackfile=../log/lme-track-tr3.json --haslabel=yes", shell=True)
# subprocess.call("python ../env/DSTCV1/score.py --dataset=train3.half2 --dataroot=/Users/junion/Development/DSTC-DATA --trackfile=../log/lme-track-tr3.json --scorefile=../log/lme-score-tr3.csv", shell=True)
# subprocess.call("python ../env/DSTCV1/report.py --scorefile=../log/lme-score-tr3.csv --reportfile=../log/lme-report-tr3.txt", shell=True)

# subprocess.call("python ../env/DSTCV1/offline_tracker.py --dataset=train2.half2 --dataroot=/Users/junion/Development/DSTC-DATA --asrmode=live --trackfile=../log/lme-track-tr2.json --haslabel=yes", shell=True)
# subprocess.call("python ../env/DSTCV1/score.py --dataset=train2.half2 --dataroot=/Users/junion/Development/DSTC-DATA --trackfile=../log/lme-track-tr2.json --scorefile=../log/lme-score-tr2.csv", shell=True)
# subprocess.call("python ../env/DSTCV1/report.py --scorefile=../log/lme-score-tr2.csv --reportfile=../log/lme-report-tr2.txt", shell=True)

subprocess.call("python ../env/DSTCV1/offline_tracker.py --dataset=train1a.half2 --dataroot=/Users/junion/Development/DSTC-DATA --asrmode=live --trackfile=../log/lme-track-tr1a.json --haslabel=yes", shell=True)
subprocess.call("python ../env/DSTCV1/score.py --dataset=train1a.half2 --dataroot=/Users/junion/Development/DSTC-DATA --trackfile=../log/lme-track-tr1a.json --scorefile=../log/lme-score-tr1a.csv", shell=True)
subprocess.call("python ../env/DSTCV1/report.py --scorefile=../log/lme-score-tr1a.csv --reportfile=../log/lme-report-tr1a.txt", shell=True)
