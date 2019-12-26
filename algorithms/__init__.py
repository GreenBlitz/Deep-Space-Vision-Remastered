from .base_algorithm import BaseAlgorithm
from .target_algorithm import TargetAlgorithm

def get_algorithms():
    return BaseAlgorithm.registered.copy()

