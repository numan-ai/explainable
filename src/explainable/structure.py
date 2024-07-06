from dataclasses import dataclass

from explainable.base_entities import BaseStructure


@dataclass
class String(BaseStructure):
    """ Structure that represents string value """
    value: any


@dataclass
class Number(BaseStructure):
    """ Structure that represents string value """
    value: any


@dataclass
class List(BaseStructure):
    """ Structure that represents a list of other structures """
    data: list[BaseStructure]


@dataclass
class Dict(BaseStructure):
    """ Structure that represents a dictionary of other structures """
    keys: list[BaseStructure]
    values: list[BaseStructure]
