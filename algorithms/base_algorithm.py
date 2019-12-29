import abc
from typing import Union, List, Iterable, Dict, Type

import gbvision as gbv
import gbrpi


class BaseAlgorithm(abc.ABC):
    __registered = {}
    algorithm_name = None

    def __init_subclass__(cls, **kwargs):
        if cls.algorithm_name is None:
            raise AttributeError(f'algorithm_name static field value not set for class {cls.__name__}')
        if cls.algorithm_name in BaseAlgorithm.__registered:
            other_cls = BaseAlgorithm.__registered[cls.algorithm_name]
            raise KeyError(
                f'duplicated entry for algorithm_name {cls.algorithm_name}: {other_cls.__name__} and {cls.__name__}')
        BaseAlgorithm.__registered[cls.algorithm_name] = cls

    def __init__(self, output_key: Union[str, List[str]], conn: gbrpi.TableConn):
        self.output_key = output_key
        self.conn = conn

    def __call__(self, frame: gbv.Frame, camera: gbv.Camera):
        values = self._process(frame, camera)
        if type(self.output_key) is str:
            self.conn.set(self.output_key, values)
        else:
            for i, value in enumerate(values):
                self.conn.set(self.output_key[i], value)

    @abc.abstractmethod
    def _process(self, frame: gbv.Frame, camera: gbv.Camera) -> Union[
        gbrpi.ConnEntryValue, Iterable[gbrpi.ConnEntryValue]]:
        """

        :param frame:
        :param camera:
        :return:
        """

    @classmethod
    def get_algorithms(cls) -> Dict[str, Type['BaseAlgorithm']]:
        return cls.__registered.copy()