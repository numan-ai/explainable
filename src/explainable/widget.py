from dataclasses import dataclass
from typing import Optional

from explainable.base_entities import (
    BaseWidget, 
    BaseStructure,
)
from explainable.structure_funcs import BaseStructureFunction


@dataclass
class StringWidge(BaseWidget):
    """ Visually represents any structure as a string
    Any structure can be represented using the "format" field.
    Formats use references based on the structure passed to this
      component. 
    Example of a format: "{item.name}: {item.age}"
    This format will result in a string like "Mike: 12"
    In order to have a "{" or "}" character in the format escape it
      like this "{{" or "}}" accordingly.
    """
    max_size: Optional[int] = None
    format: str = "{item}"


@dataclass
class NumberWidget(BaseWidget):
    """ Visually represents number structure
    Can round the represented number. 
    """
    round: Optional[int] = None


@dataclass
class ListWidget(BaseWidget):
    """ Visually represents multiple structures in a row """
    source: BaseStructure | list
    component_list: Optional[list[BaseWidget]] = None
    item_component: Optional[BaseWidget] = None


@dataclass
class VerticalListWidget(ListWidget):
    """ Visually represents multiple structures in a column """
    pass


@dataclass
class GraphNodeWidget(BaseWidget):
    """ Node configuration for the graph widget """
    source: BaseStructure
    id: BaseStructureFunction
    component: Optional[BaseWidget] = None



@dataclass
class GraphEdgeComponent(BaseWidget):
    """ Edge configuration for the graph component """
    source: BaseStructure
    start: BaseStructureFunction
    end: BaseStructureFunction
    id: Optional[BaseStructureFunction] = None
    label: Optional[BaseStructureFunction] = None
    weight: Optional[BaseStructureFunction] = None
    component: Optional[BaseWidget] = None


@dataclass
class GraphComponent(BaseWidget):
    """ Visually represents multiple structures as a graph
    Connects those structures with arrows
    """
    node: GraphNodeWidget
    edge: GraphEdgeComponent
