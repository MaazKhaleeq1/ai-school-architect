
import psutil
import logging
import time

# Configure logging
logging.basicConfig(filename='canary.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

def check_cpu_usage(threshold=80):
    usage = psutil.cpu_percent(interval=1)
    if usage > threshold:
        logging.warning(f"High CPU usage detected: {usage}%")
    else:
        logging.info(f"CPU usage is normal: {usage}%")
    return usage

def check_memory_usage(threshold=80):
    memory = psutil.virtual_memory()
    if memory.percent > threshold:
        logging.warning(f"High memory usage detected: {memory.percent}%")
    else:
        logging.info(f"Memory usage is normal: {memory.percent}%")
    return memory.percent

def check_disk_usage(threshold=80):
    disk = psutil.disk_usage('/')
    if disk.percent > threshold:
        logging.warning(f"High disk usage detected: {disk.percent}%")
    else:
        logging.info(f"Disk usage is normal: {disk.percent}%")
    return disk.percent

def run_canary_checks():
    while True:
        check_cpu_usage()
        check_memory_usage()
        check_disk_usage()
        time.sleep(60)  # Sleep for one minute before next check

if __name__ == "__main__":
    run_canary_checks()
