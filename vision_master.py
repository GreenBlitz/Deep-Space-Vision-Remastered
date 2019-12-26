import gbvision as gbv
import gbrpi
import numpy as np

import algorithms

TABLE_NAME = 'vision'
TABLE_IP = '10.45.90.2'
OUTPUT_KEY = 'output'

def main():
    conn = gbrpi.TableConn(ip=TABLE_IP, table_name=TABLE_NAME)
    camera = gbv.USBCamera(0, gbv.LIFECAM_3000.rotate_pitch(np.deg2rad(35)))
    possible_algos = {}
    for algo in algorithms.get_algorithms():
        possible_algos[algo.algorithm_name] = algo(OUTPUT_KEY)

    while True:
        ok, frame = camera.read()
        algo_type = conn.get('algorithm')
        if algo_type is not None:
            algo: algorithms.BaseAlgorithm = possible_algos[algo_type]
            algo(frame, camera, conn)


if __name__ == '__main__':
    main()
