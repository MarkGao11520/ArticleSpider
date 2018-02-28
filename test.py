# coding:utf8

import redis
redis_cli = redis.StrictRedis(host="localhost")

redis_cli.incrby("jobbole_count")
