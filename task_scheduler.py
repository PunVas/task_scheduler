# my task scheduler
import threading as th
import queue
import time
import json
import csv
from enum import IntEnum
from dataclasses import dataclass, field
import psutil
from datetime import datetime

# priority levels
class Prio(IntEnum):
	hi=1
	med=2
	lo=3

@dataclass
class Job:
	# a job to do
	id: int
	prio: Prio
	fn: callable
	ag: tuple = field(default_factory=tuple)
	kw: dict = field(default_factory=dict)
	
	# tracking
	t_create: float = field(default_factory=time.time)
	t_start: float = None
	t_end: float = None
	
	def __lt__(self, other):
		# for the priority queue
		if self.prio!=other.prio:
			return self.prio<other.prio
		return self.t_create<other.t_create
	
	def run(self):
		self.t_start=time.time()
		try:
			res=self.fn(*self.ag,**self.kw)
			self.t_end=time.time()
			return res
		except Exception as e:
			self.t_end=time.time()
			raise e
	
	def wait_t(self):
		if self.t_start:
			return self.t_start-self.t_create
		return None
	
	def run_t(self):
		if self.t_start and self.t_end:
			return self.t_end-self.t_start
		return None


class Stats:
	# keep track of stuff
	def __init__(self):
		self.lk=th.Lock() 
		self.done_jobs=[]
		self.cpu=[]
		self.cpu_t=[]
		
	def add_job(self, j: Job):
		with self.lk:
			self.done_jobs.append(j)
	
	def add_cpu(self, u: float):
		with self.lk:
			self.cpu.append(u)
			self.cpu_t.append(time.time())
	
	def get_stats(self):
		with self.lk:
			if not self.done_jobs:
				return {
					"total_tasks": 0, "avg_wait_time": 0, "avg_execution_time": 0,
					"throughput": 0, "avg_cpu_usage": 0
				}
			
			w_times=[t.wait_t() for t in self.done_jobs if t.wait_t()]
			avg_w=sum(w_times)/len(w_times) if w_times else 0
			
			r_times=[t.run_t() for t in self.done_jobs if t.run_t()]
			avg_r=sum(r_times)/len(r_times) if r_times else 0
			
			if self.done_jobs:
					t_first=self.done_jobs[0].t_create
					t_last=self.done_jobs[-1].t_end or time.time()
					dur=t_last-t_first
					thru=len(self.done_jobs)/dur if dur>0 else 0
			else:
			  thru=0
			
			avg_cpu=sum(self.cpu)/len(self.cpu) if self.cpu else 0
			
			p_count={
				"HIGH": sum(1 for t in self.done_jobs if t.prio==Prio.hi),
				"MEDIUM": sum(1 for t in self.done_jobs if t.prio==Prio.med),
				"LOW": sum(1 for t in self.done_jobs if t.prio==Prio.lo)
			}
			
			return {
				"total_tasks": len(self.done_jobs),
				"avg_wait_time": avg_w,
				"avg_execution_time": avg_r,
				"throughput": thru,
				"avg_cpu_usage": avg_cpu,
				"priority_breakdown": p_count
			}
	
	def to_csv(self, fname: str):
		with self.lk:
			with open(fname,'w',newline='') as f:
				w=csv.writer(f)
				w.writerow(['Task_ID','Priority','Wait_Time','Execution_Time','Created','Started','Ended'])
				
				for j in self.done_jobs:
					w.writerow([
						j.id,
						j.prio.name,
						f"{j.wait_t():.4f}" if j.wait_t() else "N/A",
						f"{j.run_t():.4f}" if j.run_t() else "N/A",
						datetime.fromtimestamp(j.t_create).strftime('%H:%M:%S.%f'),
						datetime.fromtimestamp(j.t_start).strftime('%H:%M:%S.%f') if j.t_start else "N/A",
						datetime.fromtimestamp(j.t_end).strftime('%H:%M:%S.%f') if j.t_end else "N/A"
					])
	
	def to_json(self, fname: str):
		s=self.get_stats()
		with open(fname,'w') as f:
			json.dump(s,f,indent=2)


class Pool:
	# the workers
	def __init__(self, n_threads: int, stats: Stats):
		self.n_threads=n_threads
		self.stats=stats
		self.q=queue.PriorityQueue()
		
		self.lk=th.Lock()
		self.cond=th.Condition(self.lk)
		
		self.run_flag=False
		self.paused=False
		self.stop_flag=False
		
		self.threads=[]
		self.cpu_mon=None
		
	def start(self):
		self.run_flag=True
		self.stop_flag=False
		
		for i in range(self.n_threads):
			t=th.Thread(target=self._loop, name=f"W-{i}")
			t.daemon=True # so it dies when main dies
			t.start()
			self.threads.append(t)
		
		self.cpu_mon=th.Thread(target=self._mon_cpu)
		self.cpu_mon.daemon=True
		self.cpu_mon.start()
		
		print(f"[Pool] Started {self.n_threads} workers")
	
	def _loop(self):
		# this is the loop for threads
		while not self.stop_flag:
			job=None
			
			with self.cond:
				# wait if paused or no jobs
				while self.paused or (self.q.empty() and not self.stop_flag):
					self.cond.wait(timeout=0.1) 
					if self.stop_flag:
						return
				
				if not self.q.empty():
					try:
						job=self.q.get_nowait()
					except queue.Empty:
						continue # someone else got it
			
			# run the job outside the lock!
			if job:
				try:
					print(f"[{th.current_thread().name}] Run Task-{job.id} (Prio: {job.prio.name})")
					job.run()
					print(f"[{th.current_thread().name}] Done Task-{job.id}")
					self.stats.add_job(job)
				except Exception as e:
					print(f"[{th.current_thread().name}] Task-{job.id} FAILED: {e}")
				finally:
					self.q.task_done()
	
	def _mon_cpu(self):
		p=psutil.Process()
		while not self.stop_flag:
			try:
				cpu_p=p.cpu_percent(interval=0.5)
				self.stats.add_cpu(cpu_p)
			except:
				pass
			time.sleep(1)
	
	def add_job(self, job: Job):
		with self.cond:
			self.q.put(job)
			self.cond.notify() # wake up one worker
	
	def pause(self):
		with self.cond:
			self.paused=True
			print("[Pool] Paused")
	
	def resume(self):
		with self.cond:
			self.paused=False
			self.cond.notify_all()
			print("[Pool] Resumed")
	
	def stop(self, wait=True):
		print("[Pool] Shutting down...")
		
		with self.cond:
			self.stop_flag=True
			self.cond.notify_all()
		
		if wait:
			self.q.join() # wait for all jobs
			
			for t in self.threads:
				t.join(timeout=5)
			
			if self.cpu_mon:
				self.cpu_mon.join(timeout=2)
		
		print("[Pool] Shutdown complete")


class Scheduler:
	# the main boss
	def __init__(self, n_threads: int=4):
		self.stats=Stats()
		self.pool=Pool(n_threads, self.stats)
		self.task_id_ctr=0
		self.lk=th.Lock()
		
	def start(self):
		self.pool.start()
	
	def sched(self, fn: callable, prio: Prio=Prio.med, 
					 ag: tuple=(), kw: dict=None):
		with self.lk:
			self.task_id_ctr+=1
			task_id=self.task_id_ctr
		
		job=Job(
			id=task_id,
			prio=prio,
			fn=fn,
			ag=ag,
			kw=kw or {}
		)
		
		self.pool.add_job(job)
		print(f"[Scheduler] Scheduled Task-{task_id} with {prio.name} prio")
		return task_id
	
	def pause(self):
		self.pool.pause()
	
	def resume(self):
		self.pool.resume()
	
	def stop(self, wait=True):
		self.pool.stop(wait)
	
	def get_stats(self):
		return self.stats.get_stats()
	
	def export(self, csv_f: str=None, json_f: str=None):
		if csv_f:
			self.stats.to_csv(csv_f)
			print(f"[Scheduler] Metrics saved to {csv_f}")
		
		if json_f:
			self.stats.to_json(json_f)
			print(f"[Scheduler] Stats saved to {json_f}")