import uuid
import time
import threading
from queue import Queue as ThreadQueue
from multiprocessing import Process, Queue, MPQueue
from typing import Enum

class Status(Enum):
  CREATED = "created"
  RUNNING =  "running"
  PAUSED = "paused"
  STOPPED = "stopped"
  COMPLETE = "complete"


class Task(self, inp_state):
  self.id = str(uuid.uuid4())[:8]
  self.inp_state = inp_state
  self.status = Status.CREATED
  self.process = None
  self.start_time = None

class TaskQueue(self, name, ):
  self.id = str(uuid.uuid4)[:8]
  self.name = name
  self.tasks = ThreadQueue()
  
  def _worker(self):
    while True:
      if self.task.get() is None:
        break
      
        task.status = Status.RUNNING
        task.start_time = time.time()
        
        print(f"Task {task.id} is running")

        p = Process(
          
        )
      
      else:
        print(f"Queue with Id: {self.id}, Name: {self.name} has finished")
        #code of removing the queue from queue group and show ing output

class Buddy:
  def __init__(self, max_parallel=4):
    self.processes = {}
    self.queues = {}
    self.workers = {}
    
  def add_process(self, queue_name):
    q = self.queues[queue_name]
    
    
    