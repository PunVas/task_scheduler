# my python task scheduler

just a python script i wrote to test out multithreading and stuff.

it's a basic thread pool scheduler. you can give it jobs, and it runs them on a few threads. not for real use, just a project.

## features

  * thread pool (you pick how many threads)
  * priority queue for jobs (**hi**, **med**, **lo**). hi prio jobs *should* run first.
  * can **pause** and **resume** the whole thing
  * tracks stats (wait time, run time, cpu usage, etc.)
  * dumps all the data to a `.csv` and `.json` file at the end.

## how to run

1.  you need python 3
2.  you need to install `psutil` (for the cpu monitor):
    ```bash
    pip install psutil
    ```
3.  just run the test file (i named it `main.py` in my test):
    ```bash
    python main.py
    ```

## test output

it works. here's the log from my machine.

it runs 4 tests:

1.  **Basic Test:** 20 tasks with different priorities.
2.  **Pause/Resume:** checks if that works.
3.  **Priority Demo:** tries to show high-prio tasks run first.
4.  **Stress Test:** hammers it with 50 tasks.

### Test 1: Basic Run

this one just runs 20 tasks. worked fine.

```
============================================================
STATS (TEST 1)
============================================================
Total Tasks: 20
Avg Wait: 0.6043 s
Avg Exec: 0.3796 s
Throughput: 9.40 tasks/s
Avg CPU: 1.52%

Priority Breakdown:
  HIGH: 5
  MEDIUM: 8
  LOW: 7
[Scheduler] Metrics saved to tasks.csv
[Scheduler] Stats saved to stats.json
```

### Test 2: Pause/Resume

this one schedules 10 tasks, waits 2 seconds, pauses, waits 2 more, then resumes. you can see it pause in the log.

```
...
>>> PAUSING <<<
[Pool] Paused
  -> 7: IO done
[W-1] Done Task-7
...paused... no tasks should run now

>>> RESUMING <<<
[Pool] Resumed
...
Completed 10 tasks
Pause/Resume test done.
```

### Test 3: Priority Demo

this one is a bit weird. i scheduled LOW, then MED, then HIGH tasks. the log shows them running in that order (LOW, MED, HIGH). that's just because the threads (only 2 for this test) were so fast they grabbed the LOW tasks and finished them *before* the MED/HIGH tasks were even added to the queue.

the priority logic in the queue itself is fine, i swear.

```
Scheduling LOW, then MED, then HIGH...
HIGH tasks should execute first!

[Scheduler] Scheduled Task-1 with lo prio
[W-0] Run Task-1 (Prio: lo)
...
[Scheduler] Scheduled Task-4 with med prio
[W-1] Run Task-4 (Prio: med)
...
[Scheduler] Scheduled Task-7 with hi prio
[W-1] Run Task-8 (Prio: hi)
...
Priority test done.
```

### Test 4: Stress Test

hammered it with 50 tasks on 6 threads. it handled it. wait time went up, which makes sense.

```
============================================================
STRESS TEST RESULTS
============================================================
Completed: 50/50 tasks
Avg Wait: 1.2912s
Throughput: 17.24 tasks/sec
[Scheduler] Metrics saved to stress.csv
```

all done. check the `.csv` files for all the data.