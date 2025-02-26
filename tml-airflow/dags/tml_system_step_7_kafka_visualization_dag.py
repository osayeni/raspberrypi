from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from airflow.decorators import dag, task
import sys
import subprocess
import tsslogging
import os
import time
import random

sys.dont_write_bytecode = True
######################################## USER CHOOSEN PARAMETERS ########################################
default_args = {
  'topic' : 'iot-preprocess-data',    # <<< *** Separate multiple topics by a comma - Viperviz will stream data from these topics to your browser
  'secure': '1',   # <<< *** 1=connection is encrypted, 0=no encryption
  'offset' : '-1',    # <<< *** -1 indicates to read from the last offset always
  'append' : '0',   # << ** Do not append new data in the browser
  'rollbackoffset' : '500', # *************** Rollback the data stream by rollbackoffset.  For example, if 500, then Viperviz wll grab all of the data from the last offset - 500
}

######################################## DO NOT MODIFY BELOW #############################################

# Instantiate your DAG
@dag(dag_id="tml_system_step_7_kafka_visualization_dag", default_args=default_args, tags=["tml_system_step_7_kafka_visualization_dag"], schedule=None,catchup=False)
def startstreaming():    
  def empty():
      pass
dag = startstreaming()

def windowname(wtype,vipervizport,sname,dagname):
    randomNumber = random.randrange(10, 9999)
    wn = "viperviz-{}-{}-{}={}".format(wtype,randomNumber,sname,dagname)
    with open("/tmux/vipervizwindows_{}.txt".format(sname), 'a', encoding='utf-8') as file: 
      file.writelines("{},{}\n".format(wn,vipervizport))
    
    return wn

def startstreamingengine(**context):
        repo=tsslogging.getrepo()  
        try:
          tsslogging.tsslogit("Visualization DAG in {}".format(os.path.basename(__file__)), "INFO" )                     
          tsslogging.git_push("/{}".format(repo),"Entry from {}".format(os.path.basename(__file__)),"origin")    
        except Exception as e:
            #git push -f origin main
            os.chdir("/{}".format(repo))
            subprocess.call("git push -f origin main", shell=True)
    
        sd = context['dag'].dag_id
        sname=context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_solutionname".format(sd))
        chip = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_chip".format(sname)) 
        vipervizport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_VIPERVIZPORT".format(sname)) 
        solutionvipervizport = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_SOLUTIONVIPERVIZPORT".format(sname)) 
        tss = context['ti'].xcom_pull(task_ids='step_1_solution_task_getparams',key="{}_TSS".format(sname)) 
    
        topic = default_args['topic']
        secure = default_args['secure']
        offset = default_args['offset']
        append = default_args['append']
        rollbackoffset = default_args['rollbackoffset']
                
        ti = context['task_instance']
        ti.xcom_push(key="{}_topic".format(sname),value=topic)
        ti.xcom_push(key="{}_secure".format(sname),value="_{}".format(secure))
        ti.xcom_push(key="{}_offset".format(sname),value="_{}".format(offset))
        ti.xcom_push(key="{}_append".format(sname),value="_{}".format(append))
        ti.xcom_push(key="{}_chip".format(sname),value=chip)
        ti.xcom_push(key="{}_rollbackoffset".format(sname),value="_{}".format(rollbackoffset))
    
        # start the viperviz on Vipervizport
        # STEP 5: START Visualization Viperviz 
        wn = windowname('visual',vipervizport,sname,sd)
        subprocess.run(["tmux", "new", "-d", "-s", "{}".format(wn)])
        subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "cd /Viperviz", "ENTER"])
        if tss[1:] == "1":
          subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "/Viperviz/viperviz-linux-{} 0.0.0.0 {}".format(chip,vipervizport[1:]), "ENTER"])            
        else:    
          subprocess.run(["tmux", "send-keys", "-t", "{}".format(wn), "/Viperviz/viperviz-linux-{} 0.0.0.0 {}".format(chip,solutionvipervizport[1:]), "ENTER"])
