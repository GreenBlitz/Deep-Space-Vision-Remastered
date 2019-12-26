import abc
import gbvision as gbv
import gbrpi
from collections.abc import Iterable


class BaseAlgorithm(abc.ABC):
    registered = []
    algorithm_name = None

    def __init_subclass__(cls, **kwargs):
        BaseAlgorithm.registered.append(cls)

    def __init__(self, output_key: str, ignore_exceptions=False):
        self.output_key = output_key
        self.ignore_exceptions = ignore_exceptions

    def __call__(self, frame: gbv.Frame, camera: gbv.Camera, conn: gbrpi.TableConn):
        """
        :param camera:
        :param conn:
        :return:
        """
        try:
            values = self._process(frame, camera, conn)
        except:
            if self.ignore_exceptions:
                values = None
            else:
                raise

        if isinstance(values, Iterable):
            values = tuple(values)
        conn.set(self.output_key, values)

    @abc.abstractmethod
    def _process(self, frame: gbv.Frame, camera: gbv.Camera, conn: gbrpi.TableConn):
        pass
