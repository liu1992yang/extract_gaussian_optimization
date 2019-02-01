#!/bin/bash

CKPT=$1
METHOD=$2
BASIS=$3
module load anaconda3_4.3.1

if [ -z "$CKPT" ]||[ -z "$METHOD" ]||[ -z "$BASIS" ]; then
  echo "Usage: ./extract_wrapper.sh Y/N(individual folder such as checkpoint_queue) new_functional new_basis" 
  echo "Y/N expected to indicate whether this is a checkpoint queue run, which indicates geometry opt jobs are individual folders"
  exit 1
fi

if [[ $CKPT = Y ]]; then
  DLIST=$(echo $(ls -d *_snap_*/))
else
  echo "regular optimization"
  DLIST=$(echo $(ls *_snap_*.log))
fi

if [ -f 'opted_gjf' ] || [ -f 'not_done' ]; then
  rm -r 'opted_gjf'
  rm -r 'not_done'
fi


PYTHON_CKPT="$CKPT" PYTHON_DLIST="$DLIST" PYTHON_METHOD="$METHOD" PYTHON_BASIS="$BASIS" /gscratch/sw/anaconda-4.3.1/python3/bin/python3.6 - << END 

import glob, os, subprocess,sys

def get_general_parameters():
  CKPT = os.environ['PYTHON_CKPT']
  DLIST = os.environ['PYTHON_DLIST']
  METHOD = os.environ['PYTHON_METHOD']
  BASIS = os.environ['PYTHON_BASIS']
  return CKPT, DLIST, METHOD, BASIS

def find_ckpt_log(dlist):
  ckpt_list = []
  for ckptdir in dlist.split():
    list_of_logs = glob.iglob(os.path.join(ckptdir,'*.log'))
    latest_log = max(list_of_logs,key=os.path.getmtime)
    log_fn = os.path.basename(latest_log)
    subprocess.call(['cp', latest_log, log_fn])
    ckpt_list.append(log_fn)
  return ckpt_list



if __name__ == '__main__':
  ckpt, dlist, method, basis = get_general_parameters()
  if ckpt == 'Y': 
    log_files = find_ckpt_log(dlist)
  else:
    log_files = dlist.split()
  print(log_files)
  for log in log_files:
    subprocess.call(["python", "extract_gaussian_opt.py", log, method, basis])
END

echo "please see dir 'opted_gjf' for optimized structures and energys"
echo "please see dir 'not_done' for not optimized structures and filelist"
