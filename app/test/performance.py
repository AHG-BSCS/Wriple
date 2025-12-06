"""Simple performance testing utility"""

import time

import numpy as np
import psutil

def total_cpu_time(p):
    t = p.cpu_times()
    total = getattr(t, "user", 0.0) + getattr(t, "system", 0.0)
    return total

def get_system_performance(duration = 60.0, sample_interval = 0.5, sleep_before = 2.0):
    """Measure CPU, memory, and network usage over a period of time."""
    if duration <= 0 or sample_interval <= 0:
        raise ValueError('duration and sample_interval must be positive')
    
    process = psutil.Process()
    total_mem_bytes = psutil.virtual_memory().total
    
    sample_count = max(1, int(duration / sample_interval))
    cpu_samples = np.empty(sample_count, dtype=np.float64)
    cpu_count = psutil.cpu_count(logical=False)
    mem_pct_samples = np.empty(sample_count, dtype=np.float64)
    mem_mb_samples = np.empty(sample_count, dtype=np.float64)
    net_up_samples = np.empty(sample_count, dtype=np.float64)
    net_down_samples = np.empty(sample_count, dtype=np.float64)

    time.sleep(sleep_before)
    print(f'PID: {process.pid}')
    print(f'CPU: {cpu_count}')
    print('Starting performance measurement...')

    # psutil.cpu_percent()
    # process.cpu_percent(interval=None)
    prev_net = psutil.net_io_counters()
    prev_time = time.perf_counter()

    # Baseline
    cpu_before = total_cpu_time(process)
    for child in process.children(recursive=True):
        cpu_before += total_cpu_time(child)

    end_time = prev_time + duration
    idx = 0
    while idx < sample_count:
        remaining = end_time - time.perf_counter()
        if remaining <= 0:
            break
        time.sleep(sample_interval)
        # now = time.perf_counter()
        # dt = max(now - prev_time, 1e-9)

        # cpu_samples[idx] = psutil.cpu_percent()
        # cpu_usage = process.cpu_percent(interval=None)
        # cpu_samples[idx] = cpu_usage / cpu_count

        cpu_after = total_cpu_time(process)
        for child in process.children(recursive=True):
            cpu_after += total_cpu_time(child)

        delta_cpu = cpu_after - cpu_before
        cpu_before = cpu_after
        if delta_cpu < 0:
            # safety: clock wrap or reading issue
            delta_cpu = 0.0

        cpu_samples[idx] = (delta_cpu / sample_interval) / cpu_count * 100.0
        # print(f'CPU Sample {idx}: {cpu_samples[idx]:.2f}%')

        rss_bytes = process.memory_info().rss
        mem_pct_samples[idx] = rss_bytes / total_mem_bytes * 100.0
        mem_mb_samples[idx] = rss_bytes / (1024.0 ** 2)

        # net = psutil.net_io_counters()
        # net_up_samples[idx] = max(0.0, net.bytes_sent - prev_net.bytes_sent) / dt
        # net_down_samples[idx] = max(0.0, net.bytes_recv - prev_net.bytes_recv) / dt

        # prev_net = net
        # prev_time = now
        idx += 1

    if idx == 0:
        print('No samples collected.')
        return

    # Set the cpu samples that exceed 100% to 100%
    for i in range(idx):
        if cpu_samples[i] > 100.0:
            cpu_samples[i] = 100.0

    cpu_samples = cpu_samples[:idx]
    mem_pct_samples = mem_pct_samples[:idx]
    mem_mb_samples = mem_mb_samples[:idx]
    net_up_samples = net_up_samples[:idx]
    net_down_samples = net_down_samples[:idx]

    cpu_avg = float(cpu_samples.mean())
    cpu_max = float(cpu_samples.max())
    cpu_std = float(cpu_samples.std(ddof=1)) if idx > 1 else 0.0

    mem_pct_avg = float(mem_pct_samples.mean())
    mem_pct_max = float(mem_pct_samples.max())
    mem_pct_std = float(mem_pct_samples.std(ddof=1)) if idx > 1 else 0.0

    mem_mb_avg = float(mem_mb_samples.mean())
    mem_mb_max = float(mem_mb_samples.max())
    mem_mb_std = float(mem_mb_samples.std(ddof=1)) if idx > 1 else 0.0

    # net_up_avg = float(net_up_samples.mean()) / (1024**2)
    # net_up_max = float(net_up_samples.max()) / (1024**2)
    # net_up_std = float(net_up_samples.std(ddof=1)) / (1024**2) if idx > 1 else 0.0

    # net_down_avg = float(net_down_samples.mean()) / (1024**2)
    # net_down_max = float(net_down_samples.max()) / (1024**2)
    # net_down_std = float(net_down_samples.std(ddof=1)) / (1024**2) if idx > 1 else 0.0

    print(f'\n=== PERFORMANCE TESTING RESULTS ===')
    # print(f'CPU: avg= {cpu_avg:.2f}%, max= {cpu_max:.2f}%, sd= {cpu_std:.2f}%')
    # print(f'MEM: avg= {mem_pct_avg:.2f}%, max={mem_pct_max:.2f}%, sd={mem_pct_std:.2f}%')
    # print(f'MEM MB: avg= {mem_mb_avg:.2f} MB, max= {mem_mb_max:.2f} MB, sd= {mem_mb_std:.2f} MB')
    # print(f'NET UP: avg= {net_up_avg:.3f} MB/s, max= {net_up_max:.3f} MB/s, sd= {net_up_std:.3f} MB/s')
    # print(f'NET DN: avg= {net_down_avg:.3f} MB/s, max= {net_down_max:.3f} MB/s, sd= {net_down_std:.3f} MB/s\n')

    # print(f'{cpu_avg:.2f}%,{cpu_max:.2f}%,{cpu_std:.2f}%,{mem_mb_avg:.2f},{mem_mb_max:.2f},{mem_mb_max:.2f},{net_up_avg:.3f},{net_up_max:.3f},{net_up_std:.3f},{net_down_avg:.3f},{net_down_max:.3f},{net_down_std:.3f}')
    print(f'{cpu_avg:.2f}%,{cpu_max:.2f}%,{cpu_std:.2f}%,{mem_mb_avg:.2f},{mem_mb_max:.2f},{mem_mb_std:.2f}')
