"""Card-based keyword editor for K-file format editing"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QScrollArea, QFrame, QGroupBox,
    QPlainTextEdit, QSplitter, QPushButton
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont, QFontDatabase, QDoubleValidator, QIntValidator
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    import qtawesome as qta
except ImportError:
    qta = None


@dataclass
class FieldDef:
    """필드 정의"""
    name: str           # 필드명 (예: 'eid', 'n1')
    label: str          # 표시 레이블
    width: int = 8      # K-file 칸 너비 (8 또는 10)
    field_type: str = 'int'  # int, float, str
    default: Any = 0


@dataclass
class CardDef:
    """Card 정의"""
    name: str           # Card 이름 (예: 'Card 1')
    fields: List[FieldDef]


# 키워드별 Card 정의
KEYWORD_CARDS = {
    'NODE': [
        CardDef('Card 1', [
            FieldDef('nid', 'NID', 8, 'int'),
            FieldDef('x', 'X', 16, 'float'),
            FieldDef('y', 'Y', 16, 'float'),
            FieldDef('z', 'Z', 16, 'float'),
        ]),
    ],
    'ELEMENT_SHELL': [
        CardDef('Card 1', [
            FieldDef('eid', 'EID', 8, 'int'),
            FieldDef('pid', 'PID', 8, 'int'),
            FieldDef('n1', 'N1', 8, 'int'),
            FieldDef('n2', 'N2', 8, 'int'),
            FieldDef('n3', 'N3', 8, 'int'),
            FieldDef('n4', 'N4', 8, 'int'),
        ]),
    ],
    'ELEMENT_SOLID': [
        CardDef('Card 1', [
            FieldDef('eid', 'EID', 8, 'int'),
            FieldDef('pid', 'PID', 8, 'int'),
        ]),
        CardDef('Card 2 (Nodes)', [
            FieldDef('n1', 'N1', 8, 'int'),
            FieldDef('n2', 'N2', 8, 'int'),
            FieldDef('n3', 'N3', 8, 'int'),
            FieldDef('n4', 'N4', 8, 'int'),
            FieldDef('n5', 'N5', 8, 'int'),
            FieldDef('n6', 'N6', 8, 'int'),
            FieldDef('n7', 'N7', 8, 'int'),
            FieldDef('n8', 'N8', 8, 'int'),
        ]),
    ],
    'PART': [
        CardDef('Card 1 (Title)', [
            FieldDef('name', 'TITLE', 80, 'str', ''),
        ]),
        CardDef('Card 2', [
            FieldDef('pid', 'PID', 10, 'int'),
            FieldDef('secid', 'SECID', 10, 'int'),
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('eosid', 'EOSID', 10, 'int'),
            FieldDef('hgid', 'HGID', 10, 'int'),
            FieldDef('grav', 'GRAV', 10, 'int'),
            FieldDef('adpopt', 'ADPOPT', 10, 'int'),
            FieldDef('tmid', 'TMID', 10, 'int'),
        ]),
    ],
    'SECTION_SHELL': [
        CardDef('Card 1', [
            FieldDef('secid', 'SECID', 10, 'int'),
            FieldDef('elform', 'ELFORM', 10, 'int', 2),
            FieldDef('shrf', 'SHRF', 10, 'float', 1.0),
            FieldDef('nip', 'NIP', 10, 'int', 2),
            FieldDef('propt', 'PROPT', 10, 'int'),
            FieldDef('qr_irid', 'QR/IRID', 10, 'int'),
            FieldDef('icomp', 'ICOMP', 10, 'int'),
            FieldDef('setyp', 'SETYP', 10, 'int', 1),
        ]),
        CardDef('Card 2', [
            FieldDef('t1', 'T1', 10, 'float'),
            FieldDef('t2', 'T2', 10, 'float'),
            FieldDef('t3', 'T3', 10, 'float'),
            FieldDef('t4', 'T4', 10, 'float'),
            FieldDef('nloc', 'NLOC', 10, 'float'),
            FieldDef('marea', 'MAREA', 10, 'float'),
            FieldDef('idof', 'IDOF', 10, 'float'),
            FieldDef('edgset', 'EDGSET', 10, 'float'),
        ]),
    ],
    'SECTION_SOLID': [
        CardDef('Card 1', [
            FieldDef('secid', 'SECID', 10, 'int'),
            FieldDef('elform', 'ELFORM', 10, 'int', 1),
            FieldDef('aet', 'AET', 10, 'int'),
        ]),
    ],
    'SECTION_BEAM': [
        CardDef('Card 1', [
            FieldDef('secid', 'SECID', 10, 'int'),
            FieldDef('elform', 'ELFORM', 10, 'int', 1),
            FieldDef('shrf', 'SHRF', 10, 'float', 1.0),
            FieldDef('qr_irid', 'QR/IRID', 10, 'int'),
            FieldDef('cst', 'CST', 10, 'int'),
            FieldDef('scoor', 'SCOOR', 10, 'float'),
            FieldDef('nsm', 'NSM', 10, 'float'),
        ]),
        CardDef('Card 2 (Cross Section)', [
            FieldDef('ts1', 'TS1', 10, 'float'),
            FieldDef('ts2', 'TS2', 10, 'float'),
            FieldDef('tt1', 'TT1', 10, 'float'),
            FieldDef('tt2', 'TT2', 10, 'float'),
            FieldDef('nsloc', 'NSLOC', 10, 'float'),
            FieldDef('ntloc', 'NTLOC', 10, 'float'),
        ]),
    ],
    # ===== MATERIAL KEYWORDS =====
    'MAT_ELASTIC': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('e', 'E', 10, 'float'),
            FieldDef('pr', 'PR', 10, 'float'),
            FieldDef('da', 'DA', 10, 'float'),
            FieldDef('db', 'DB', 10, 'float'),
            FieldDef('k', 'K', 10, 'float'),
        ]),
    ],
    'MAT_PLASTIC_KINEMATIC': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('e', 'E', 10, 'float'),
            FieldDef('pr', 'PR', 10, 'float'),
            FieldDef('sigy', 'SIGY', 10, 'float'),
            FieldDef('etan', 'ETAN', 10, 'float'),
            FieldDef('beta', 'BETA', 10, 'float'),
            FieldDef('src', 'SRC', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('srp', 'SRP', 10, 'float'),
            FieldDef('fs', 'FS', 10, 'float'),
            FieldDef('vp', 'VP', 10, 'float'),
        ]),
    ],
    'MAT_PIECEWISE_LINEAR_PLASTICITY': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('e', 'E', 10, 'float'),
            FieldDef('pr', 'PR', 10, 'float'),
            FieldDef('sigy', 'SIGY', 10, 'float'),
            FieldDef('etan', 'ETAN', 10, 'float'),
            FieldDef('fail', 'FAIL', 10, 'float'),
            FieldDef('tdel', 'TDEL', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('c', 'C', 10, 'float'),
            FieldDef('p', 'P', 10, 'float'),
            FieldDef('lcss', 'LCSS', 10, 'int'),
            FieldDef('lcsr', 'LCSR', 10, 'int'),
            FieldDef('vp', 'VP', 10, 'float'),
        ]),
    ],
    'MAT_RIGID': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('e', 'E', 10, 'float'),
            FieldDef('pr', 'PR', 10, 'float'),
            FieldDef('n', 'N', 10, 'float'),
            FieldDef('couple', 'COUPLE', 10, 'float'),
            FieldDef('m', 'M', 10, 'float'),
            FieldDef('alias', 'ALIAS', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('cmo', 'CMO', 10, 'float'),
            FieldDef('con1', 'CON1', 10, 'int'),
            FieldDef('con2', 'CON2', 10, 'int'),
        ]),
    ],
    'MAT_ORTHOTROPIC_ELASTIC': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('ea', 'EA', 10, 'float'),
            FieldDef('eb', 'EB', 10, 'float'),
            FieldDef('ec', 'EC', 10, 'float'),
            FieldDef('prba', 'PRBA', 10, 'float'),
            FieldDef('prca', 'PRCA', 10, 'float'),
            FieldDef('prcb', 'PRCB', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('gab', 'GAB', 10, 'float'),
            FieldDef('gbc', 'GBC', 10, 'float'),
            FieldDef('gca', 'GCA', 10, 'float'),
            FieldDef('aopt', 'AOPT', 10, 'float'),
        ]),
    ],
    'MAT_COMPOSITE_DAMAGE': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('ea', 'EA', 10, 'float'),
            FieldDef('eb', 'EB', 10, 'float'),
            FieldDef('ec', 'EC', 10, 'float'),
            FieldDef('prba', 'PRBA', 10, 'float'),
            FieldDef('prca', 'PRCA', 10, 'float'),
            FieldDef('prcb', 'PRCB', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('gab', 'GAB', 10, 'float'),
            FieldDef('gbc', 'GBC', 10, 'float'),
            FieldDef('gca', 'GCA', 10, 'float'),
            FieldDef('kfail', 'KFAIL', 10, 'float'),
            FieldDef('aopt', 'AOPT', 10, 'float'),
            FieldDef('macf', 'MACF', 10, 'int'),
        ]),
        CardDef('Card 3', [
            FieldDef('xp', 'XP', 10, 'float'),
            FieldDef('yp', 'YP', 10, 'float'),
            FieldDef('zp', 'ZP', 10, 'float'),
            FieldDef('a1', 'A1', 10, 'float'),
            FieldDef('a2', 'A2', 10, 'float'),
            FieldDef('a3', 'A3', 10, 'float'),
        ]),
        CardDef('Card 4', [
            FieldDef('v1', 'V1', 10, 'float'),
            FieldDef('v2', 'V2', 10, 'float'),
            FieldDef('v3', 'V3', 10, 'float'),
            FieldDef('d1', 'D1', 10, 'float'),
            FieldDef('d2', 'D2', 10, 'float'),
            FieldDef('d3', 'D3', 10, 'float'),
            FieldDef('beta', 'BETA', 10, 'float'),
        ]),
        CardDef('Card 5 (Strengths)', [
            FieldDef('sc', 'SC', 10, 'float'),
            FieldDef('xt', 'XT', 10, 'float'),
            FieldDef('yt', 'YT', 10, 'float'),
            FieldDef('yc', 'YC', 10, 'float'),
            FieldDef('sn', 'SN', 10, 'float'),
            FieldDef('syx', 'SYX', 10, 'float'),
            FieldDef('syz', 'SYZ', 10, 'float'),
        ]),
    ],
    'MAT_ENHANCED_COMPOSITE_DAMAGE': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('ea', 'EA', 10, 'float'),
            FieldDef('eb', 'EB', 10, 'float'),
            FieldDef('ec', 'EC', 10, 'float'),
            FieldDef('prba', 'PRBA', 10, 'float'),
            FieldDef('prca', 'PRCA', 10, 'float'),
            FieldDef('prcb', 'PRCB', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('gab', 'GAB', 10, 'float'),
            FieldDef('gbc', 'GBC', 10, 'float'),
            FieldDef('gca', 'GCA', 10, 'float'),
            FieldDef('aopt', 'AOPT', 10, 'float'),
            FieldDef('dfailm', 'DFAILM', 10, 'float'),
            FieldDef('dfails', 'DFAILS', 10, 'float'),
        ]),
    ],
    'MAT_JOHNSON_COOK': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('g', 'G', 10, 'float'),
            FieldDef('e', 'E', 10, 'float'),
            FieldDef('pr', 'PR', 10, 'float'),
            FieldDef('dtf', 'DTF', 10, 'float'),
            FieldDef('vp', 'VP', 10, 'float'),
            FieldDef('rateop', 'RATEOP', 10, 'float'),
        ]),
        CardDef('Card 2', [
            FieldDef('a', 'A', 10, 'float'),
            FieldDef('b', 'B', 10, 'float'),
            FieldDef('n', 'N', 10, 'float'),
            FieldDef('c', 'C', 10, 'float'),
            FieldDef('m', 'M', 10, 'float'),
            FieldDef('tm', 'TM', 10, 'float'),
            FieldDef('tr', 'TR', 10, 'float'),
            FieldDef('epso', 'EPSO', 10, 'float'),
        ]),
        CardDef('Card 3', [
            FieldDef('cp', 'CP', 10, 'float'),
            FieldDef('pc', 'PC', 10, 'float'),
            FieldDef('spall', 'SPALL', 10, 'float'),
            FieldDef('it', 'IT', 10, 'float'),
            FieldDef('d1', 'D1', 10, 'float'),
            FieldDef('d2', 'D2', 10, 'float'),
            FieldDef('d3', 'D3', 10, 'float'),
            FieldDef('d4', 'D4', 10, 'float'),
        ]),
        CardDef('Card 4', [
            FieldDef('d5', 'D5', 10, 'float'),
            FieldDef('c2p', 'C2/P', 10, 'float'),
            FieldDef('erod', 'EROD', 10, 'float'),
            FieldDef('efmin', 'EFMIN', 10, 'float'),
        ]),
    ],
    'MAT_NULL': [
        CardDef('Card 1', [
            FieldDef('mid', 'MID', 10, 'int'),
            FieldDef('ro', 'RO', 10, 'float'),
            FieldDef('pc', 'PC', 10, 'float'),
            FieldDef('mu', 'MU', 10, 'float'),
            FieldDef('terod', 'TEROD', 10, 'float'),
            FieldDef('cerod', 'CEROD', 10, 'float'),
            FieldDef('ym', 'YM', 10, 'float'),
            FieldDef('pr', 'PR', 10, 'float'),
        ]),
    ],
    # ===== CONTACT KEYWORDS =====
    'CONTACT_AUTOMATIC_SURFACE_TO_SURFACE': [
        CardDef('Card 1', [
            FieldDef('ssid', 'SSID', 10, 'int'),
            FieldDef('msid', 'MSID', 10, 'int'),
            FieldDef('sstyp', 'SSTYP', 10, 'int', 0),
            FieldDef('mstyp', 'MSTYP', 10, 'int', 0),
            FieldDef('sboxid', 'SBOXID', 10, 'int'),
            FieldDef('mboxid', 'MBOXID', 10, 'int'),
            FieldDef('spr', 'SPR', 10, 'int'),
            FieldDef('mpr', 'MPR', 10, 'int'),
        ]),
        CardDef('Card 2', [
            FieldDef('fs', 'FS', 10, 'float'),
            FieldDef('fd', 'FD', 10, 'float'),
            FieldDef('dc', 'DC', 10, 'float'),
            FieldDef('vc', 'VC', 10, 'float'),
            FieldDef('vdc', 'VDC', 10, 'float'),
            FieldDef('penchk', 'PENCHK', 10, 'int'),
            FieldDef('bt', 'BT', 10, 'float'),
            FieldDef('dt', 'DT', 10, 'float'),
        ]),
        CardDef('Card 3', [
            FieldDef('sfs', 'SFS', 10, 'float', 1.0),
            FieldDef('sfm', 'SFM', 10, 'float', 1.0),
            FieldDef('sst', 'SST', 10, 'float'),
            FieldDef('mst', 'MST', 10, 'float'),
            FieldDef('sfst', 'SFST', 10, 'float'),
            FieldDef('sfmt', 'SFMT', 10, 'float'),
            FieldDef('fsf', 'FSF', 10, 'float', 1.0),
            FieldDef('vsf', 'VSF', 10, 'float', 1.0),
        ]),
    ],
    'CONTACT_AUTOMATIC_SINGLE_SURFACE': [
        CardDef('Card 1', [
            FieldDef('ssid', 'SSID', 10, 'int'),
            FieldDef('msid', 'MSID', 10, 'int'),
            FieldDef('sstyp', 'SSTYP', 10, 'int', 0),
            FieldDef('mstyp', 'MSTYP', 10, 'int', 0),
            FieldDef('sboxid', 'SBOXID', 10, 'int'),
            FieldDef('mboxid', 'MBOXID', 10, 'int'),
            FieldDef('spr', 'SPR', 10, 'int'),
            FieldDef('mpr', 'MPR', 10, 'int'),
        ]),
        CardDef('Card 2', [
            FieldDef('fs', 'FS', 10, 'float'),
            FieldDef('fd', 'FD', 10, 'float'),
            FieldDef('dc', 'DC', 10, 'float'),
            FieldDef('vc', 'VC', 10, 'float'),
            FieldDef('vdc', 'VDC', 10, 'float'),
            FieldDef('penchk', 'PENCHK', 10, 'int'),
            FieldDef('bt', 'BT', 10, 'float'),
            FieldDef('dt', 'DT', 10, 'float'),
        ]),
    ],
    'CONTACT_TIED_SURFACE_TO_SURFACE': [
        CardDef('Card 1', [
            FieldDef('ssid', 'SSID', 10, 'int'),
            FieldDef('msid', 'MSID', 10, 'int'),
            FieldDef('sstyp', 'SSTYP', 10, 'int', 0),
            FieldDef('mstyp', 'MSTYP', 10, 'int', 0),
            FieldDef('sboxid', 'SBOXID', 10, 'int'),
            FieldDef('mboxid', 'MBOXID', 10, 'int'),
            FieldDef('spr', 'SPR', 10, 'int'),
            FieldDef('mpr', 'MPR', 10, 'int'),
        ]),
    ],
    # ===== SET KEYWORDS =====
    'SET_NODE': [
        CardDef('Card 1', [
            FieldDef('sid', 'SID', 10, 'int'),
            FieldDef('da1', 'DA1', 10, 'float'),
            FieldDef('da2', 'DA2', 10, 'float'),
            FieldDef('da3', 'DA3', 10, 'float'),
            FieldDef('da4', 'DA4', 10, 'float'),
            FieldDef('solver', 'SOLVER', 10, 'str'),
        ]),
    ],
    'SET_PART': [
        CardDef('Card 1', [
            FieldDef('sid', 'SID', 10, 'int'),
            FieldDef('da1', 'DA1', 10, 'float'),
            FieldDef('da2', 'DA2', 10, 'float'),
            FieldDef('da3', 'DA3', 10, 'float'),
            FieldDef('da4', 'DA4', 10, 'float'),
            FieldDef('solver', 'SOLVER', 10, 'str'),
        ]),
    ],
    'SET_SHELL': [
        CardDef('Card 1', [
            FieldDef('sid', 'SID', 10, 'int'),
            FieldDef('da1', 'DA1', 10, 'float'),
            FieldDef('da2', 'DA2', 10, 'float'),
            FieldDef('da3', 'DA3', 10, 'float'),
            FieldDef('da4', 'DA4', 10, 'float'),
            FieldDef('solver', 'SOLVER', 10, 'str'),
        ]),
    ],
    'SET_SOLID': [
        CardDef('Card 1', [
            FieldDef('sid', 'SID', 10, 'int'),
            FieldDef('da1', 'DA1', 10, 'float'),
            FieldDef('da2', 'DA2', 10, 'float'),
            FieldDef('da3', 'DA3', 10, 'float'),
            FieldDef('da4', 'DA4', 10, 'float'),
            FieldDef('solver', 'SOLVER', 10, 'str'),
        ]),
    ],
    'SET_SEGMENT': [
        CardDef('Card 1', [
            FieldDef('sid', 'SID', 10, 'int'),
            FieldDef('da1', 'DA1', 10, 'float'),
            FieldDef('da2', 'DA2', 10, 'float'),
            FieldDef('da3', 'DA3', 10, 'float'),
            FieldDef('da4', 'DA4', 10, 'float'),
            FieldDef('solver', 'SOLVER', 10, 'str'),
        ]),
    ],
    # ===== CONTROL KEYWORDS =====
    'CONTROL_TERMINATION': [
        CardDef('Card 1', [
            FieldDef('endtim', 'ENDTIM', 10, 'float'),
            FieldDef('endcyc', 'ENDCYC', 10, 'int'),
            FieldDef('dtmin', 'DTMIN', 10, 'float'),
            FieldDef('endeng', 'ENDENG', 10, 'float'),
            FieldDef('endmas', 'ENDMAS', 10, 'float'),
        ]),
    ],
    'CONTROL_TIMESTEP': [
        CardDef('Card 1', [
            FieldDef('dtinit', 'DTINIT', 10, 'float'),
            FieldDef('tssfac', 'TSSFAC', 10, 'float', 0.9),
            FieldDef('isdo', 'ISDO', 10, 'int'),
            FieldDef('tslimt', 'TSLIMT', 10, 'float'),
            FieldDef('dt2ms', 'DT2MS', 10, 'float'),
            FieldDef('lctm', 'LCTM', 10, 'int'),
            FieldDef('erode', 'ERODE', 10, 'int'),
            FieldDef('ms1st', 'MS1ST', 10, 'int'),
        ]),
    ],
    'CONTROL_ENERGY': [
        CardDef('Card 1', [
            FieldDef('hgen', 'HGEN', 10, 'int', 1),
            FieldDef('rwen', 'RWEN', 10, 'int', 2),
            FieldDef('slnten', 'SLNTEN', 10, 'int', 1),
            FieldDef('rylen', 'RYLEN', 10, 'int', 1),
        ]),
    ],
    'CONTROL_OUTPUT': [
        CardDef('Card 1', [
            FieldDef('npopt', 'NPOPT', 10, 'int'),
            FieldDef('netefb', 'NETEFB', 10, 'int'),
            FieldDef('nrefup', 'NREFUP', 10, 'int'),
            FieldDef('iaccop', 'IACCOP', 10, 'int'),
            FieldDef('optefb', 'OPTEFB', 10, 'int'),
            FieldDef('ipnint', 'IPNINT', 10, 'int'),
            FieldDef('ikedit', 'IKEDIT', 10, 'int'),
            FieldDef('iflush', 'IFLUSH', 10, 'int'),
        ]),
    ],
    'CONTROL_SHELL': [
        CardDef('Card 1', [
            FieldDef('wrpang', 'WRPANG', 10, 'float', 20.0),
            FieldDef('esort', 'ESORT', 10, 'int'),
            FieldDef('irnxx', 'IRNXX', 10, 'int', -1),
            FieldDef('istupd', 'ISTUPD', 10, 'int'),
            FieldDef('theory', 'THEORY', 10, 'int', 2),
            FieldDef('bwc', 'BWC', 10, 'int', 2),
            FieldDef('miter', 'MITER', 10, 'int', 1),
            FieldDef('proj', 'PROJ', 10, 'int'),
        ]),
    ],
    'CONTROL_CONTACT': [
        CardDef('Card 1', [
            FieldDef('slsfac', 'SLSFAC', 10, 'float', 0.1),
            FieldDef('rwpnal', 'RWPNAL', 10, 'float'),
            FieldDef('islchk', 'ISLCHK', 10, 'int', 1),
            FieldDef('shlthk', 'SHLTHK', 10, 'int'),
            FieldDef('penopt', 'PENOPT', 10, 'int'),
            FieldDef('thkchg', 'THKCHG', 10, 'int'),
            FieldDef('otefb', 'OTEFB', 10, 'int'),
            FieldDef('enmass', 'ENMASS', 10, 'int'),
        ]),
    ],
    'CONTROL_HOURGLASS': [
        CardDef('Card 1', [
            FieldDef('ihq', 'IHQ', 10, 'int', 1),
            FieldDef('qh', 'QH', 10, 'float', 0.1),
        ]),
    ],
    'CONTROL_BULK_VISCOSITY': [
        CardDef('Card 1', [
            FieldDef('q1', 'Q1', 10, 'float', 1.5),
            FieldDef('q2', 'Q2', 10, 'float', 0.06),
            FieldDef('type', 'TYPE', 10, 'int', 1),
        ]),
    ],
    # ===== DATABASE KEYWORDS =====
    'DATABASE_BINARY_D3PLOT': [
        CardDef('Card 1', [
            FieldDef('dt', 'DT', 10, 'float'),
            FieldDef('lcdt', 'LCDT', 10, 'int'),
            FieldDef('beam', 'BEAM', 10, 'int'),
            FieldDef('npltc', 'NPLTC', 10, 'int'),
            FieldDef('psetid', 'PSETID', 10, 'int'),
        ]),
    ],
    'DATABASE_BINARY_D3THDT': [
        CardDef('Card 1', [
            FieldDef('dt', 'DT', 10, 'float'),
            FieldDef('lcdt', 'LCDT', 10, 'int'),
        ]),
    ],
    'DATABASE_GLSTAT': [
        CardDef('Card 1', [
            FieldDef('dt', 'DT', 10, 'float'),
            FieldDef('binary', 'BINARY', 10, 'int'),
            FieldDef('lcur', 'LCUR', 10, 'int'),
            FieldDef('ioopt', 'IOOPT', 10, 'int'),
        ]),
    ],
    'DATABASE_MATSUM': [
        CardDef('Card 1', [
            FieldDef('dt', 'DT', 10, 'float'),
            FieldDef('binary', 'BINARY', 10, 'int'),
            FieldDef('lcur', 'LCUR', 10, 'int'),
            FieldDef('ioopt', 'IOOPT', 10, 'int'),
        ]),
    ],
    'DATABASE_NODOUT': [
        CardDef('Card 1', [
            FieldDef('dt', 'DT', 10, 'float'),
            FieldDef('binary', 'BINARY', 10, 'int'),
            FieldDef('lcur', 'LCUR', 10, 'int'),
            FieldDef('ioopt', 'IOOPT', 10, 'int'),
        ]),
    ],
    'DATABASE_ELOUT': [
        CardDef('Card 1', [
            FieldDef('dt', 'DT', 10, 'float'),
            FieldDef('binary', 'BINARY', 10, 'int'),
            FieldDef('lcur', 'LCUR', 10, 'int'),
            FieldDef('ioopt', 'IOOPT', 10, 'int'),
        ]),
    ],
    'DATABASE_HISTORY_NODE': [
        CardDef('Card 1', [
            FieldDef('id1', 'ID1', 10, 'int'),
            FieldDef('id2', 'ID2', 10, 'int'),
            FieldDef('id3', 'ID3', 10, 'int'),
            FieldDef('id4', 'ID4', 10, 'int'),
            FieldDef('id5', 'ID5', 10, 'int'),
            FieldDef('id6', 'ID6', 10, 'int'),
            FieldDef('id7', 'ID7', 10, 'int'),
            FieldDef('id8', 'ID8', 10, 'int'),
        ]),
    ],
    'DATABASE_HISTORY_SHELL': [
        CardDef('Card 1', [
            FieldDef('id1', 'ID1', 10, 'int'),
            FieldDef('id2', 'ID2', 10, 'int'),
            FieldDef('id3', 'ID3', 10, 'int'),
            FieldDef('id4', 'ID4', 10, 'int'),
            FieldDef('id5', 'ID5', 10, 'int'),
            FieldDef('id6', 'ID6', 10, 'int'),
            FieldDef('id7', 'ID7', 10, 'int'),
            FieldDef('id8', 'ID8', 10, 'int'),
        ]),
    ],
    'DATABASE_CROSS_SECTION_PLANE': [
        CardDef('Card 1', [
            FieldDef('psid', 'PSID', 10, 'int'),
            FieldDef('xct', 'XCT', 10, 'float'),
            FieldDef('yct', 'YCT', 10, 'float'),
            FieldDef('zct', 'ZCT', 10, 'float'),
            FieldDef('xch', 'XCH', 10, 'float'),
            FieldDef('ych', 'YCH', 10, 'float'),
            FieldDef('zch', 'ZCH', 10, 'float'),
        ]),
    ],
    # ===== BOUNDARY KEYWORDS =====
    'BOUNDARY_SPC_NODE': [
        CardDef('Card 1', [
            FieldDef('nid', 'NID', 10, 'int'),
            FieldDef('cid', 'CID', 10, 'int'),
            FieldDef('dofx', 'DOFX', 10, 'int'),
            FieldDef('dofy', 'DOFY', 10, 'int'),
            FieldDef('dofz', 'DOFZ', 10, 'int'),
            FieldDef('dofrx', 'DOFRX', 10, 'int'),
            FieldDef('dofry', 'DOFRY', 10, 'int'),
            FieldDef('dofrz', 'DOFRZ', 10, 'int'),
        ]),
    ],
    'BOUNDARY_SPC_SET': [
        CardDef('Card 1', [
            FieldDef('nsid', 'NSID', 10, 'int'),
            FieldDef('cid', 'CID', 10, 'int'),
            FieldDef('dofx', 'DOFX', 10, 'int'),
            FieldDef('dofy', 'DOFY', 10, 'int'),
            FieldDef('dofz', 'DOFZ', 10, 'int'),
            FieldDef('dofrx', 'DOFRX', 10, 'int'),
            FieldDef('dofry', 'DOFRY', 10, 'int'),
            FieldDef('dofrz', 'DOFRZ', 10, 'int'),
        ]),
    ],
    'BOUNDARY_PRESCRIBED_MOTION_NODE': [
        CardDef('Card 1', [
            FieldDef('nid', 'NID', 10, 'int'),
            FieldDef('dof', 'DOF', 10, 'int'),
            FieldDef('vad', 'VAD', 10, 'int'),
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sf', 'SF', 10, 'float', 1.0),
            FieldDef('vid', 'VID', 10, 'int'),
            FieldDef('death', 'DEATH', 10, 'float'),
            FieldDef('birth', 'BIRTH', 10, 'float'),
        ]),
    ],
    'BOUNDARY_PRESCRIBED_MOTION_SET': [
        CardDef('Card 1', [
            FieldDef('nsid', 'NSID', 10, 'int'),
            FieldDef('dof', 'DOF', 10, 'int'),
            FieldDef('vad', 'VAD', 10, 'int'),
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sf', 'SF', 10, 'float', 1.0),
            FieldDef('vid', 'VID', 10, 'int'),
            FieldDef('death', 'DEATH', 10, 'float'),
            FieldDef('birth', 'BIRTH', 10, 'float'),
        ]),
    ],
    # ===== LOAD KEYWORDS =====
    'LOAD_NODE_POINT': [
        CardDef('Card 1', [
            FieldDef('nid', 'NID', 10, 'int'),
            FieldDef('dof', 'DOF', 10, 'int'),
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sf', 'SF', 10, 'float', 1.0),
            FieldDef('cid', 'CID', 10, 'int'),
            FieldDef('m1', 'M1', 10, 'int'),
            FieldDef('m2', 'M2', 10, 'int'),
            FieldDef('m3', 'M3', 10, 'int'),
        ]),
    ],
    'LOAD_NODE_SET': [
        CardDef('Card 1', [
            FieldDef('nsid', 'NSID', 10, 'int'),
            FieldDef('dof', 'DOF', 10, 'int'),
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sf', 'SF', 10, 'float', 1.0),
            FieldDef('cid', 'CID', 10, 'int'),
            FieldDef('m1', 'M1', 10, 'int'),
            FieldDef('m2', 'M2', 10, 'int'),
            FieldDef('m3', 'M3', 10, 'int'),
        ]),
    ],
    'LOAD_SEGMENT': [
        CardDef('Card 1', [
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sf', 'SF', 10, 'float', 1.0),
            FieldDef('at', 'AT', 10, 'float'),
            FieldDef('n1', 'N1', 10, 'int'),
            FieldDef('n2', 'N2', 10, 'int'),
            FieldDef('n3', 'N3', 10, 'int'),
            FieldDef('n4', 'N4', 10, 'int'),
        ]),
    ],
    'LOAD_BODY_Z': [
        CardDef('Card 1', [
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sf', 'SF', 10, 'float', 1.0),
            FieldDef('lciddr', 'LCIDDR', 10, 'int'),
            FieldDef('xc', 'XC', 10, 'float'),
            FieldDef('yc', 'YC', 10, 'float'),
            FieldDef('zc', 'ZC', 10, 'float'),
        ]),
    ],
    # ===== INITIAL KEYWORDS =====
    'INITIAL_VELOCITY': [
        CardDef('Card 1', [
            FieldDef('nsid', 'NSID', 10, 'int'),
            FieldDef('nsidex', 'NSIDEX', 10, 'int'),
            FieldDef('boxid', 'BOXID', 10, 'int'),
            FieldDef('irigid', 'IRIGID', 10, 'int'),
            FieldDef('icid', 'ICID', 10, 'int'),
        ]),
        CardDef('Card 2', [
            FieldDef('vx', 'VX', 10, 'float'),
            FieldDef('vy', 'VY', 10, 'float'),
            FieldDef('vz', 'VZ', 10, 'float'),
            FieldDef('vxr', 'VXR', 10, 'float'),
            FieldDef('vyr', 'VYR', 10, 'float'),
            FieldDef('vzr', 'VZR', 10, 'float'),
        ]),
    ],
    'INITIAL_VELOCITY_NODE': [
        CardDef('Card 1', [
            FieldDef('nid', 'NID', 10, 'int'),
            FieldDef('vx', 'VX', 10, 'float'),
            FieldDef('vy', 'VY', 10, 'float'),
            FieldDef('vz', 'VZ', 10, 'float'),
            FieldDef('vxr', 'VXR', 10, 'float'),
            FieldDef('vyr', 'VYR', 10, 'float'),
            FieldDef('vzr', 'VZR', 10, 'float'),
        ]),
    ],
    'INITIAL_STRESS_SHELL': [
        CardDef('Card 1', [
            FieldDef('eid', 'EID', 10, 'int'),
            FieldDef('nplane', 'NPLANE', 10, 'int'),
            FieldDef('nthick', 'NTHICK', 10, 'int'),
            FieldDef('nhisv', 'NHISV', 10, 'int'),
            FieldDef('large', 'LARGE', 10, 'int'),
        ]),
    ],
    # ===== CONSTRAINED KEYWORDS =====
    'CONSTRAINED_RIGID_BODIES': [
        CardDef('Card 1', [
            FieldDef('pidm', 'PIDM', 10, 'int'),
            FieldDef('pids', 'PIDS', 10, 'int'),
        ]),
    ],
    'CONSTRAINED_EXTRA_NODES_NODE': [
        CardDef('Card 1', [
            FieldDef('pid', 'PID', 10, 'int'),
            FieldDef('nid', 'NID', 10, 'int'),
        ]),
    ],
    'CONSTRAINED_EXTRA_NODES_SET': [
        CardDef('Card 1', [
            FieldDef('pid', 'PID', 10, 'int'),
            FieldDef('nsid', 'NSID', 10, 'int'),
        ]),
    ],
    'CONSTRAINED_JOINT_REVOLUTE': [
        CardDef('Card 1', [
            FieldDef('n1', 'N1', 10, 'int'),
            FieldDef('n2', 'N2', 10, 'int'),
            FieldDef('n3', 'N3', 10, 'int'),
            FieldDef('n4', 'N4', 10, 'int'),
            FieldDef('n5', 'N5', 10, 'int'),
            FieldDef('n6', 'N6', 10, 'int'),
        ]),
        CardDef('Card 2', [
            FieldDef('rps', 'RPS', 10, 'float'),
            FieldDef('damp', 'DAMP', 10, 'float'),
            FieldDef('lcidph', 'LCIDPH', 10, 'int'),
            FieldDef('lcidth', 'LCIDTH', 10, 'int'),
        ]),
    ],
    'CONSTRAINED_JOINT_SPHERICAL': [
        CardDef('Card 1', [
            FieldDef('n1', 'N1', 10, 'int'),
            FieldDef('n2', 'N2', 10, 'int'),
            FieldDef('n3', 'N3', 10, 'int'),
            FieldDef('n4', 'N4', 10, 'int'),
        ]),
    ],
    'CONSTRAINED_SPOTWELD': [
        CardDef('Card 1', [
            FieldDef('n1', 'N1', 10, 'int'),
            FieldDef('n2', 'N2', 10, 'int'),
            FieldDef('sn', 'SN', 10, 'float'),
            FieldDef('ss', 'SS', 10, 'float'),
            FieldDef('n', 'N', 10, 'float'),
            FieldDef('m', 'M', 10, 'float'),
            FieldDef('tf', 'TF', 10, 'float'),
        ]),
    ],
    # ===== DEFINE KEYWORDS =====
    'DEFINE_CURVE': [
        CardDef('Card 1', [
            FieldDef('lcid', 'LCID', 10, 'int'),
            FieldDef('sidr', 'SIDR', 10, 'int'),
            FieldDef('sfa', 'SFA', 10, 'float', 1.0),
            FieldDef('sfo', 'SFO', 10, 'float', 1.0),
            FieldDef('offa', 'OFFA', 10, 'float'),
            FieldDef('offo', 'OFFO', 10, 'float'),
            FieldDef('dattyp', 'DATTYP', 10, 'int'),
            FieldDef('lcint', 'LCINT', 10, 'int'),
        ]),
    ],
    'DEFINE_COORDINATE_NODES': [
        CardDef('Card 1', [
            FieldDef('cid', 'CID', 10, 'int'),
            FieldDef('n1', 'N1', 10, 'int'),
            FieldDef('n2', 'N2', 10, 'int'),
            FieldDef('n3', 'N3', 10, 'int'),
        ]),
    ],
    'DEFINE_COORDINATE_VECTOR': [
        CardDef('Card 1', [
            FieldDef('cid', 'CID', 10, 'int'),
            FieldDef('xt', 'XT', 10, 'float'),
            FieldDef('yt', 'YT', 10, 'float'),
            FieldDef('zt', 'ZT', 10, 'float'),
            FieldDef('xh', 'XH', 10, 'float'),
            FieldDef('yh', 'YH', 10, 'float'),
            FieldDef('zh', 'ZH', 10, 'float'),
        ]),
    ],
    # ===== ELEMENT BEAM =====
    'ELEMENT_BEAM': [
        CardDef('Card 1', [
            FieldDef('eid', 'EID', 8, 'int'),
            FieldDef('pid', 'PID', 8, 'int'),
            FieldDef('n1', 'N1', 8, 'int'),
            FieldDef('n2', 'N2', 8, 'int'),
            FieldDef('n3', 'N3', 8, 'int'),
            FieldDef('rt1', 'RT1', 8, 'int'),
            FieldDef('rr1', 'RR1', 8, 'int'),
            FieldDef('rt2', 'RT2', 8, 'int'),
        ]),
    ],
}


class FieldWidget(QWidget):
    """개별 필드 편집 위젯"""

    valueChanged = Signal(str, object, object)  # (field_name, old_value, new_value)

    def __init__(self, field_def: FieldDef, parent=None):
        super().__init__(parent)
        self._field_def = field_def
        self._current_value = field_def.default  # 현재 값 저장
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # 레이블
        label = QLabel(self._field_def.label)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(label)

        # 입력 필드
        self._edit = QLineEdit()
        self._edit.setAlignment(Qt.AlignCenter)

        # 너비 설정 (문자 너비 기준)
        char_width = 10  # 대략적인 문자 너비
        self._edit.setFixedWidth(self._field_def.width * char_width)

        # 유효성 검사기 설정
        if self._field_def.field_type == 'int':
            self._edit.setValidator(QIntValidator())
        elif self._field_def.field_type == 'float':
            self._edit.setValidator(QDoubleValidator())

        self._edit.setStyleSheet("""
            QLineEdit {
                background: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                font-family: monospace;
            }
            QLineEdit:focus {
                border: 1px solid #7fbadc;
            }
        """)

        self._edit.textChanged.connect(self._on_value_changed)
        layout.addWidget(self._edit)

    def set_value(self, value, emit_signal=False):
        """값 설정

        Args:
            value: 설정할 값
            emit_signal: True면 valueChanged 시그널 발생 (기본: False)
        """
        if value is None:
            value = self._field_def.default

        # 현재 값 저장 (시그널 발생 안함)
        self._current_value = value

        if self._field_def.field_type == 'float':
            if isinstance(value, float):
                if abs(value) > 1e6 or (abs(value) < 1e-4 and value != 0):
                    text = f"{value:.6e}"
                else:
                    text = f"{value:.6g}"
            else:
                text = str(value)
        else:
            text = str(value)

        # 시그널 발생 제어
        if not emit_signal:
            self._edit.blockSignals(True)
        self._edit.setText(text)
        if not emit_signal:
            self._edit.blockSignals(False)

    def get_value(self):
        """값 가져오기"""
        text = self._edit.text().strip()
        if not text:
            return self._field_def.default

        try:
            if self._field_def.field_type == 'int':
                return int(text)
            elif self._field_def.field_type == 'float':
                return float(text)
            else:
                return text
        except ValueError:
            return self._field_def.default

    def _on_value_changed(self, text):
        """값 변경 시 시그널 발생 (old_value 포함)"""
        new_value = self.get_value()
        old_value = self._current_value
        # 값이 실제로 변경된 경우에만 시그널 발생
        if new_value != old_value:
            self.valueChanged.emit(self._field_def.name, old_value, new_value)
            self._current_value = new_value

    @property
    def field_name(self) -> str:
        return self._field_def.name


class CardWidget(QGroupBox):
    """Card 편집 위젯 (필드들의 그룹)"""

    valueChanged = Signal(str, object, object)  # (field_name, old_value, new_value)

    def __init__(self, card_def: CardDef, parent=None):
        super().__init__(card_def.name, parent)
        self._card_def = card_def
        self._field_widgets: Dict[str, FieldWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #7fbadc;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 4px;
                background: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 8)
        layout.setSpacing(4)

        for field_def in self._card_def.fields:
            field_widget = FieldWidget(field_def)
            field_widget.valueChanged.connect(self._on_field_changed)
            self._field_widgets[field_def.name] = field_widget
            layout.addWidget(field_widget)

        layout.addStretch()

    def set_values(self, data: Dict[str, Any]):
        """데이터에서 값 설정"""
        for field_name, widget in self._field_widgets.items():
            value = data.get(field_name)
            widget.set_value(value)

    def get_values(self) -> Dict[str, Any]:
        """모든 필드 값 가져오기"""
        return {name: widget.get_value() for name, widget in self._field_widgets.items()}

    def _on_field_changed(self, field_name: str, old_value, new_value):
        """필드 값 변경 시 - old_value 포함하여 전달"""
        self.valueChanged.emit(field_name, old_value, new_value)


class KeywordCardEditor(QWidget):
    """키워드 Card 기반 편집기

    K-file 형식에 맞게 Card 단위로 필드를 그룹화하여 편집합니다.
    """

    keywordModified = Signal(str, object, str, object, object)  # (category, item, field_name, old_value, new_value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_category: str = ""
        self._current_item: Any = None
        self._card_widgets: List[CardWidget] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더
        self._header = QLabel("키워드를 선택하세요")
        self._header.setFont(QFont("", 12, QFont.Bold))
        self._header.setStyleSheet("""
            padding: 10px;
            background: #2d5a7b;
            color: #ffffff;
            border-bottom: 2px solid #1a3a4f;
        """)
        layout.addWidget(self._header)

        # 스플리터 (Card 편집 / Raw 미리보기)
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background: #4a4a4a; height: 3px; }")

        # 상단: Card 편집 영역
        self._card_container = QWidget()
        self._card_container.setStyleSheet("background: #2b2b2b;")
        self._card_layout = QVBoxLayout(self._card_container)
        self._card_layout.setContentsMargins(8, 8, 8, 8)
        self._card_layout.setSpacing(8)
        self._card_layout.addStretch()

        card_scroll = QScrollArea()
        card_scroll.setWidgetResizable(True)
        card_scroll.setFrameShape(QFrame.NoFrame)
        card_scroll.setStyleSheet("QScrollArea { background: #2b2b2b; border: none; }")
        card_scroll.setMinimumHeight(100)
        card_scroll.setWidget(self._card_container)
        splitter.addWidget(card_scroll)

        # 하단: Raw K-file 미리보기 (편집 가능)
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)

        preview_header = QLabel("K-file 미리보기 (편집 가능)")
        preview_header.setStyleSheet("padding: 4px 8px; background: #3c3c3c; color: #b0b0b0;")
        preview_layout.addWidget(preview_header)

        self._raw_editor = QPlainTextEdit()
        self._raw_editor.setStyleSheet("""
            QPlainTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                border: none;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed_font.setPointSize(10)
        self._raw_editor.setFont(fixed_font)
        self._raw_editor.textChanged.connect(self._on_raw_text_changed)
        preview_layout.addWidget(self._raw_editor)

        splitter.addWidget(preview_container)
        splitter.setSizes([200, 300])  # 프리뷰 영역을 더 크게
        splitter.setStretchFactor(0, 1)  # Card 영역
        splitter.setStretchFactor(1, 2)  # 프리뷰 영역 우선 확장

        layout.addWidget(splitter)

    def set_keyword(self, category: str, item: Any):
        """키워드 설정 및 Card 편집기 표시"""
        self._current_category = category
        self._current_item = item
        self._update_display()

    def set_range(self, category: str, items: list):
        """범위 항목들의 K-file 미리보기 생성"""
        self._current_category = category
        self._current_item = None

        # 기존 Card 위젯 제거
        self._clear_cards()

        # 헤더 업데이트
        self._header.setText(f"*{self._get_keyword_name(category)} ({len(items):,}개 항목)")

        # Raw 미리보기만 표시
        lines = self._generate_range_kfile(category, items)
        self._raw_editor.setPlainText('\n'.join(lines))

    def _update_display(self):
        """디스플레이 갱신"""
        # 기존 Card 위젯 제거
        self._clear_cards()

        if self._current_item is None:
            self._header.setText("키워드를 선택하세요")
            self._raw_editor.setPlainText("")
            return

        # 헤더 업데이트
        header_text = self._get_header_text()
        self._header.setText(header_text)

        # Card 정의 가져오기
        keyword_name = self._get_keyword_name(self._current_category)
        cards = KEYWORD_CARDS.get(keyword_name, [])

        print(f"[CardEditor] category={self._current_category}, keyword={keyword_name}, cards={len(cards)}")

        # 데이터 추출
        data = self._extract_data()
        print(f"[CardEditor] data={data}")

        # Card 위젯 생성
        for card_def in cards:
            card_widget = CardWidget(card_def)
            card_widget.set_values(data)
            card_widget.valueChanged.connect(self._on_card_value_changed)
            self._card_widgets.append(card_widget)
            # stretch 앞에 삽입 (index 0부터)
            self._card_layout.insertWidget(len(self._card_widgets) - 1, card_widget)
            card_widget.show()  # 명시적으로 표시
            print(f"[CardEditor] Added card: {card_def.name}, visible={card_widget.isVisible()}")

        # 컨테이너 크기 업데이트
        self._card_container.adjustSize()
        print(f"[CardEditor] Container size={self._card_container.size()}")

        # Raw 미리보기 업데이트
        self._update_raw_preview()

    def _clear_cards(self):
        """기존 Card 위젯 제거"""
        for widget in self._card_widgets:
            self._card_layout.removeWidget(widget)
            widget.deleteLater()
        self._card_widgets.clear()

    def _get_keyword_name(self, category: str) -> str:
        """카테고리에서 키워드 이름 추출"""
        mapping = {
            'nodes': 'NODE',
            'shell': 'ELEMENT_SHELL',
            'solid': 'ELEMENT_SOLID',
            'beam': 'ELEMENT_BEAM',
            'parts': 'PART',
            'sections': 'SECTION_SHELL',
            'materials': 'MAT_ELASTIC',
            'contacts': 'CONTACT_AUTOMATIC_SURFACE_TO_SURFACE',
            'sets': 'SET_NODE',
            # Controls
            'termination': 'CONTROL_TERMINATION',
            'timestep': 'CONTROL_TIMESTEP',
            'energy': 'CONTROL_ENERGY',
            'output': 'CONTROL_OUTPUT',
            'hourglass': 'CONTROL_HOURGLASS',
            'bulk_viscosity': 'CONTROL_BULK_VISCOSITY',
            # Databases
            'binary': 'DATABASE_BINARY_D3PLOT',
            'ascii': 'DATABASE_GLSTAT',
            'history_node': 'DATABASE_HISTORY_NODE',
            'history_element': 'DATABASE_HISTORY_SHELL',
            'cross_section': 'DATABASE_CROSS_SECTION_PLANE',
            # Boundaries
            'spc': 'BOUNDARY_SPC_SET',
            'motion': 'BOUNDARY_PRESCRIBED_MOTION_SET',
            # Loads
            'node': 'LOAD_NODE_SET',
            'segment': 'LOAD_SEGMENT',
            'body': 'LOAD_BODY_Z',
            # Initials
            'velocity': 'INITIAL_VELOCITY',
            'stress': 'INITIAL_STRESS_SHELL',
            # Constraineds
            'rigid_body': 'CONSTRAINED_RIGID_BODIES',
            'joint': 'CONSTRAINED_JOINT_REVOLUTE',
            'spotweld': 'CONSTRAINED_SPOTWELD',
        }
        # keyword_type 속성으로 구체적인 타입 확인
        if self._current_item:
            keyword_type = getattr(self._current_item, 'keyword_type', None)
            if keyword_type:
                return keyword_type
        return mapping.get(category, category.upper())

    def _get_header_text(self) -> str:
        """헤더 텍스트 생성"""
        if not self._current_item:
            return ""

        category = self._current_category
        keyword_type = getattr(self._current_item, 'keyword_type', None)

        if category == 'nodes':
            nid = getattr(self._current_item, 'nid', '?')
            return f"*NODE #{nid}"
        elif category == 'parts':
            pid = getattr(self._current_item, 'pid', '?')
            name = getattr(self._current_item, 'name', '')
            return f"*PART #{pid}: {name}"
        elif category in ('shell', 'solid', 'beam'):
            eid = getattr(self._current_item, 'eid', '?')
            return f"*ELEMENT_{category.upper()} #{eid}"
        elif category == 'sections':
            secid = getattr(self._current_item, 'secid', '?')
            kw = keyword_type or 'SECTION'
            return f"*{kw} #{secid}"
        elif category == 'materials':
            mid = getattr(self._current_item, 'mid', '?')
            kw = keyword_type or 'MAT'
            return f"*{kw} #{mid}"
        elif category == 'contacts':
            kw = keyword_type or 'CONTACT'
            return f"*{kw}"
        elif category == 'sets':
            sid = getattr(self._current_item, 'sid', '?')
            kw = keyword_type or 'SET'
            return f"*{kw} #{sid}"
        elif category in ('termination', 'timestep', 'energy', 'output', 'hourglass', 'bulk_viscosity'):
            kw = keyword_type or f'CONTROL_{category.upper()}'
            return f"*{kw}"
        elif category in ('binary', 'ascii', 'history_node', 'history_element', 'cross_section'):
            kw = keyword_type or 'DATABASE'
            return f"*{kw}"
        elif category in ('spc', 'motion'):
            kw = keyword_type or 'BOUNDARY'
            return f"*{kw}"
        elif category in ('node', 'segment', 'body'):
            kw = keyword_type or 'LOAD'
            return f"*{kw}"
        elif category in ('velocity', 'stress'):
            kw = keyword_type or 'INITIAL'
            return f"*{kw}"
        elif category in ('rigid_body', 'joint', 'spotweld'):
            kw = keyword_type or 'CONSTRAINED'
            return f"*{kw}"
        else:
            kw = keyword_type or category.upper()
            return f"*{kw}"

    def _extract_data(self) -> Dict[str, Any]:
        """아이템에서 데이터 추출"""
        data = {}
        if not self._current_item:
            return data

        for attr in dir(self._current_item):
            if attr.startswith('_'):
                continue
            try:
                value = getattr(self._current_item, attr)
                if callable(value):
                    continue

                # nodes 리스트를 n1~n8로 분리
                if attr == 'nodes' and isinstance(value, (list, tuple)):
                    for i, node_id in enumerate(value, 1):
                        data[f'n{i}'] = node_id
                else:
                    data[attr] = value
            except:
                pass

        return data

    def _on_card_value_changed(self, field_name: str, old_value, new_value):
        """Card 필드 값 변경 시 - 실제 데이터 업데이트 (Undo 지원)"""
        if not self._current_item:
            return

        # keywordModified 시그널에 field_name, old_value, new_value 전달
        # module.py에서 keyword_model.modify_item() 호출하여 Undo 스택에 기록
        self.keywordModified.emit(
            self._current_category,
            self._current_item,
            field_name,
            old_value,
            new_value
        )

    def _update_item_attribute(self, field_name: str, value):
        """아이템의 속성 업데이트"""
        if not self._current_item:
            return

        # n1~n8 필드의 경우 nodes 리스트 업데이트
        if field_name.startswith('n') and field_name[1:].isdigit():
            idx = int(field_name[1:]) - 1
            if hasattr(self._current_item, 'nodes'):
                nodes = list(getattr(self._current_item, 'nodes', []))
                # 리스트 확장 필요 시
                while len(nodes) <= idx:
                    nodes.append(0)
                nodes[idx] = value
                try:
                    setattr(self._current_item, 'nodes', nodes)
                except AttributeError:
                    pass  # 읽기 전용 속성일 수 있음
            return

        # 일반 속성 업데이트
        if hasattr(self._current_item, field_name):
            try:
                setattr(self._current_item, field_name, value)
            except AttributeError:
                pass  # 읽기 전용 속성일 수 있음

    def _update_raw_preview(self):
        """Raw K-file 미리보기 업데이트"""
        if not self._current_item:
            return

        lines = self._generate_kfile_text()
        # 시그널 일시 차단
        self._raw_editor.blockSignals(True)
        self._raw_editor.setPlainText('\n'.join(lines))
        self._raw_editor.blockSignals(False)

    def _generate_kfile_text(self) -> List[str]:
        """K-file 형식 텍스트 생성"""
        lines = []
        category = self._current_category

        # 모든 Card에서 값 수집
        all_values = {}
        for card_widget in self._card_widgets:
            all_values.update(card_widget.get_values())

        if category == 'nodes':
            lines.append("*NODE")
            nid = all_values.get('nid', 0)
            x = all_values.get('x', 0.0)
            y = all_values.get('y', 0.0)
            z = all_values.get('z', 0.0)
            lines.append(f"{nid:8d}{x:16.8f}{y:16.8f}{z:16.8f}")

        elif category == 'shell':
            lines.append("*ELEMENT_SHELL")
            eid = all_values.get('eid', 0)
            pid = all_values.get('pid', 0)
            n1 = all_values.get('n1', 0)
            n2 = all_values.get('n2', 0)
            n3 = all_values.get('n3', 0)
            n4 = all_values.get('n4', 0)
            lines.append(f"{eid:8d}{pid:8d}{n1:8d}{n2:8d}{n3:8d}{n4:8d}")

        elif category == 'solid':
            lines.append("*ELEMENT_SOLID")
            eid = all_values.get('eid', 0)
            pid = all_values.get('pid', 0)
            nodes = [all_values.get(f'n{i}', 0) for i in range(1, 9)]
            lines.append(f"{eid:8d}{pid:8d}")
            lines.append(''.join(f"{n:8d}" for n in nodes))

        elif category == 'parts':
            lines.append("*PART")
            name = all_values.get('name', '')
            lines.append(name)
            pid = all_values.get('pid', 0)
            secid = all_values.get('secid', 0)
            mid = all_values.get('mid', 0)
            eosid = all_values.get('eosid', 0)
            hgid = all_values.get('hgid', 0)
            grav = all_values.get('grav', 0)
            adpopt = all_values.get('adpopt', 0)
            tmid = all_values.get('tmid', 0)
            lines.append(f"{pid:10d}{secid:10d}{mid:10d}{eosid:10d}{hgid:10d}{grav:10d}{adpopt:10d}{tmid:10d}")

        elif category == 'sections':
            keyword_type = getattr(self._current_item, 'keyword_type', 'SECTION_SHELL')
            lines.append(f"*{keyword_type}")

            if keyword_type == 'SECTION_SHELL':
                secid = all_values.get('secid', 0)
                elform = all_values.get('elform', 2)
                shrf = all_values.get('shrf', 1.0)
                nip = all_values.get('nip', 2)
                propt = all_values.get('propt', 0)
                qr_irid = all_values.get('qr_irid', 0)
                icomp = all_values.get('icomp', 0)
                setyp = all_values.get('setyp', 1)
                lines.append(f"{secid:10d}{elform:10d}{shrf:10.4f}{nip:10d}{propt:10d}{qr_irid:10d}{icomp:10d}{setyp:10d}")

                t1 = all_values.get('t1', 0.0)
                t2 = all_values.get('t2', 0.0)
                t3 = all_values.get('t3', 0.0)
                t4 = all_values.get('t4', 0.0)
                nloc = all_values.get('nloc', 0.0)
                marea = all_values.get('marea', 0.0)
                idof = all_values.get('idof', 0.0)
                edgset = all_values.get('edgset', 0.0)
                lines.append(f"{t1:10.4f}{t2:10.4f}{t3:10.4f}{t4:10.4f}{nloc:10.4f}{marea:10.4f}{idof:10.4f}{edgset:10.4f}")

            elif keyword_type == 'SECTION_SOLID':
                secid = all_values.get('secid', 0)
                elform = all_values.get('elform', 1)
                aet = all_values.get('aet', 0)
                lines.append(f"{secid:10d}{elform:10d}{aet:10d}")

            elif keyword_type == 'SECTION_BEAM':
                secid = all_values.get('secid', 0)
                elform = all_values.get('elform', 1)
                shrf = all_values.get('shrf', 1.0)
                qr_irid = all_values.get('qr_irid', 0)
                cst = all_values.get('cst', 0)
                scoor = all_values.get('scoor', 0.0)
                nsm = all_values.get('nsm', 0.0)
                lines.append(f"{secid:10d}{elform:10d}{shrf:10.4f}{qr_irid:10d}{cst:10d}{scoor:10.4f}{nsm:10.4f}")

                ts1 = all_values.get('ts1', 0.0)
                ts2 = all_values.get('ts2', 0.0)
                tt1 = all_values.get('tt1', 0.0)
                tt2 = all_values.get('tt2', 0.0)
                nsloc = all_values.get('nsloc', 0.0)
                ntloc = all_values.get('ntloc', 0.0)
                lines.append(f"{ts1:10.4f}{ts2:10.4f}{tt1:10.4f}{tt2:10.4f}{nsloc:10.4f}{ntloc:10.4f}")

        elif category == 'materials':
            keyword_type = getattr(self._current_item, 'keyword_type', 'MAT_ELASTIC')
            lines.append(f"*{keyword_type}")

            # 공통 필드: MID, RO
            mid = all_values.get('mid', 0)
            ro = all_values.get('ro', 0.0)

            if keyword_type == 'MAT_ELASTIC':
                e = all_values.get('e', 0.0)
                pr = all_values.get('pr', 0.0)
                da = all_values.get('da', 0.0)
                db = all_values.get('db', 0.0)
                k = all_values.get('k', 0.0)
                lines.append(f"{mid:10d}{ro:10.4e}{e:10.4e}{pr:10.4f}{da:10.4f}{db:10.4f}{k:10.4e}")

            elif keyword_type == 'MAT_PLASTIC_KINEMATIC':
                e = all_values.get('e', 0.0)
                pr = all_values.get('pr', 0.0)
                sigy = all_values.get('sigy', 0.0)
                etan = all_values.get('etan', 0.0)
                beta = all_values.get('beta', 0.0)
                src = all_values.get('src', 0.0)
                lines.append(f"{mid:10d}{ro:10.4e}{e:10.4e}{pr:10.4f}{sigy:10.4e}{etan:10.4e}{beta:10.4f}{src:10.4f}")
                srp = all_values.get('srp', 0.0)
                fs = all_values.get('fs', 0.0)
                vp = all_values.get('vp', 0.0)
                lines.append(f"{srp:10.4f}{fs:10.4f}{vp:10.4f}")

            elif keyword_type == 'MAT_PIECEWISE_LINEAR_PLASTICITY':
                e = all_values.get('e', 0.0)
                pr = all_values.get('pr', 0.0)
                sigy = all_values.get('sigy', 0.0)
                etan = all_values.get('etan', 0.0)
                fail = all_values.get('fail', 0.0)
                tdel = all_values.get('tdel', 0.0)
                lines.append(f"{mid:10d}{ro:10.4e}{e:10.4e}{pr:10.4f}{sigy:10.4e}{etan:10.4e}{fail:10.4f}{tdel:10.4f}")
                c = all_values.get('c', 0.0)
                p = all_values.get('p', 0.0)
                lcss = all_values.get('lcss', 0)
                lcsr = all_values.get('lcsr', 0)
                vp = all_values.get('vp', 0.0)
                lines.append(f"{c:10.4f}{p:10.4f}{lcss:10d}{lcsr:10d}{vp:10.4f}")

            elif keyword_type == 'MAT_RIGID':
                e = all_values.get('e', 0.0)
                pr = all_values.get('pr', 0.0)
                n = all_values.get('n', 0.0)
                couple = all_values.get('couple', 0.0)
                m = all_values.get('m', 0.0)
                alias = all_values.get('alias', 0.0)
                lines.append(f"{mid:10d}{ro:10.4e}{e:10.4e}{pr:10.4f}{n:10.4f}{couple:10.4f}{m:10.4f}{alias:10.4f}")
                cmo = all_values.get('cmo', 0.0)
                con1 = all_values.get('con1', 0)
                con2 = all_values.get('con2', 0)
                lines.append(f"{cmo:10.4f}{con1:10d}{con2:10d}")

            elif keyword_type in ('MAT_ORTHOTROPIC_ELASTIC', 'MAT_COMPOSITE_DAMAGE', 'MAT_ENHANCED_COMPOSITE_DAMAGE'):
                ea = all_values.get('ea', 0.0)
                eb = all_values.get('eb', 0.0)
                ec = all_values.get('ec', 0.0)
                prba = all_values.get('prba', 0.0)
                prca = all_values.get('prca', 0.0)
                prcb = all_values.get('prcb', 0.0)
                lines.append(f"{mid:10d}{ro:10.4e}{ea:10.4e}{eb:10.4e}{ec:10.4e}{prba:10.4f}{prca:10.4f}{prcb:10.4f}")
                gab = all_values.get('gab', 0.0)
                gbc = all_values.get('gbc', 0.0)
                gca = all_values.get('gca', 0.0)
                aopt = all_values.get('aopt', 0.0)
                lines.append(f"{gab:10.4e}{gbc:10.4e}{gca:10.4e}{aopt:10.4f}")

            elif keyword_type == 'MAT_NULL':
                pc = all_values.get('pc', 0.0)
                mu = all_values.get('mu', 0.0)
                terod = all_values.get('terod', 0.0)
                cerod = all_values.get('cerod', 0.0)
                ym = all_values.get('ym', 0.0)
                pr = all_values.get('pr', 0.0)
                lines.append(f"{mid:10d}{ro:10.4e}{pc:10.4f}{mu:10.4f}{terod:10.4f}{cerod:10.4f}{ym:10.4e}{pr:10.4f}")

            else:
                # 기본: 모든 값을 한 줄에 출력
                lines.append(f"{mid:10d}{ro:10.4e}")

        elif category == 'contacts':
            keyword_type = getattr(self._current_item, 'keyword_type', 'CONTACT_AUTOMATIC_SURFACE_TO_SURFACE')
            lines.append(f"*{keyword_type}")
            ssid = all_values.get('ssid', 0)
            msid = all_values.get('msid', 0)
            sstyp = all_values.get('sstyp', 0)
            mstyp = all_values.get('mstyp', 0)
            sboxid = all_values.get('sboxid', 0)
            mboxid = all_values.get('mboxid', 0)
            spr = all_values.get('spr', 0)
            mpr = all_values.get('mpr', 0)
            lines.append(f"{ssid:10d}{msid:10d}{sstyp:10d}{mstyp:10d}{sboxid:10d}{mboxid:10d}{spr:10d}{mpr:10d}")
            fs = all_values.get('fs', 0.0)
            fd = all_values.get('fd', 0.0)
            dc = all_values.get('dc', 0.0)
            vc = all_values.get('vc', 0.0)
            lines.append(f"{fs:10.4f}{fd:10.4f}{dc:10.4f}{vc:10.4f}")

        elif category == 'sets':
            keyword_type = getattr(self._current_item, 'keyword_type', 'SET_NODE')
            lines.append(f"*{keyword_type}")
            sid = all_values.get('sid', 0)
            da1 = all_values.get('da1', 0.0)
            da2 = all_values.get('da2', 0.0)
            da3 = all_values.get('da3', 0.0)
            da4 = all_values.get('da4', 0.0)
            lines.append(f"{sid:10d}{da1:10.4f}{da2:10.4f}{da3:10.4f}{da4:10.4f}")

        elif category in ('termination', 'timestep', 'energy', 'output', 'hourglass', 'bulk_viscosity'):
            keyword_type = getattr(self._current_item, 'keyword_type', f'CONTROL_{category.upper()}')
            lines.append(f"*{keyword_type}")
            # 공통 출력 - Card에서 수집한 모든 값 출력
            values_line = ''.join(f"{v:10.4f}" if isinstance(v, float) else f"{v:10d}"
                                 for v in list(all_values.values())[:8])
            if values_line:
                lines.append(values_line)

        elif category in ('binary', 'ascii', 'history_node', 'history_element', 'cross_section'):
            keyword_type = getattr(self._current_item, 'keyword_type', 'DATABASE')
            lines.append(f"*{keyword_type}")
            dt = all_values.get('dt', 0.0)
            binary = all_values.get('binary', 0)
            lines.append(f"{dt:10.4e}{binary:10d}")

        elif category in ('spc', 'motion'):
            keyword_type = getattr(self._current_item, 'keyword_type', 'BOUNDARY_SPC_SET')
            lines.append(f"*{keyword_type}")
            if 'nsid' in all_values:
                nsid = all_values.get('nsid', 0)
                lines.append(f"{nsid:10d}")
            elif 'nid' in all_values:
                nid = all_values.get('nid', 0)
                lines.append(f"{nid:10d}")

        elif category in ('node', 'segment', 'body'):
            keyword_type = getattr(self._current_item, 'keyword_type', 'LOAD')
            lines.append(f"*{keyword_type}")
            lcid = all_values.get('lcid', 0)
            sf = all_values.get('sf', 1.0)
            lines.append(f"{lcid:10d}{sf:10.4f}")

        elif category in ('velocity', 'stress'):
            keyword_type = getattr(self._current_item, 'keyword_type', 'INITIAL_VELOCITY')
            lines.append(f"*{keyword_type}")
            vx = all_values.get('vx', 0.0)
            vy = all_values.get('vy', 0.0)
            vz = all_values.get('vz', 0.0)
            lines.append(f"{vx:10.4e}{vy:10.4e}{vz:10.4e}")

        elif category in ('rigid_body', 'joint', 'spotweld'):
            keyword_type = getattr(self._current_item, 'keyword_type', 'CONSTRAINED')
            lines.append(f"*{keyword_type}")
            # 간단한 출력
            values_line = ''.join(f"{v:10.4f}" if isinstance(v, float) else f"{v:10d}"
                                 for v in list(all_values.values())[:8])
            if values_line:
                lines.append(values_line)

        elif category == 'beam':
            lines.append("*ELEMENT_BEAM")
            eid = all_values.get('eid', 0)
            pid = all_values.get('pid', 0)
            n1 = all_values.get('n1', 0)
            n2 = all_values.get('n2', 0)
            n3 = all_values.get('n3', 0)
            lines.append(f"{eid:8d}{pid:8d}{n1:8d}{n2:8d}{n3:8d}")

        else:
            # 일반 키워드 - keyword_type으로 출력
            keyword_type = getattr(self._current_item, 'keyword_type', category.upper())
            lines.append(f"*{keyword_type}")
            # Card에서 수집한 값들 출력
            for field_name, value in list(all_values.items())[:8]:
                if isinstance(value, float):
                    lines.append(f"$ {field_name}: {value:.6g}")
                else:
                    lines.append(f"$ {field_name}: {value}")

        return lines

    def _generate_range_kfile(self, category: str, items: list) -> List[str]:
        """범위 항목들의 K-file 텍스트 생성"""
        lines = []
        max_items = 100

        if category == 'nodes':
            lines.append("*NODE")
            for item in items[:max_items]:
                nid = getattr(item, 'nid', 0)
                x = getattr(item, 'x', 0.0)
                y = getattr(item, 'y', 0.0)
                z = getattr(item, 'z', 0.0)
                lines.append(f"{nid:8d}{x:16.8f}{y:16.8f}{z:16.8f}")

        elif category in ('shell', 'solid'):
            lines.append(f"*ELEMENT_{category.upper()}")
            for item in items[:max_items]:
                eid = getattr(item, 'eid', 0)
                pid = getattr(item, 'pid', 0)
                nodes = getattr(item, 'nodes', [])
                if category == 'shell':
                    nodes_padded = list(nodes) + [0] * (4 - len(nodes))
                    lines.append(f"{eid:8d}{pid:8d}" + ''.join(f"{n:8d}" for n in nodes_padded[:4]))
                else:
                    nodes_padded = list(nodes) + [0] * (8 - len(nodes))
                    lines.append(f"{eid:8d}{pid:8d}" + ''.join(f"{n:8d}" for n in nodes_padded[:8]))

        if len(items) > max_items:
            lines.append(f"$ ... 외 {len(items) - max_items:,}개 더")

        return lines

    def _on_raw_text_changed(self):
        """Raw 텍스트 변경 시 (사용자가 직접 편집)"""
        # TODO: 파싱하여 Card 필드 업데이트
        pass

    def clear(self):
        """편집기 초기화"""
        self._current_category = ""
        self._current_item = None
        self._clear_cards()
        self._header.setText("키워드를 선택하세요")
        self._raw_editor.setPlainText("")
