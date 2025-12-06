"""Simple performance timing utility"""

import time

class Timer:
    _start_time = None
    _count = 0
    _sum_elapsed_ns = 0

    @staticmethod
    def begin():
        Timer._start_time = time.perf_counter_ns()

    @staticmethod
    def stop():
        end_time = time.perf_counter_ns()
        elapsed = end_time - Timer._start_time

        Timer._count += 1
        Timer._sum_elapsed_ns += elapsed

        print(f"Operation took {elapsed} ns")

        # Every 10 stops, print the average for those 10 and reset counters
        if Timer._count % 10 == 0:
            avg = Timer._sum_elapsed_ns / Timer._count
            print(f"Average of last 10 operations: {avg} ns")
            # PerfTimer._count = 0
            # PerfTimer._sum_elapsed_ns = 0
