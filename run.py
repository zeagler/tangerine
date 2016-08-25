"""
This module is a class used to represent a run.
"""
from time import time
from datetime import datetime
from json import dumps

from postgres_connection import PGconnection
global postgres
postgres = PGconnection()

class Run(object):
    """
    """
    def __init__(self, columns, values):
        """
        Set the initial attributes of this task object

        Args:
            input: the results of a `SELECT *` query on the task table
        """
        for i in range(len(values)):
            setattr(self, columns[i][0], values[i])
        
        # Set the JSON response
        setattr(self, "json", dumps(self.__dict__))
    
    def update(self, column, value):
        """
        Update the value of a column in this run's row

        Args
            column: The column that will be updated
            value: The new value to be set
        """
        global postgres
        
        if not column:
            return None

        setattr(self, column, value)
        query = "UPDATE task_history SET "+column+"="
        
        if value == None:
            query += "NULL"
        else:
            query += "'"+str(value)+"'"
        
        cur = postgres.conn.cursor()
        try:
            cur.execute(query + " WHERE run_id='"+str(self.run_id)+"';")
            postgres.conn.commit()
            return True
        except:
            postgres.conn.rollback()
            return False
        
    def insert_stats(self, stats):
        query = "UPDATE task_history SET" + \
              " time_scale = time_scale || '{" + str(stats['time']) + "}'," + \
              " cpu_history = cpu_history || '{" + str(stats['cpu']) + "}'," + \
              " memory_history = memory_history || '{" + str(stats['memory']) + "}'," + \
              " network_in_history = network_in_history || '{" + str(stats['rx_bytes']) + "}'," + \
              " network_out_history = network_out_history || '{" + str(stats['tx_bytes']) + "}'," + \
              " disk_in_history = disk_in_history || '{" + str(stats['read_bytes']) + "}'," + \
              " disk_out_history = disk_out_history || '{" + str(stats['write_bytes']) + "}'" + \
              " WHERE run_id='" + str(self.run_id) + "';"

        cur = postgres.conn.cursor()
        
        try:
            cur.execute(query)
            postgres.conn.commit()
            return True
        except:
            postgres.conn.rollback()
            return False
        
    def finish(self, exit_code):
        """
        Set the permanent values of this run after it has completed
        """
        
        # Set the result state based on the exit code
        self.update("result_exitcode", exit_code)
        if exit_code == "stopped" or exit_code == "host failure":
            self.update("result_state", exit_code)
        elif exit_code == 0:
            self.update("result_state", "success")
        else:
            self.update("result_state", "failed")
            
            
        # Log the finish time
        self.update("run_finish_time", int(time()))
        self.update("run_finish_time_str", datetime.fromtimestamp(self.run_finish_time).strftime('%I:%M%p %B %d, %Y'))
        
        
        # Calculate the elapsed time
        start = datetime.fromtimestamp(self.run_start_time)
        finish = datetime.fromtimestamp(self.run_finish_time)
        elapsed_seconds = (finish-start).total_seconds()
        
        elapsed_hours=int(elapsed_seconds/60/60)
        elapsed_minutes=int((elapsed_seconds-elapsed_hours*60*60)/60)
        
        elapsed_string = ""
        if elapsed_hours:
            elapsed_string += str(elapsed_hours) + " hours"
            
        if elapsed_minutes:
            elapsed_string += " " + str(elapsed_minutes) + " minutes"
            
        self.update("elapsed_time", elapsed_string)
