import time
import random
# lazy import, i know
from task_scheduler import *

# ---
#test jobs
# ---

def cpu_task(num, dur):
	print(f"  -> {num}: CPU work for {dur}s")
	start=time.time()
	# spin cpu
	while time.time()-start < dur:
		_ = sum([i*i for i in range(1000)])
	print(f"  -> {num}: Done!")
	return f"Res_{num}"

def io_task(num, sleep_t):
	print(f"  -> {num}: IO sleeping {sleep_t}s")
	time.sleep(sleep_t)
	print(f"  -> {num}: IO done")
	return f"IO_{num}"

def q_task(num):
	print(f"  -> {num}: Quick task")
	time.sleep(0.1)
	return f"Q_{num}"

def data_task(num, d_size):
	print(f"  -> {num}: processing {d_size} items")
	res=0
	for i in range(d_size): res+=random.randint(1,100)
	time.sleep(0.2)
	print(f"  -> {num}: processed, sum={res}")
	return res


def main():
	print("\n" + "#"*60)
	print("# MY TASK SCHEDULER - TEST SUITE")
	print("#"*60)
	
	# --- test 1: basic run ---
	if 1: # easy to toggle this test
		print("\n" + "="*60)
		print("TEST 1: Basic Test - 20 Mixed Tasks")
		print("="*60)
		
		s=Scheduler(n_threads=4)
		s.start()
		
		print("\nScheduling 20 tasks...")
		
		# 5 high
		for i in range(5):
			s.sched(
				fn=cpu_task,
				prio=Prio.hi,
				ag=(i+1, random.uniform(0.2,0.5))
			)
		
		# 8 med
		for i in range(8):
			s.sched(
				fn=io_task,
				prio=Prio.med,
				ag=(i+6, random.uniform(0.3,0.6))
			)
		
		# 7 low
		for i in range(7):
			s.sched(
				fn=data_task,
				prio=Prio.lo,
				ag=(i+14, random.randint(1000,5000))
			)
		
		print("\nAll tasks in. letting them run...\n")
		time.sleep(8)
		s.stop(wait=True)
		
		print("\n" + "="*60)
		print("STATS (TEST 1)")
		print("="*60)
		
		st=s.get_stats()
		print(f"Total Tasks: {st['total_tasks']}")
		print(f"Avg Wait: {st['avg_wait_time']:.4f} s")
		print(f"Avg Exec: {st['avg_execution_time']:.4f} s")
		print(f"Throughput: {st['throughput']:.2f} tasks/s")
		print(f"Avg CPU: {st['avg_cpu_usage']:.2f}%")
		print(f"\nPriority Breakdown:")
		print(f"  HIGH: {st['priority_breakdown']['HIGH']}")
		print(f"  MEDIUM: {st['priority_breakdown']['MEDIUM']}")
		print(f"  LOW: {st['priority_breakdown']['LOW']}")
		
		s.export(
			csv_f='tasks.csv',
			json_f='stats.json'
		)
		
		print("\n" + "="*60)
		print("Test 1 done. Check tasks.csv and stats.json")
		print("="*60)


	# --- test 2: pause/resume ---
	if 1:
		print("\n\n" + "="*60)
		print("TEST 2: Pause/Resume")
		print("="*60)
		
		s2=Scheduler(n_threads=3) 
		s2.start()
		
		print("\nScheduling 10 tasks...")
		for i in range(10):
			s2.sched(io_task, Prio.med, ag=(i+1,0.5))
		
		time.sleep(2) # let some run
		
		print("\n>>> PAUSING <<<")
		s2.pause()
		time.sleep(2)
		print("...paused... no tasks should run now")
		
		print("\n>>> RESUMING <<<")
		s2.resume()
		
		time.sleep(4) # let them finish
		s2.stop(wait=True)
		
		st2=s2.get_stats()
		print(f"\nCompleted {st2['total_tasks']} tasks")
		print("Pause/Resume test done.")


	# --- test 3: priority check ---
	if 1:
		print("\n\n" + "="*60)
		print("TEST 3: Priority Demo")
		print("="*60)
		
		s3=Scheduler(n_threads=2) 
		s3.start()
		
		print("\nScheduling LOW, then MED, then HIGH...")
		print("HIGH tasks should execute first!\n")
		
		for i in range(3): s3.sched(q_task, Prio.lo, ag=(f"LOW-{i+1}",))
		time.sleep(0.2)
		for i in range(3): s3.sched(q_task, Prio.med, ag=(f"MED-{i+1}",))
		time.sleep(0.2)
		for i in range(3): s3.sched(q_task, Prio.hi, ag=(f"HIGH-{i+1}",))
		
		time.sleep(5) # give time to finish
		s3.stop(wait=True)
		print("\nPriority test done.")


	# --- test 4: stress test ---
	# enabled this test for you
	if 1: 
		print("\n\n" + "="*60)
		print("TEST 4: Stress Test - 50 Tasks")
		print("="*60)
		
		s4=Scheduler(n_threads=6) 
		s4.start()
		
		print("\nScheduling 50 tasks...")
		prios=[Prio.hi, Prio.med, Prio.lo]
		for i in range(50):
			p=random.choice(prios)
			t_type=random.choice(['cpu','io','data'])
			
			if t_type=='cpu':
				s4.sched(cpu_task,p,ag=(i+1,0.2))
			elif t_type=='io':
				s4.sched(io_task,p,ag=(i+1,0.3))
			else:
				s4.sched(data_task,p,ag=(i+1,2000))
		
		print("All 50 tasks in. this might take a bit...\n")
		time.sleep(15)
		s4.stop(wait=True)
		
		st4=s4.get_stats()
		print("\n" + "="*60)
		print("STRESS TEST RESULTS")
		print("="*60)
		print(f"Completed: {st4['total_tasks']}/50 tasks")
		print(f"Avg Wait: {st4['avg_wait_time']:.4f}s")
		print(f"Throughput: {st4['throughput']:.2f} tasks/sec")
		
		s4.export(csv_f='stress.csv')


if __name__ == "__main__":
	main()
	print("\n\n" + "#"*60)
	print("# ALL TESTS FINISHED")
	print("#"*60)
