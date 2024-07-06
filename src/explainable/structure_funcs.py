from dataclasses import dataclass
from explainable.base_entities import BaseStructure, BaseStructureFunction


@dataclass
class ref(BaseStructureFunction):
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


@dataclass
class number_min(BaseStructureFunction):
    """ Creates a number structure
    Its value is the minimum value of the two structures
    """
    first: BaseStructure
    second: BaseStructure


@dataclass
class number_max(number_min):
    """ Creates a number structure
    Its value is the maximum value of the two structures
    """
    pass


@dataclass
class list_min(BaseStructureFunction):
    """ Creates a number structure
    Its value is the minimum value of a list structure
    """
    value: BaseStructure


@dataclass
class list_max(list_min):
    """ Creates a number structure
    Its value is the maximum value of a list structure
    """
    pass
