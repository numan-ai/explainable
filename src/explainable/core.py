import inspect
import logging
import dataclasses

from typing import Any, Callable, Optional, Self
from collections import UserDict, UserList, defaultdict
from dataclasses import dataclass, field, is_dataclass

from . import server


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

META_OBJECT_PROPERTY = "_explainable"


def _on_value_being_set(obj, key, value, previoius_value):
    expl = getattr(obj, META_OBJECT_PROPERTY, None)
    if expl and (expl.parents or expl.views):
        send_updates(
            obj,
            key,
            value,
            previoius_value,
        )
    
    if isinstance(value, dict):
        value = ExplainableDict(value)
    elif isinstance(value, list):
        value = ExplainableList(value)
    elif is_dataclass(value):
        make_observable(type(value))
        if not hasattr(value, META_OBJECT_PROPERTY):
            metadata = MetaData(initialised=True)
            super(type(value), value).__setattr__(META_OBJECT_PROPERTY, metadata)

    if hasattr(value, META_OBJECT_PROPERTY):
        value_expl = getattr(value, META_OBJECT_PROPERTY)
        value_expl.parents.append((key, expl))

    return value


@dataclass
class MetaData:
    initialised: bool = False
    old_post_init: Optional[Callable] = None
    old_setattr: Optional[Callable] = None
    views: set[str] = field(default_factory=set)
    parents: list[tuple[str, Self]] = field(default_factory=list)

    def get_path_list(self, base_path) -> dict[str, set[str]]:
        paths = defaultdict(set)

        for parent_name, parent_explainable in self.parents:
            new_paths = parent_explainable.get_path_list(base_path=f"data.{parent_name}.{base_path}")
            for key, value in new_paths.items():
                paths[key].update(value)
        
        if self.views:
            for view in self.views:
                paths[view].add(base_path)

        return paths


def send_updates(obj, key, value, previoius_value):
    expl = getattr(obj, META_OBJECT_PROPERTY)
    paths = expl.get_path_list(f"data.{key}")

    for view, path_set in paths.items():
        for path in list(path_set):
            server.send_update("diff", data={
                "view_id": view,
                "type": "setValue",
                "path": path,
                "value": serialize(value, path="diff"),
                "previoiusValue": serialize(previoius_value, path="diff"),
            })


class ExplainableDict(UserDict):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__setattr__(META_OBJECT_PROPERTY, MetaData(initialised=True))
        super().__init__(data)

    def __setitem__(self, key, value):
        value = _on_value_being_set(self, key, value, self.get(key, None))
        super().__setitem__(key, value)


class ExplainableList(UserList):
    def __init__(self, data: list[Any]) -> None:
        super().__setattr__(META_OBJECT_PROPERTY, MetaData(initialised=True))
        super().__init__(data)

    def __setitem__(self, key, value):
        try:
            old_value = self[key]
        except IndexError:
            old_value = None

        value = _on_value_being_set(self, key, value, old_value)
        super().__setitem__(key, value)
    
    def append(self, value):
        raise NotImplementedError()
        super().append(value)

    def insert(self, index, value):
        raise NotImplementedError()
        super().insert(index, value)

    def extend(self, values):
        raise NotImplementedError()
        super().extend(values)

    def remove(self, value):
        raise NotImplementedError()
        super().remove(value)

    def pop(self, index):
        raise NotImplementedError()
        return super().pop(index)
    
    def clear(self):
        raise NotImplementedError()
        super().clear()

    def sort(self, key=None, reverse=False):
        raise NotImplementedError()
        super().sort(key=key, reverse=reverse)

    def reverse(self):
        raise NotImplementedError()
        super().reverse()

    def __delitem__(self, key):
        raise NotImplementedError()
        super().__delitem__(key)


def serialize(obj: Any, path) -> dict[str, Any]:
    if is_dataclass(obj):
        return {
            "type": "object",
            "struct_id": path,
            "subtype": type(obj).__name__,
            "data": {
                field.name: serialize(getattr(obj, field.name), path=f"{path}.{field.name}")
                for field in dataclasses.fields(obj)
            },
        }
    elif isinstance(obj, (int, float)):
        return {
            "type": "number",
            "struct_id": path,
            "value": obj,
        }
    elif isinstance(obj, str):
        return {
            "type": "string",
            "struct_id": path,
            "value": obj,
        }
    elif isinstance(obj, (list, ExplainableList)):
        return {
            "type": "array", 
            "struct_id": path,
            "data": [
                serialize(item, path=f"{path}.{idx}")
                for idx, item in enumerate(obj)
            ],
        }
    elif isinstance(obj, (dict, ExplainableDict)):
        return {
            "type": "map",
            "struct_id": path,
            "data": {
                key: serialize(value, path=f"{path}.{key}")
                for key, value in obj.items()
            },
        }
    elif obj is None:
        return {
            "type": "null",
            "struct_id": path,
            "data": {},
        }
    elif hasattr(obj, "serialize_explainable"):
        return obj.serialize_explainable(serialize)
    else:
        raise NotImplementedError(f"Unknown type: {type(obj)}")


def make_observable(cls) -> type:
    assert inspect.isclass(cls)

    if hasattr(cls, "__old_setattr"):
        return cls

    def __new_new__(cls, *args, **kwargs) -> None:
        instance = cls.__old_new(cls)
        super(cls, instance).__setattr__(META_OBJECT_PROPERTY, MetaData(
            initialised=False,
        ))

        return instance

    def __new_post_init__(self) -> None:
        if self.__old_post_init is not None:
            self.__old_post_init()

    def __new_setattr__(self, name: str, value: Any) -> None:
        value = _on_value_being_set(
            self, name, value, getattr(self, name, None)
        )
        
        if self.__old_setattr is not None:
            self.__old_setattr(name, value)
        else:
            raise RuntimeError("No old setattr")

    cls.__old_new = getattr(cls, "__new__")
    cls.__old_post_init = getattr(cls, "__post_init__", None)
    cls.__old_setattr = getattr(cls, f"__setattr__", None)
    cls.__post_init__ = __new_post_init__
    cls.__setattr__ = __new_setattr__
    cls.__new__ = __new_new__

    return cls



def _deep_make_observable(obj: Any) -> None:
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    
    if isinstance(obj, list):
        obj = ExplainableList(obj)
    elif isinstance(obj, dict):
        obj = ExplainableDict(obj)
    
    if not hasattr(obj, META_OBJECT_PROPERTY):
        super(type(obj), obj).__setattr__(META_OBJECT_PROPERTY, MetaData(initialised=True))

    if is_dataclass(obj):
        make_observable(type(obj))
        for field in dataclasses.fields(obj):
            value = getattr(obj, field.name)
            if value is not None:
                value = _deep_make_observable(value)
            setattr(obj, field.name, value)

    elif isinstance(obj, ExplainableList):
        for idx, value in enumerate(obj):
            obj[idx] = _deep_make_observable(value)

    elif isinstance(obj, ExplainableDict):
        for key, value in obj.items():
            obj[key] = _deep_make_observable(value)

    return obj


def observe(view_id: str, obj: Any) -> None:    
    if not server.ENABLED:
        logger.debug()
        return obj
    
    obj = _deep_make_observable(obj)
    expl = getattr(obj, META_OBJECT_PROPERTY)
    expl.views.add(view_id)

    server.send_update(
        "snapshot",
        data={
            "view_id": view_id,
            "is_paused": server.PAUSED,
            "settings": {
                "view_id": view_id,
            },
            "structure": serialize(obj, path=view_id),
        }
    )
    expl.initialised = True

    return obj
