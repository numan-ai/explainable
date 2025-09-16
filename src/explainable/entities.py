from dataclasses import dataclass, field
from typing import Any, NotRequired, Optional, TypedDict


@dataclass
class Node:
    data: Any
    object_id: str = ""
    widget: str = ""
    default_x: float = 100.0
    default_y: float = 100.0
    is_draggable: bool = True


class TextNodeData(TypedDict):
    text: str
    width: NotRequired[int]
    height: NotRequired[int]
    background: NotRequired[str]
    foreground: NotRequired[str]


@dataclass
class TextNode(Node):
    data: TextNodeData = field(default_factory=lambda: TextNodeData(text="", width=None, height=None))
    widget: str = "text"


class NumberNodeData(TypedDict):
    value: float


@dataclass
class NumberNode(Node):
    data: NumberNodeData = field(default_factory=lambda: NumberNodeData(value=0.0))
    widget: str = "number"


class RowNodeData(TypedDict):
    children: list[Node]


@dataclass
class RowNode(Node):
    data: RowNodeData = field(default_factory=lambda: RowNodeData(children=[]))
    widget: str = "row"


class ColumnNodeData(TypedDict):
    children: list[Node]


@dataclass
class ColumnNode(Node):
    data: ColumnNodeData = field(default_factory=lambda: ColumnNodeData(children=[]))
    widget: str = "column"


class PixelNodeData(TypedDict):
    color: str
    size: NotRequired[int] = None
    width: NotRequired[int] = None
    height: NotRequired[int] = None


@dataclass
class PixelNode(Node):
    data: PixelNodeData = field(default_factory=lambda: PixelNodeData(color="", size=None, width=None, height=None))
    widget: str = "pixel"


class LineChartNodeData(TypedDict):
    data: list[tuple[float, float]]


@dataclass
class LineChartNode(Node):
    data: LineChartNodeData = field(default_factory=lambda: LineChartNodeData(data=[]))
    widget: str = "linechart"


class ClickableExclusiveNodeData(TypedDict):
    group: str
    widget: Node


@dataclass
class ClickableExclusiveNode(Node):
    data: ClickableExclusiveNodeData = field(default_factory=lambda: ClickableExclusiveNodeData(group="", widget=TextNode()))
    widget: str = "clickable_exclusive"


@dataclass
class Edge:
    edge_id: str
    node_start_id: str
    node_end_id: str
    data: Any = None
    line_width: float = 2.0
    line_color: str = '#fff'
    label_color: str = '#fff'
    widget: str = "edge"


@dataclass
class ClickableExclusiveEdge(Edge):
    edge_id: str
    node_start_id: str
    node_end_id: str
    data: Any = None
    line_width: float = 2.0
    line_color: str = '#fff'
    label_color: str = '#fff'
    widget: str = "clickable_exclusive_edge"
