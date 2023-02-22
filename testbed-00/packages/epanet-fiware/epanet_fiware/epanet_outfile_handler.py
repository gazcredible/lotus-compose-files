import os
from enum import Enum, unique
import struct


@unique
class NodeResultLabels(Enum):
    Supply = 'node_supply'
    Head = 'node_head'
    Pressure = 'node_pressure'
    Quality = 'node_quality'


@unique
class LinkResultLabels(Enum):
    Flow = 'link_flow'
    Headloss = 'link_headloss'
    Quality = 'link_quality'
    Status = 'link_status'
    Setting = 'link_setting'
    ReactionRate = 'link_reaction'
    FrictionFactor = 'link_friction'
    Velocity = 'link_velocity'


class EpanetOutFile():
    def __init__(self, filename: str):
        # http://wateranalytics.org/EPANET/_out_file.html
        self.magic_value = 516114521
        self.load(filename)
        if self.warning_flag() > 0:
            print('WARNING: Simulation data contains warnings')

    def bytes_to_int(self, index):
        return struct.unpack_from('I', self.data[index:index + 4])[0]

    def bytes_to_float(self, index):
        return struct.unpack_from('f', self.data[index:index+4])[0]

    def bytes_to_str(self, index, len):
        temp = ''
        for i in range(0, len):
            temp += chr(self.data[index + i])

        return str(temp)

    def load(self, filename):
        if not os.path.exists(filename):
            raise RuntimeError(
                'ERROR: {} does not exist'.format(filename))
        file = open(filename, 'rb')
        self.data = file.read()
        file.close()

        if self.prolog_magic() != self.magic_value:
            raise Exception('Bad data')

        if self.epilog_magic() != self.magic_value:
            raise Exception('Bad data')

        if self.version() != 20012:
            raise Exception('Unsupported version:' + str(self.version()))

        self._node_count = self.bytes_to_int(8)
        self._link_count = self.bytes_to_int(16)
        self._pump_count = self.bytes_to_int(20)
        self._tank_count = self.bytes_to_int(12)

    def prolog_magic(self) -> int:
        return self.bytes_to_int(0)

    def version(self) -> int:
        return self.bytes_to_int(4)

    def node_count(self) -> int:
        return self._node_count

    def tank_count(self) -> int:
        return self._tank_count

    def link_count(self) -> int:
        return self._link_count

    def pump_count(self) -> int:
        return self._pump_count

    def valve_count(self) -> int:
        return self.bytes_to_int(24)

    def node_name(self, index):
        start = 884
        start += 32 * index
        return self.bytes_to_str(start, 32)

    def link_name(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * index
        return self.bytes_to_str(start, 32)

    def link_start(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * index
        return self.bytes_to_int(start)

    def link_end(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * self.link_count()  # link head index
        start += 4 * index
        return self.bytes_to_int(start)

    def node_elevation(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * self.link_count()  # link head index
        start += 4 * self.link_count()  # link tail index
        start += 4 * self.link_count()  # link type
        start += 4 * self.tank_count()  # tank index
        start += 4 * self.tank_count()  # tank surface index
        start += 4 * index
        return self.bytes_to_float(start)

    def link_length(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * self.link_count()  # link head index
        start += 4 * self.link_count()  # link tail index
        start += 4 * self.link_count()  # link type
        start += 4 * self.tank_count()  # tank index
        start += 4 * self.tank_count()  # tank surface index
        start += 4 * self.node_count()  # node elevation
        start += 4 * index
        return self.bytes_to_float(start)

    def link_diameter(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * self.link_count()  # link head index
        start += 4 * self.link_count()  # link tail index
        start += 4 * self.link_count()  # link type
        start += 4 * self.tank_count()  # tank index
        start += 4 * self.tank_count()  # tank surface index
        start += 4 * self.node_count()  # node elevation
        start += 4 * self.link_count()  # link length
        start += 4 * index
        return self.bytes_to_float(start)

    def tank_node(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * self.link_count()  # link head index
        start += 4 * self.link_count()  # link tail index
        start += 4 * self.link_count()  # link type
        start += 4 * index
        return self.bytes_to_int(start)

    def tank_surface_area(self, index):
        start = 884
        start += 32 * self.node_count()  # node ID
        start += 32 * self.link_count()  # link ID
        start += 4 * self.link_count()  # link head index
        start += 4 * self.link_count()  # link tail index
        start += 4 * self.link_count()  # link type
        start += 4 * self.tank_count()  # tank index
        start += 4 * index
        return self.bytes_to_float(start)

    def pump_node(self, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * index

        return self.bytes_to_int(start)

    def node_sim_frame(self,
                       period: int,
                       label: NodeResultLabels):
        if label not in NodeResultLabels:
            raise Exception(
                'Invalid node result label. Label must be in NodeResultLabels')
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        if label == NodeResultLabels.Supply:
            start += 0

        if label == NodeResultLabels.Head:
            start += self.node_count() * 4

        if label == NodeResultLabels.Pressure:
            start += self.node_count() * 8

        if label == NodeResultLabels.Quality:
            start += self.node_count() * 12

        fmt = ''

        for i in range(0, self.node_count()):
            fmt += 'f'

        return struct.unpack_from(
            fmt, self.data[start:start + (self.node_count() * 4)])

    def link_sim_frame(self, period, label: LinkResultLabels):
        if label not in LinkResultLabels:
            raise Exception(
                'Invalid link result label. Label must be in LinkResultLabels')
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size
        start += (4 * 4) * self.node_count()  # go past all the node info

        if label == LinkResultLabels.Flow:
            start += 0

        if label == LinkResultLabels.Velocity:
            start += self.link_count() * 4

        if label == LinkResultLabels.Headloss:
            start += self.link_count() * 8

        if label == LinkResultLabels.Quality:
            start += self.link_count() * 12

        if label == LinkResultLabels.Status:
            start += self.link_count() * 16

        if label == LinkResultLabels.Setting:
            start += self.link_count() * 20

        if label == LinkResultLabels.ReactionRate:
            start += self.link_count() * 24

        if label == LinkResultLabels.FrictionFactor:
            start += self.link_count() * 28

        fmt = ''

        for i in range(0, self.link_count()):
            fmt += 'f'

        return struct.unpack_from(
            fmt, self.data[start:start+(self.link_count()*4)])

    def node_supply(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size
        start += index * 4

        return self.bytes_to_float(start)

    def node_head(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size
        start += 4 * self.node_count()  # demand
        start += index * 4

        return self.bytes_to_float(start)

    def node_pressure(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size
        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += index * 4

        return self.bytes_to_float(start)

    def node_quality(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size
        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += index * 4

        return self.bytes_to_float(start)

    def link_flow(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality
        start += index * 4

        return self.bytes_to_float(start)

    def link_velocity(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link

        start += index * 4

        return self.bytes_to_float(start)

    def link_headloss(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link
        start += 4 * self.link_count()  # velocity

        start += index * 4

        return self.bytes_to_float(start)

    def link_quality(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link
        start += 4 * self.link_count()  # velocity
        start += 4 * self.link_count()  # headloss

        start += index * 4

        return self.bytes_to_float(start)

    def link_status(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link
        start += 4 * self.link_count()  # velocity
        start += 4 * self.link_count()  # headloss
        start += 4 * self.link_count()  # quality

        start += index * 4

        return self.bytes_to_float(start)

    def link_setting(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link
        start += 4 * self.link_count()  # velocity
        start += 4 * self.link_count()  # headloss
        start += 4 * self.link_count()  # quality
        start += 4 * self.link_count()  # status

        start += index * 4

        return self.bytes_to_float(start)

    def link_reaction(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link
        start += 4 * self.link_count()  # velocity
        start += 4 * self.link_count()  # headloss
        start += 4 * self.link_count()  # quality
        start += 4 * self.link_count()  # status
        start += 4 * self.link_count()  # setting

        start += index * 4

        return self.bytes_to_float(start)

    def link_friction(self, period, index):
        start = 884 + (36 * self.node_count()) + \
            (52 * self.link_count()) + (8 * self.tank_count())
        start += 28 * self.pump_count()
        start += 4  # peak demand charge
        start += period * (
            (16 * self.node_count()) + (32 * self.link_count()))  # period size

        start += 4 * self.node_count()  # demand
        start += 4 * self.node_count()  # head
        start += 4 * self.node_count()  # pressure
        start += 4 * self.node_count()  # quality

        start += 4 * self.link_count()  # link
        start += 4 * self.link_count()  # velocity
        start += 4 * self.link_count()  # headloss
        start += 4 * self.link_count()  # quality
        start += 4 * self.link_count()  # status
        start += 4 * self.link_count()  # setting
        start += 4 * self.link_count()  # reaction

        start += index * 4

        return self.bytes_to_float(start)

    def reporting_periods(self):
        start = len(self.data) - 28
        start += 16

        return self.bytes_to_int(start)

    def epilog_magic(self):
        start = len(self.data) - 28
        start += 24

        return self.bytes_to_int(start)

    def warning_flag(self):
        start = len(self.data) - 28
        start += 20

        return self.bytes_to_int(start)
