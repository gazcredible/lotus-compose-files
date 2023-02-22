from enum import Enum, unique
from typing import NamedTuple, Union
import epanet.toolkit as en

# Identifier: Number used to get the property value from EPANET (directly or
# indirectly)
# MethodGet: Function to get the property value
# MethodSet: Function to set the property value. `None` if cannot be set.
Properties = NamedTuple('Properties', [
    ('Identifier', Union[int, None]),
    ('MethodGet', str),
    ('MethodSet', Union[str, None])
])


@unique
class EpanetModes(Enum):
    PDA = en.PDA
    DDA = en.DDA


@unique
class ProjectSources(Enum):
    NoModel = 'NoModel'
    Inp = 'Inp'
    Fiware = 'Fiware'


@unique
class LinkTypes(Enum):
    CheckValvePipe = en.CVPIPE
    Pipe = en.PIPE
    Pump = en.PUMP
    PRValve = en.PRV
    PSValve = en.PSV
    PBValve = en.PBV
    FCValve = en.FCV
    TCValve = en.TCV
    GPValve = en.GPV


@unique
class NodeTypes(Enum):
    Junction = en.JUNCTION
    Reservoir = en.RESERVOIR
    Tank = en.TANK


@unique
class SourceTypes(Enum):
    CONCEN = en.CONCEN
    MASS = en.MASS
    SETPOINT = en.SETPOINT
    FLOWPACED = en.FLOWPACED


@unique
class TimeParams(Enum):
    Duration = Properties(en.DURATION, 'gettimeparam', 'settimeparam')
    HydStep = Properties(en.HYDSTEP, 'gettimeparam', 'settimeparam')
    QualStep = Properties(en.QUALSTEP, 'gettimeparam', 'settimeparam')
    PatternStep = Properties(en.PATTERNSTEP, 'gettimeparam', 'settimeparam')
    PatternStart = Properties(en.PATTERNSTART, 'gettimeparam', 'settimeparam')
    ReportStep = Properties(en.REPORTSTEP, 'gettimeparam', 'settimeparam')
    ReportStart = Properties(en.REPORTSTART, 'gettimeparam', 'settimeparam')
    RuleStep = Properties(en.RULESTEP, 'gettimeparam', 'settimeparam')
    Statistic = Properties(en.STATISTIC, 'gettimeparam', 'settimeparam')
    Periods = Properties(en.PERIODS, 'gettimeparam', None)
    StartTime = Properties(en.STARTTIME, 'gettimeparam', None)
    HTime = Properties(en.HTIME, 'gettimeparam', None)
    QTime = Properties(en.QTIME, 'gettimeparam', None)
    HaltFlag = Properties(en.HALTFLAG, 'gettimeparam', None)
    NextEvent = Properties(en.NEXTEVENT, 'gettimeparam', None)
    NextEventTank = Properties(en.NEXTEVENTTANK, 'gettimeparam', None)


QualityInfo = NamedTuple('QualityInfo', [
    ('QualType', int),
    ('ChemName', str),
    ('ChemUnits', str),
    ('TraceNode', Union[str, None])
])


@unique
class Options(Enum):
    Trials = Properties(en.TRIALS, 'getoption', 'setoption')
    Accuracy = Properties(en.ACCURACY, 'getoption', 'setoption')
    Tolerance = Properties(en.TOLERANCE, 'getoption', 'setoption')
    EmitExpon = Properties(en.EMITEXPON, 'getoption', 'setoption')
    DemandMult = Properties(en.DEMANDMULT, 'getoption', 'setoption')
    HeadError = Properties(en.HEADERROR, 'getoption', 'setoption')
    FlowChange = Properties(en.FLOWCHANGE, 'getoption', 'setoption')
    HeadLossForm = Properties(en.HEADLOSSFORM, 'getoption', 'setoption')
    DemandCharge = Properties(en.DEMANDCHARGE, 'getoption', 'setoption')
    SpGravity = Properties(en.SP_GRAVITY, 'getoption', 'setoption')
    Viscos = Properties(en.SP_VISCOS, 'getoption', 'setoption')
    Unbalanced = Properties(en.UNBALANCED, 'getoption', 'setoption')
    CheckFreq = Properties(en.CHECKFREQ, 'getoption', 'setoption')
    MaxCheck = Properties(en.MAXCHECK, 'getoption', 'setoption')
    DampLimit = Properties(en.DAMPLIMIT, 'getoption', 'setoption')
    Diffus = Properties(en.SP_DIFFUS, 'getoption', 'setoption')
    BulkOrder = Properties(en.BULKORDER, 'getoption', 'setoption')
    WallOrder = Properties(en.WALLORDER, 'getoption', 'setoption')
    TankOrder = Properties(en.TANKORDER, 'getoption', 'setoption')
    ConcenLimit = Properties(en.CONCENLIMIT, 'getoption', 'setoption')
    QualInfo = Properties(None, 'get_qual_info', 'set_qual_info')


@unique
class PipeProperties(Enum):
    # Static properties (change only if updated manually):
    Name = Properties(None, 'get_name', None)
    LinkType = Properties(None, 'get_link_type', None)
    StartNodeID = Properties(0, 'get_link_node_id', None)
    EndNodeID = Properties(1, 'get_link_node_id', None)
    VerticesX = Properties(0, 'get_link_vertices', None)
    VerticesY = Properties(1, 'get_link_vertices', None)
    KBulk = Properties(en.KBULK, 'get_link_value', 'set_link_value')
    KWall = Properties(en.KWALL, 'get_link_value', 'set_link_value')
    Length = Properties(en.LENGTH, 'get_link_value', 'set_link_value')
    Diameter = Properties(en.DIAMETER, 'get_link_value', 'set_link_value')
    Roughness = Properties(en.ROUGHNESS, 'get_link_value', 'set_link_value')
    MinorLossCoeff = Properties(
        en.MINORLOSS, 'get_link_value', 'set_link_value')
    InitStatus = Properties(en.INITSTATUS, 'get_link_value', 'set_link_value')
    # Dynamic properties:
    Status = Properties(en.STATUS, 'get_link_value', 'set_link_value')
    Flow = Properties(en.FLOW, 'get_link_value', None)
    Velocity = Properties(en.VELOCITY, 'get_link_value', None)
    HeadLoss = Properties(en.HEADLOSS, 'get_link_value', None)
    Quality = Properties(en.QUALITY, 'get_link_value', None)


@unique
class ValveProperties(Enum):
    # Static properties (change only if updated manually):
    Name = Properties(None, 'get_name', None)
    LinkType = Properties(None, 'get_link_type', None)
    StartNodeID = Properties(0, 'get_link_node_id', None)
    EndNodeID = Properties(1, 'get_link_node_id', None)
    Diameter = Properties(en.DIAMETER, 'get_link_value', 'set_link_value')
    MinorLossCoeff = Properties(
        en.MINORLOSS, 'get_link_value', 'set_link_value')
    InitStatus = Properties(en.INITSTATUS, 'get_link_value', 'set_link_value')
    InitSetting = Properties(
        en.INITSETTING, 'get_link_value', 'set_link_value')
    VerticesX = Properties(0, 'get_link_vertices', None)
    VerticesY = Properties(1, 'get_link_vertices', None)
    # Dynamic properties:
    Status = Properties(en.STATUS, 'get_link_value', 'set_link_value')
    Setting = Properties(en.SETTING, 'get_link_value', 'set_link_value')
    Flow = Properties(en.FLOW, 'get_link_value', None)
    Velocity = Properties(en.VELOCITY, 'get_link_value', None)
    HeadLoss = Properties(en.HEADLOSS, 'get_link_value', None)
    Quality = Properties(en.QUALITY, 'get_link_value', None)


@unique
class PumpProperties(Enum):
    # Static properties (change only if updated manually)
    Name = Properties(None, 'get_name', None)
    LinkType = Properties(None, 'get_link_type', None)
    StartNodeID = Properties(0, 'get_link_node_id', None)
    EndNodeID = Properties(1, 'get_link_node_id', None)
    InitStatus = Properties(en.INITSTATUS, 'get_link_value', 'set_link_value')
    InitSetting = Properties(
        en.INITSETTING, 'get_link_value', 'set_link_value')
    HCurveName = Properties(en.PUMP_HCURVE, 'get_link_curve_name', None)
    PowerRating = Properties(en.PUMP_POWER, 'get_link_value', 'set_link_value')
    ECurveName = Properties(en.PUMP_ECURVE, 'get_link_curve_name', None)
    ECost = Properties(en.PUMP_ECOST, 'get_link_value', 'set_link_value')
    EPatternName = Properties(en.PUMP_EPAT, 'get_link_patten_name', None)
    VerticesX = Properties(0, 'get_link_vertices', None)
    VerticesY = Properties(1, 'get_link_vertices', None)
    PumpSpeedPatternName = Properties(
        en.LINKPATTERN, 'get_link_patten_name', None)
    # Dynamic properties
    Status = Properties(en.STATUS, 'get_link_value', 'set_link_value')
    Setting = Properties(en.SETTING, 'get_link_value', 'set_link_value')
    Flow = Properties(en.FLOW, 'get_link_value', None)
    Velocity = Properties(en.VELOCITY, 'get_link_value', None)
    HeadLoss = Properties(en.HEADLOSS, 'get_link_value', None)
    Quality = Properties(en.QUALITY, 'get_link_value', None)
    EnergyUse = Properties(en.ENERGY, 'get_link_value', None)
    PumpState = Properties(en.PUMP_STATE, 'get_link_value', None)
    PumpEffic = Properties(en.PUMP_EFFIC, 'get_link_value', None)


@unique
class JunctionProperties(Enum):
    # Static properties (change only if updated manually)
    Name = Properties(None, 'get_name', None)
    NodeType = Properties(None, 'get_node_type', None)
    Position = Properties(en.CANOVERFLOW, 'get_node_position', None)
    Elevation = Properties(en.ELEVATION, 'get_node_value', 'set_node_value')
    BaseDemand = Properties(en.BASEDEMAND, 'get_node_value', 'set_node_value')
    DemandPatternName = Properties(en.PATTERN, 'get_node_patten_name', None)
    InitQuality = Properties(en.INITQUAL, 'get_node_value', 'set_node_value')
    Emitter = Properties(en.EMITTER, 'get_node_value', 'set_node_value')
    SourceQuality = Properties(
        en.SOURCEQUAL, 'get_node_value', 'set_node_value')
    SourcePatternName = Properties(en.SOURCEPAT, 'get_node_patten_name', None)
    SourceType = Properties(en.SOURCETYPE, 'get_node_value', 'set_node_value')
    # Dynamic properties
    Supply = Properties(en.DEMAND, 'get_node_value', None)
    SupplyDeficit = Properties(en.DEMANDDEFICIT, 'get_node_value', None)
    Head = Properties(en.HEAD, 'get_node_value', None)
    Pressure = Properties(en.PRESSURE, 'get_node_value', None)
    Quality = Properties(en.QUALITY, 'get_node_value', None)
    SourceMassInflow = Properties(en.SOURCEMASS, 'get_node_value', None)


@unique
class TankProperties(Enum):
    # Static properties (change only if updated manually)
    Name = Properties(None, 'get_name', None)
    NodeType = Properties(None, 'get_node_type', None)
    Position = Properties(en.CANOVERFLOW, 'get_node_position', None)
    SourcePatternName = Properties(en.SOURCEPAT, 'get_node_patten_name', None)
    Elevation = Properties(en.ELEVATION, 'get_node_value', 'set_node_value')
    InitQuality = Properties(en.INITQUAL, 'get_node_value', 'set_node_value')
    SourceQuality = Properties(
        en.SOURCEQUAL, 'get_node_value', 'set_node_value')
    SourceType = Properties(en.SOURCETYPE, 'get_node_value', 'set_node_value')
    InitVolume = Properties(en.INITVOLUME, 'get_node_value', None)
    InitLevel = Properties(None, 'get_init_level', 'set_init_level')
    MixModel = Properties(en.MIXMODEL, 'get_node_value', 'set_node_value')
    MixZoneVolume = Properties(en.MIXZONEVOL, 'get_node_value', None)
    Diameter = Properties(en.TANKDIAM, 'get_node_value', 'set_node_value')
    MinVolume = Properties(en.MINVOLUME, 'get_node_value', 'set_node_value')
    MinLevel = Properties(en.MINLEVEL, 'get_node_value', 'set_node_value')
    MaxLevel = Properties(en.MAXLEVEL, 'get_node_value', 'set_node_value')
    MixFraction = Properties(
        en.MIXFRACTION, 'get_node_value', 'set_node_value')
    KBulk = Properties(en.TANK_KBULK, 'get_node_value', 'set_node_value')
    VolumeCurveName = Properties(en.VOLCURVE, 'get_node_curve_name', None)
    MaxVolume = Properties(en.MAXVOLUME, 'get_node_value', None)
    CanOverflow = Properties(en.CANOVERFLOW, 'get_node_value', None)
    # Dynamic properties
    TankLevel = Properties(en.TANKLEVEL, 'get_node_value', None)
    Supply = Properties(en.DEMAND, 'get_node_value', None)
    SupplyDeficit = Properties(en.DEMANDDEFICIT, 'get_node_value', None)
    Head = Properties(en.HEAD, 'get_node_value', None)
    Pressure = Properties(en.PRESSURE, 'get_node_value', None)
    Quality = Properties(en.QUALITY, 'get_node_value', None)
    SourceMassInflow = Properties(en.SOURCEMASS, 'get_node_value', None)
    Volume = Properties(en.TANKVOLUME, 'get_node_value', None)


@unique
class ReservoirProperties(Enum):
    # Static properties (change only if updated manually)
    Name = Properties(None, 'get_name', None)
    NodeType = Properties(None, 'get_node_type', None)
    Position = Properties(en.CANOVERFLOW, 'get_node_position', None)
    SourcePatternName = Properties(en.SOURCEPAT, 'get_node_patten_name', None)
    Elevation = Properties(en.ELEVATION, 'get_node_value', 'set_node_value')
    InitQuality = Properties(en.INITQUAL, 'get_node_value', 'set_node_value')
    SourceQuality = Properties(
        en.SOURCEQUAL, 'get_node_value', 'set_node_value')
    SourceType = Properties(en.SOURCETYPE, 'get_node_value', 'set_node_value')
    # Dynamic properties
    Supply = Properties(en.DEMAND, 'get_node_value', None)
    SupplyDeficit = Properties(en.DEMANDDEFICIT, 'get_node_value', None)
    Head = Properties(en.HEAD, 'get_node_value', None)
    Pressure = Properties(en.PRESSURE, 'get_node_value', None)
    Quality = Properties(en.QUALITY, 'get_node_value', None)
    SourceMassInflow = Properties(en.SOURCEMASS, 'get_node_value', None)
