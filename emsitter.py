# etherminer.exe wrapper
# restart when speed drop down
# restart when exit unexpectedly
#       on Windows, need to disable dialog of Windows Error Reporting
#
# HouYu Li <lihouyu@phpex.net>
#
# You can use it freely.
# >> Happy Mining <<

import os, sys, subprocess, re, signal

from datetime import datetime

######## Change following variables to match your env ########

## etherminer.exe path and parameters
exe_miner       = "<path>\\to\\ethminer.exe"
opt_miner_path  = "stratum+tls12://<wallet>.<rig>@<pool_server>:<port>"
opt_miner_ext   = "--exit -RH -HWMON 1 --farm-recheck 2000 -G"

## When speed drop down far more than the threshold (Mh/s) after limit counts,
##  subprocess will be killed and restarted.
speed_drop_threshold = 2
speed_drop_threshold_limit = 10

######## // ########

######## DO NOT CHANGE ANYTHING BELOW ########

## Ctrl-C handler
def signal_handler(signal, frame):
    print('exiting...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

## Setup environment variables for miner
miner_env = os.environ.copy()
miner_env["GPU_FORCE_64BIT_PTR"]        = str(0)
miner_env["GPU_MAX_HEAP_SIZE"]          = str(100)
miner_env["GPU_USE_SYNC_OBJECTS"]       = str(1)
miner_env["GPU_MAX_ALLOC_PERCENT"]      = str(100)
miner_env["GPU_SINGLE_ALLOC_PERCENT"]   = str(100)

## Compose miner command
miner = " ".join([exe_miner, "-P", opt_miner_path, opt_miner_ext])

## The infinit loop to keep the miner running forever
while True:
    ###
    normal_speed = 0.00
    speed_drop_count = 0
    ### The miner subprocess, merging STDERR to STDOUT
    miner_proc = subprocess.Popen(miner, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, env = miner_env)
    ### Read miner output
    for miner_out in miner_proc.stdout:
        ### Only match speed output, ignoring all other output lines
        miner_out_re = re.match(r"^m\s+\d\d:\d\d:\d\d\|[^\s]+\s+\|\s+(Speed\s+([^\s]+)\s+Mh\/s).+", 
            miner_out.decode("utf-8").strip(), re.M|re.I)
        ### Get the current local time
        str_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ### If we find a output line with speed
        if miner_out_re:
            ### Get speed out from regex match
            str_speed = miner_out_re.group(1)
            val_speed = miner_out_re.group(2)
            ###
            print("\"%s\",\"%s\"" % (str_time, val_speed))

            ### Compare speed change to drop threshold
            curr_speed = float(val_speed)
            if normal_speed - curr_speed > speed_drop_threshold:
                ### Speed drop is more than threshold
                ### Add one speed drop count
                speed_drop_count += 1
                ###
                print("\"%s\",\"speed down\"" % str_time)
                ### Compare speed drop count to drop limit
                if speed_drop_count >= speed_drop_threshold_limit:
                    ### Speed drop count is more than limit
                    ### Then we make sure that the miner is slowing down
                    ### Kill it and it will run again in next loop
                    miner_proc.kill()
                    ###
                    print("\"%s\",\"low speed restart\"" % str_time)
            else:
                ### Speed is changing in acceptable range
                ### Reset speed drop count
                speed_drop_count = 0
                ### Set current speed as a reference speed for later speed reports
                normal_speed = curr_speed
        else:
            pass
