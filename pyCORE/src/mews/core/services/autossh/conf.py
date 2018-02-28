'''
Configuration file for AutoSSH

Created on Feb 26, 2018

@author: Brian Ricks
'''

HOST = "10.176.149.20"
PORT = 2252
USERNAME = "coreuser"
PASSWORD = "P28c7RtO0"

# list of commands to execute
COMMAND_LIST = ["uptime", "ps aux", "df -m", "pwd", "ls -al"]
# number of commands to execute before terminating
COMMAND_COUNT = 5
