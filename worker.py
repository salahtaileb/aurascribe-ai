# app/queues/worker.py
import os
from rq import Worker, Queue, Connection
from redis import Redis

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    with Connection(redis_conn):
        q = Queue(os.getenv("BILLING_QUEUE_NAME", "billing"))
        worker = Worker([q])
        worker.work()