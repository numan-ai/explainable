from dataclasses import dataclass
from typing import Optional

from explainable.base_entities import (
    BaseSource,
    BaseWidget, 
    BaseStyle,
)
from explainable.source import BaseSource


@dataclass
class StringWidget(BaseWidget):
    """ Visually represents any structure as a string
    Any structure can be represented using the "format" field.
    Formats use references based on the structure passed to this
      widget. 
    Example of a format: "{item.name}: {item.age}"
    This format will result in a string like "Mike: 12"
    In order to have a "{" or "}" character in the format escape it
      like this "{{" or "}}" accordingly.
    """
    source: Optional[BaseSource] = None
    max_size: Optional[int] = None
    format: str = "{item}"
    type: str = "string"


@dataclass
class NumberWidget(BaseWidget):
    """ Visually represents number structure
    Can round the represented number. 
    """
    source: BaseSource
    round: Optional[int] = None
    separation: bool = False
    type: str = "number"


@dataclass
class ListWidget(BaseWidget):
    """ Visually represents multiple structures in a row """
    source: Optional[BaseSource | list[BaseSource]] = None
    item_widget: Optional[BaseWidget | list[BaseWidget]] = None
    style: Optional[BaseStyle] = None
    type: str = "list"


@dataclass
class DictWidget(BaseWidget):
    """ Visually represents multiple structures in a row """
    source: Optional[BaseSource | list[BaseSource]] = None
    item_widget: Optional[BaseWidget | list[BaseWidget]] = None
    type: str = "dict"


@dataclass
class VerticalListWidget(ListWidget):
    """ Visually represents multiple structures in a column """
    type: str = "vlist"


@dataclass
class GraphNode:
    """ Node configuration for the graph widget """
    source: Optional[BaseSource] = None
    id: Optional[BaseSource] = None
    widget: Optional[BaseWidget] = None



@dataclass
class GraphEdge:
    """ Edge configuration for the graph widget """
    source: BaseSource
    start: BaseSource
    end: BaseSource
    id: Optional[BaseSource] = None
    label: Optional[BaseSource] = None
    weight: Optional[BaseSource] = None


@dataclass
class GraphWidget(BaseWidget):
    """ Visually represents multiple structures as a graph
    Connects those structures with arrows
    """
    nodes: GraphNode
    edges: GraphEdge
    type: str = "graph"


@dataclass
class TileWidget(BaseWidget):
    """ Visually represents multiple structures as a tile
    Connects those structures with arrows
    """
    width: Optional[BaseSource] = None
    height: Optional[BaseSource] = None
    color: Optional[BaseSource] = None
    type: str = "tile"


@dataclass
class Style(BaseStyle):
    margin: int = None
    spacing: int = None