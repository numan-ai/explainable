from dataclasses import dataclass
from typing import Any


@dataclass
class Node:
    data: Any
    object_id: str = ""
    widget: str = ""
    default_x: float = 100.0
    default_y: float = 100.0
    is_draggable: bool = True


@dataclass
class TextNode(Node):
    widget: str = "text"


@dataclass
class NumberNode(Node):
    widget: str = "number"


@dataclass
class RowNode(Node):
    widget: str = "row"


@dataclass
class ColumnNode(Node):
    widget: str = "column"


@dataclass
class PixelNode(Node):
    widget: str = "pixel"


@dataclass
class LineChartNode(Node):
    widget: str = "linechart"


@dataclass
class ClickableExclusiveNode(Node):
    """
    data:
        - group: str
        - widget: Node
    """
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
