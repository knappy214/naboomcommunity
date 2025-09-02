import multiprocessing

# Systemd socket activation: use the FD passed by systemd
bind = "fd://0"

workers = multiprocessing.cpu_count() * 2 + 1
threads = 2
worker_class = "gthread"
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# Timeouts (tune if you have long-running views)
timeout = 60
graceful_timeout = 30
keepalive = 5

# Logging to journald via stdout/stderr
accesslog = '-'
errorlog = '-'
loglevel = 'info'
