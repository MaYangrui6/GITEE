
from abc import abstractmethod
from typing import List


class BaseExecutor:
    def __init__(self, dbname, user, password, host, port, schema, driver=None):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.schema = schema
        self.driver = driver

    def get_schema(self):
        return self.schema

    @abstractmethod
    def execute_sqls(self, sqls) -> List[str]:
        pass

    @abstractmethod
    def session(self):
        pass
