# utils/redis_connections.py
import os
import redis

def redis_url_from_env(prefix):
    user = os.getenv(f'{prefix}_USER')
    pwd  = os.getenv(f'{prefix}_PASSWORD')
    host = os.getenv(f'{prefix}_HOST','127.0.0.1')
    port = int(os.getenv(f'{prefix}_PORT','6379'))
    db   = int(os.getenv(f'{prefix}_DB','0'))
    if user:
        return f'redis://{user}:{pwd}@{host}:{port}/{db}'
    return f'redis://:{pwd}@{host}:{port}/{db}'

def get_client(prefix="REDIS_APP"):
    return redis.Redis.from_url(redis_url_from_env(prefix), decode_responses=True)
