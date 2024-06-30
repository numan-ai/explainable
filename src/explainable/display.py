from typing import Any
from dataclasses import dataclass


@dataclass
class DisplayBaseValue:
    pass


@dataclass
class DisplayValueField(DisplayBaseValue):
    name: str
    type: str = "field"


@dataclass
class DisplayValueConstant(DisplayBaseValue):
    value: Any
    type: str = "constant"


@dataclass
class DisplayOptions:
    data_type: str
    params: dict[str, Any]


DISPLAY_REGISTRY: dict[str, DisplayOptions] = {}


def display_as(data_type: str, *args, **kwargs):
    def decorator(cls):
        options = DisplayOptions(data_type=data_type, params={
            "items": args[0],
        })
        DISPLAY_REGISTRY[cls.__name__] = options

        return cls
    
    return decorator


def constant(value: Any) -> Any:
    return DisplayValueConstant(value=value)


def field(name: str) -> Any:
    return DisplayValueField(name=name)
