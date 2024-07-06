from dataclasses import dataclass
from typing import Optional

from explainable.base_entities import (
    BaseSource,
    BaseWidget, 
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
    max_size: Optional[int] = None
    format: str = "{item}"
    type: str = "string"


@dataclass
class NumberWidget(BaseWidget):
    """ Visually represents number structure
    Can round the represented number. 
    """
    round: Optional[int] = None
    type: str = "number"


@dataclass
class ListWidget(BaseWidget):
    """ Visually represents multiple structures in a row """
    source: BaseSource | list[BaseSource]
    item_widget: Optional[BaseWidget | list[BaseWidget]] = None
    type: str = "list"


@dataclass
class VerticalListWidget(ListWidget):
    """ Visually represents multiple structures in a column """
    pass


@dataclass
class GraphNode:
    """ Node configuration for the graph widget """
    source: BaseSource
    id: BaseSource
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