import time

class PerfTimer:
    _start_time = None
    _count = 0
    _sum_elapsed_ns = 0

    @staticmethod
    def begin():
        PerfTimer._start_time = time.perf_counter_ns()

    @staticmethod
    def stop():
        end_time = time.perf_counter_ns()
        elapsed = end_time - PerfTimer._start_time

        PerfTimer._count += 1
        PerfTimer._sum_elapsed_ns += elapsed

        print(f"Operation took {elapsed} ns")

        # Every 10 stops, print the average for those 10 and reset counters
        if PerfTimer._count % 10 == 0:
            avg = PerfTimer._sum_elapsed_ns / PerfTimer._count
            print(f"Average of last 10 operations: {avg} ns")
            # PerfTimer._count = 0
            # PerfTimer._sum_elapsed_ns = 0
