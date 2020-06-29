# config-script

Config Script:<br/>
  step 1 - connect to router and get the running-config<br/>
  step 2 - (Mode 1) open file with full config; (Mode 2) open file or/and manual input with added changes<br/>
  step 3 - (Mode 1) send (scp) full config to router; (Mode 2) send config from "show run" + added changes<br/>
  step 4 - load config that was sent<br/>
  step 5 - commit replace<br/>
  step 6 - get the running config after changes<br/>
  step 7 - display diff on console<br/>


Ex:

1. Apply full config (mode 1):<br/>
python3 config-script.py -a \<xxx.xxx.xxx.xxx\> -u \<username\> -p \<password\> -m 1 -f \<full-config-filename\>

2. Additional config (mode 2):<br/>
python3 config-script.py -a \<xxx.xxx.xxx.xxx\> -u \<username\> -p \<password\> -m 2 -f \<additional-config-filename\> -i yes<br/>
Please enter the additional configs. End the input with "end":<br/>
ssh server rate-limit 250<br/>
ssh server session-limit 99<br/>
end<br/>
Config input finished<br/>


