import  pickle
import  redis
from loguru import logger
from config.service_config import REDIS_URL
from redis import ConnectionPool, RedisCluster
from redis.backoff import ExponentialBackoff
from redis.cluster import ClusterNode
from redis.retry import Retry
from redis.sentinel import Sentinel

class RedisClient:
    
    def __init__(self, url, max_connections=10):
        if isinstance(url, str):
            self.pool = ConnectionPool.from_url(url, max_connections=max_connections)
            self.connection = redis.StrictRedis(connection_pool=self.pool)
        else:
            logger.error(f"redis init only support Standalone mode")

    def cluster_nodes(self, key):
        if isinstance(self.connection,
                      RedisCluster) and self.connection.get_default_node() is None:
            target = self.connection.get_node_from_key(key)
            self.connection.set_default_node(target)

    def setNx(self, key, value, expiration=3600):
        try:
            if pickled := pickle.dumps(value):
                self.cluster_nodes(key)
                result = self.connection.setnx(key, pickled)
                self.connection.expire(key, expiration)
                if not result:
                    return False
                return True
        except TypeError as exc:
            raise TypeError('RedisCache only accepts values that can be pickled. ') from exc
        finally:
            self.close()

    def close(self):
        self.connection.close()

# 实例化对象
redis_client = RedisClient(REDIS_URL)