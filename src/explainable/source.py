from dataclasses import dataclass
from typing import Optional
from explainable.base_entities import BaseSource


@dataclass
class Reference(BaseSource):
    """ Reference to a structure 

    Current view can be referenced using "$":
      "$.name" will take a field "name" of the current view
    
    Any view can be referenced by its id:
      "my_view.name" will take a field "name" 
        from the view with id "my_view"
    
    Relative references must start with "item.":
      When referencing a structure of a single item of an list
      use "item" as a reference path. 
      Fields can be accessed as usual: "item.name".
    """
    path: str
    type: str = "ref"


@dataclass
class Min(BaseSource):
    """ Creates a number structure
    Its value is the minimum value of the two structures
    """
    first: BaseSource
    second: BaseSource
    type: str = "min"


@dataclass
class Max(BaseSource):
    """ Creates a number structure
    Its value is the maximum value of the two structures
    """
    first: BaseSource
    second: BaseSource
    type: str = "max"


@dataclass
class String(BaseSource):
    """ Creates a string structure """
    format: str
    type: str = "string"


@dataclass
class Number(BaseSource):
    """ Creates a number structure """
    value: float
    round: Optional[bool] = None
    separation: bool = False
    type: str = "number"


@dataclass
class MathAdd(BaseSource):
    """ Creates a number structure
    Its value is the addition of the two structures
    """
    first: BaseSource
    second: BaseSource
    type: str = "addition"


@dataclass
class MathSub(BaseSource):
    """ Creates a number structure
    Its value is the subtraction of the two structures
    """
    first: BaseSource
    second: BaseSource
    type: str = "subtraction"


@dataclass
class MathMul(BaseSource):
    """ Creates a number structure
    Its value is the multiplication of the two structures
    """
    first: BaseSource
    second: BaseSource
    type: str = "multiplication"


@dataclass
class MathDiv(BaseSource):
    """ Creates a number structure
    Its value is the division of the two structures
    """
    first: BaseSource
    second: BaseSource
    type: str = "division"
