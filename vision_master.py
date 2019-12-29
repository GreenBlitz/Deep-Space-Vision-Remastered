import gbvision as gbv
import gbrpi
import numpy as np

from .algorithms import BaseAlgorithm

TABLE_NAME = 'vision'
TABLE_IP = '10.45.90.2'
OUTPUT_KEY = ('found', 'output')


def main():
    conn = gbrpi.TableConn(ip=TABLE_IP, table_name=TABLE_NAME)
    camera = gbv.USBCamera(0, gbv.LIFECAM_3000.rotate_pitch(np.deg2rad(35)))

    all_algos = BaseAlgorithm.get_algorithms()
    possible_algos = {key: all_algos[key](OUTPUT_KEY, conn) for key in all_algos}

    while True:
        ok, frame = camera.read()
        algo_type = conn.get('algorithm')
        if algo_type is not None:
            algo = possible_algos[algo_type]
            algo(frame, camera)


if __name__ == '__main__':
    main()
