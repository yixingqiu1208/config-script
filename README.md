# config-script

Ex:

1. Apply full config (mode 1):
python3 config-script.py -a \<xxx.xxx.xxx.xxx\> -u \<username\> -p \<password\> -m 1 -f \<full-config-filename\>

2. Additional config (mode 2):
python3 config-script.py -a \<xxx.xxx.xxx.xxx\> -u \<username\> -p \<password\> -m 2 -f \<additional-config-filename\> -i yes

Please enter the additional configs. End the input with "end":
ssh server rate-limit 250
ssh server session-limit 99
end
Config input finished


