from enum import Enum
from itertools import count

from abc import ABC, abstractmethod
from vsdnemul.lib.docker import DockerApi
from vsdnemul.log import get_logger
from vsdnemul.port import PortFabric, PortType
from vsdnemul.lib import check_not_null

logger = get_logger(__name__)


class NodeType(Enum):
    HOST = "HOST"
    SWITCH = "SWITCH"
    ROUTER = "ROUTER"
    WIFI_ROUTER = "WIFI_ROUTER"
    CONTROLLER = "CONTROLLER"
    SERVER = "SERVER"
    HYPERVISOR = "SDN HYPERVISOR"

    def describe(self):
        return self.name.lower()

    @classmethod
    def has_member(cls, value):
        return any(value == item.value for item in cls)

class NodeTemplate(ABC):


    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def delete(self):
        pass

class Node(object):

    def __init__(self, **kwargs):
        self.__name = kwargs.get("name")
        self.__type = kwargs.get("type")
        self.__image = kwargs.get("image")
        self.__template = kwargs.get("template")
        self.__ports = PortFabric(node_name=self.__name)


    @property
    def image(self):
        return self.__image

    @image.setter
    def image(self, value):
        pass

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        if DockerApi.get_status_node(self.name) == "running":
            DockerApi.rename_node(self.name, new_name = value)
            self.__name = value
        else:
            self.__name = value

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, value):
        if NodeType.has_member(value = value):
            self.__type = value

    @property
    def services(self):
        return self.__services

    @property
    def volume(self):
        return self.__volume

    @volume.setter
    def volume(self, value):
        if self.__volume is None:
            self.__volume = value
        else:
            pass

    @property
    def cap_add(self):
        return self.__cap_add

    @cap_add.setter
    def cap_add(self, value):
        if self.__cap_add is None:
            self.__cap_add = value
        else:
            pass

    @services.setter
    def services(self, value):
        if self.__services is None:
            self.__services = value
        else:
            pass

    @property
    def node_pid(self):
        try:
            return DockerApi.get_pid_node(name = self.name)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    @property
    def node_status(self):
        try:
            return DockerApi.get_status_node(name = self.name)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    @property
    def control_ip(self):
        try:
            return DockerApi.get_control_ip(name = self.name)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    @control_ip.setter
    def control_ip(self, value):
        pass

    def send_cmd(self, cmd = None):
        try:
            return DockerApi.run_cmd(name = self.name, cmd = cmd)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    def get_cli_prompt(self, shell = "bash"):
        try:
            DockerApi.get_shell(name = self.name, shell = shell)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    def add_node_port(self, type: PortType):
        try:
            return self.__ports.add_port(type = type)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    def del_node_port(self, name):
        try:
            self.__ports.del_port(name = name)
        except Exception as ex:
            logger.error(str(ex.args[0]))

    def is_port_exist(self, name):
        return self.__ports.is_exist(name = name)

    def get_ports(self):
        return self.__ports.get_ports()

    def commit(self):
        self.__template.create()

    def destroy(self):

class NodeFabric(object):
    def __init__(self):
        self.__nodes = {}
        self.__node_idx = count()

    def add_node(self, node):
        if not self.__exist_node(name = node.name):
            key = self.__node_idx.__next__()
            node.idx = key
            self.__nodes.update({key: node})
            return node
        else:
            raise ValueError("the node object already exists")

    def del_node(self, name):
        if self.__exist_node(name = name):
            key = self.__get_index(name = name)
            del self.__nodes[key]
        else:
            ValueError("the node was not found")

    def update_node(self, idx, node):
        if self.__exist_node(idx = idx):
            self.__nodes.update({idx: node})
        else:
            ValueError("the node was not found")

    def get_node(self, name):

        if self.__exist_node(name = name):
            key = self.get_index(name = name)
            return self.__nodes[key]
        else:
            ValueError("the node was not found")

    def get_nodes(self):
        return self.__nodes.copy()

    def is_exist(self, name):
        return self.__exist_node(name = name)

    def get_index(self, name):
        if self.__exist_node(name = name):
            return self.__get_index(name = name)
        else:
            ValueError("the node was not found")

    def __get_index(self, name):
        for k, n in self.__nodes.items():
            if n.name.__eq__(name):
                return k

    def __exist_node(self, name = None, idx = None):

        if name is not None:
            key = self.__get_index(name = name)
            if key is not None:
                return True

        if idx is not None:
            if idx in self.__nodes.keys():
                return True

        return False


