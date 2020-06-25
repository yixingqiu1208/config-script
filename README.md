# config-script

root@vm:~/config-script$ python3 config-script.py -h
usage: config-script.py [-h] [-u USERNAME] [-p PASSWORD] -a HOST [-m MODE]
                        [-f FILENAME] [-c CONFIG]

Config script

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --user USERNAME
  -p PASSWORD, --password PASSWORD
                        password
  -a HOST, --host HOST  Host IP address
  -m MODE, --mode MODE  1: Replace config; 2: Add config
  -f FILENAME, --filename FILENAME
                        Path and name of the file which contains the configs.
  -c CONFIG, --config CONFIG
                        Additional config
root@vm:~/config-script$

Ex:
1. Replace the config (mode 1):
  python3 config-script.py -a <xxx.xxx.xxx.xxx> -u <username> -p <password> -m 1 -f <full-config-filename>
  
2. Add the config (mode 2):
  python3 config-script.py -a <xxx.xxx.xxx.xxx> -u <username> -p <password> -m 2 -f <additional-config-filename>
