#!/bin/sh
# Launches the eMews SingleServiceClient with local configuration (useful for testing).
python singleserviceclient.py --node_name=client --sys_config='../system-local.yml' $1
