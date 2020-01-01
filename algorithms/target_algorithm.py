import gbrpi
import numpy as np

from constants import CONTOUR_MIN_AREA
from constants.distances import TARGETS_DISTANCE, TARGETS_MAX_ERROR
from exceptions.algorithm_incomplete import AlgorithmIncomplete
from .base_algorithm import BaseAlgorithm
import gbvision as gbv
from constants.thresholds import VISION_TARGET_THRESHOLD
from constants.game_objects import VISION_TARGET


class TargetAlgorithm(BaseAlgorithm):
    algorithm_name = 'targets'
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'

    def __init__(self, output_key: str, success_key: str, conn: gbrpi.TableConn, log_algorithm_incomplete=False):
        BaseAlgorithm.__init__(self, output_key, success_key, conn, log_algorithm_incomplete)
        self.finder = gbv.RotatedRectFinder(VISION_TARGET_THRESHOLD, VISION_TARGET, contour_min_area=CONTOUR_MIN_AREA)
        self.continuity_tracker = gbv.ContinuesShapeWrapper([], None, self.finder.find_shapes,
                                                            gbv.ContinuesShapeWrapper.SHAPE_TYPE_ROTATED_RECT,
                                                            shape_lifespan=20, track_new=True)
        self.tracked_targets_ids = set()
        self.direction = None

    def pair_shapes(self, shapes, camera):
        # split to left and right
        left_shapes, right_shapes = gbv.split_list(lambda rotated_rect: rotated_rect[1][2] < -45.0, shapes.items())

        # sort by x
        left_shapes.sort(key=lambda x: x[1][0][0])
        right_shapes.sort(key=lambda x: x[1][0][0])

        # parse to dict
        left_shapes, right_shapes = dict(left_shapes), dict(right_shapes)

        pairs = {}

        found_index_right = set()
        found_index_left = set()
        for i in left_shapes:

            for j in found_index_right:
                del right_shapes[j]
            found_index_right.clear()

            for j in right_shapes:
                if right_shapes[j] < left_shapes[j]:
                    continue

                pair = (left_shapes[i], right_shapes[j])

                locs = self.finder.locations_from_shapes(pair, camera)
                if abs(np.linalg.norm(locs[0] - locs[1]) - TARGETS_DISTANCE) <= TARGETS_MAX_ERROR:
                    pairs[i] = pairs[j] = pair

                    found_index_right.add(j)
                    found_index_left.add(i)
                    break

        for i in found_index_left:
            del left_shapes[i]

        for i in left_shapes:
            pairs[i] = (left_shapes[i], None)

        for i in right_shapes:
            pairs[i] = (None, right_shapes[i])

        return pairs

    def distance(self, shape, camera):
        if shape[0] is None:  # only left
            distance = self.finder.locations_from_shapes([shape[1]], camera)

            return np.concatenate((distance + np.array([TARGETS_DISTANCE, 0, 0]), np.array([0])))
        elif shape[1] is None:  # only right
            distance = self.finder.locations_from_shapes([shape[0]], camera)

            return np.concatenate((distance + np.array([-TARGETS_DISTANCE, 0, 0]), np.array([0])))
        else:  # both (can also find angle)
            distances = self.finder.locations_from_shapes(shape, camera)
            return np.concatenate(((distances[0] + distances[1]) / 2,
                                   np.array(
                                       [np.pi / 2 - np.arccos(
                                           max(-1, min(1, (distances[0][2] - distances[1][2]) / (
                                                   TARGETS_DISTANCE * 2))))])))

    def _process(self, frame: gbv.Frame, camera: gbv.Camera):
        shapes = self.continuity_tracker.find_shapes(frame)
        shapes = self.pair_shapes(shapes, camera)
        if len(shapes) == 0:
            raise AlgorithmIncomplete()

        direction = self.conn.get('focus')

        if direction != self.direction:
            self.direction = direction
            self.tracked_targets_ids.clear()

        for uid in self.tracked_targets_ids:
            if uid in shapes:
                return self.distance(shapes[uid], camera)

        distances = dict(map(lambda x: (x[0], self.distance(x[1], camera)), shapes.items()))
        distances = dict(sorted(distances.items(), key=lambda x: abs(x[1][0])))

        key = next(iter(distances.keys()))

        if direction == self.LEFT:
            for i in distances:
                if distances[i][0] < direction[key][0]:
                    key = i
                    break
            else:
                raise AlgorithmIncomplete()

        elif direction == self.RIGHT:
            for i in distances:
                if distances[i][0] > direction[key][0]:
                    key = i
                    break
            else:
                raise AlgorithmIncomplete()

        for i in distances:
            if distances[i] == distances[key]:  # could be two (for left and right)
                self.tracked_targets_ids.add(i)

        return distances[key]