'''
DocumentSpec is a bunch of classes that defines things about the page for the engines to refer to as well as some defaults.
'''
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple
import uuid
import random


@dataclass(frozen=True, slots=True)
class BBox:
    x: float
    y: float
    w: float
    h: float

    @property
    def x2(self) -> float:
        return self.x + self.w

    @property
    def y2(self) -> float:
        return self.y + self.h


@dataclass(frozen=True, slots=True)
class ColorRGB:
    r: float
    g: float
    b: float

TextAlign = Literal['left', 'center', 'right']


@dataclass(frozen=True, slots=True)
class FontSpec:
    name: str
    ttf_path: Optional[str] = None


@dataclass(frozen=True, slots=True)
class StyleSpec:
    font_name: str = 'Helvetica'
    font_size: float = 10.0
    fill: ColorRGB = ColorRGB(0.0, 0.0, 0.0)
    stroke: ColorRGB = ColorRGB(0.0, 0.0, 0.0)
    line_width: float = 1.0
    align: TextAlign = 'left'
    leading: Optional[float] = None

BlockKind = Literal['text', 'rect', 'line', 'image'] 


@dataclass(frozen=True, slots=True)
class BlockSpec:
    block_id: str
    kind: BlockKind
    bbox: BBox
    style: StyleSpec = field(default_factory=StyleSpec)
    content: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PageSpec:
    page_id: str
    blocks: List[BlockSpec] = field(default_factory=list)
    size: Optional[Tuple[float, float]] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    doc_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    version: str = '0.1'
    seed: Optional[int] = None

    page_size: Tuple[float, float] = (612.0, 792.0)
    page_margin: Optional[Tuple[float, float, float, float]] = None
    pages: List[PageSpec] = field(default_factory=list)

    fonts: Dict[str, FontSpec] = field(default_factory=dict)
    assets: Dict[str, str] = field(default_factory=dict)

    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__ (self) -> None:
        if self.seed is None:
            object.__setattr__(self, 'seed', random.SystemRandom().randint(0, 2**31 - 1)

        if not self.pages:
            object.__setattr__(self, 'pages', [PageSpec(page_id='page_1')]


@dataclass(frozen=True, slots=True)
class GTToken:
    text: str
    bbox: BBox
    page_id: str
    block_id: str
    order: int


@dataclass(frozen=True, slots=True)
class GroundTruth:
    tokens: List[GTToken] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)


def make_block_id(prefix: str='blk') -> str:
    return f'{prefix}_{uuid.uuid4().hex[:8]}'
    
