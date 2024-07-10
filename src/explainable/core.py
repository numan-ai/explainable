import inspect
import logging
import dataclasses

from typing import Any, Callable, Optional, Self
from collections import UserDict, UserList, defaultdict
from dataclasses import dataclass, field, is_dataclass
import weakref

from explainable import display, source, widget
from explainable.base_entities import BaseWidget
from explainable.server import CONFIG as server_config

from . import server


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

META_OBJECT_PROPERTY = "_explainable"


def _on_value_being_set(obj, key, value, previoius_value):
    expl = getattr(obj, META_OBJECT_PROPERTY, None)
    if expl and (expl.parents or expl.views):
        prev_ser = serialize(previoius_value, path="diff") if server_config.history_enabled else None
        upd = {
            "type": "setValue",
            "value": serialize(value, path="diff"),
            "previoiusValue": prev_ser,
        }
        send_updates(
            obj,
            key,
            upd,
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

    value_expl = getattr(value, META_OBJECT_PROPERTY, None)
    if value_expl is not None:
        if (key, expl) not in value_expl.parents:
            value_expl.parents.append((key, expl))

    return value


@dataclass
class MetaData:
    obj: Any
    initialised: bool = False
    old_post_init: Optional[Callable] = None
    old_setattr: Optional[Callable] = None
    views: set[str] = field(default_factory=set)
    parents: list[tuple[str, Self]] = field(default_factory=list)

    def get_path_list(self, base_path) -> dict[str, set[str]]:
        paths = defaultdict(set)

        for parent_name, parent_explainable in self.parents:
            if isinstance(parent_explainable.obj(), ExplainableDict):
                base_path = f"{parent_name}.{base_path}"
            else:
                base_path = f"data.{parent_name}.{base_path}"
            new_paths = parent_explainable.get_path_list(base_path=base_path)
            for key, value in new_paths.items():
                paths[key].update(value)
        
        if self.views:
            for view in self.views:
                paths[view].add(base_path)

        return paths


def send_updates(obj, key, update_data):
    expl = getattr(obj, META_OBJECT_PROPERTY)

    if isinstance(obj, (dict, ExplainableDict)):
        base_path = key
    else:
        base_path = f"data.{key}" if key is not None else "data"
    paths = expl.get_path_list(base_path)

    for view, path_set in paths.items():
        for path in list(path_set):
            data = update_data.copy()
            data["view_id"] = view
            data["path"] = path
            server.send_update("diff", data=data)


class ExplainableDict(UserDict):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__setattr__(META_OBJECT_PROPERTY, MetaData(initialised=True, obj=weakref.ref(self)))
        super().__init__(data)

    def __setitem__(self, key, value):
        value = _on_value_being_set(self, key, value, self.get(key, None))
        super().__setitem__(key, value)


class ExplainableList(UserList):
    def __init__(self, data: list[Any]) -> None:
        self_expl = MetaData(initialised=True, obj=weakref.ref(self))
        super().__setattr__(META_OBJECT_PROPERTY, self_expl)
        data = [
            _deep_make_observable(item)
            for item in data
        ]
        for idx,item in enumerate(data):
            expl = getattr(item, META_OBJECT_PROPERTY, None)
            if expl is None:
                continue
            if (idx, expl) not in expl.parents:
                expl.parents.append((idx, self_expl))
            
        # if not isinstance(data[0], str):
        #     breakpoint()
        super().__init__(data)

    def __setitem__(self, key, value):
        try:
            old_value = self[key]
        except IndexError:
            old_value = None

        value = _on_value_being_set(self, key, value, old_value)
        super().__setitem__(key, value)
    
    def append(self, value):
        upd = {
            "type": "listAppend",
            "value": serialize(value, path="diff"),
        }
        send_updates(
            self,
            key=None,
            update_data=upd,
        )
        # TODO: add parent to the value

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
            "type": "dataclass",
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
            "type": "list", 
            "struct_id": path,
            "data": [
                serialize(item, path=f"{path}.{idx}")
                for idx, item in enumerate(obj)
            ],
        }
    elif isinstance(obj, (dict, ExplainableDict)):
        return {
            "type": "dict",
            "struct_id": path,
            "keys": [
                serialize(key, path=f"{path}.keys.{idx}")
                for idx, key in enumerate(obj.keys())
            ],
            "values": [
                serialize(value, path=f"{path}.values.{idx}")
                for idx, value in enumerate(obj.values())
            ],
        }
    elif obj is None:
        return {
            "type": "string",
            "struct_id": path,
            "value": "None",
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


def _set_default_display_as(cls):
    if cls.__name__ in display.DISPLAY_REGISTRY:
        return
    
    display.display_as(widget.ListWidget([
        source.Reference(f"item.{field.name}")
        for field in dataclasses.fields(cls)
    ]))(cls)
        

def _deep_make_observable(obj: Any) -> None:
    if isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    
    if isinstance(obj, list):
        obj = ExplainableList(obj)
    elif isinstance(obj, dict):
        obj = ExplainableDict(obj)
    
    if not hasattr(obj, META_OBJECT_PROPERTY):
        super(type(obj), obj).__setattr__(META_OBJECT_PROPERTY, MetaData(initialised=True, obj=weakref.ref(obj)))

    if is_dataclass(obj):
        _set_default_display_as(type(obj))
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


def observe(view_id: str, obj: Any, widget: BaseWidget=None) -> None:    
    if not server_config.enabled:
        logger.debug()
        return obj
    
    if view_id in server.OBSERVED_OBJECTS:
        raise ValueError(f"Only one object per view is allowed")
        
    obj = _deep_make_observable(obj)
    expl = getattr(obj, META_OBJECT_PROPERTY)
    expl.views.add(view_id)

    init_data = {
        "view_id": view_id,
        "structure": serialize(obj, path=view_id),
        "widget": None if widget is None else dataclasses.asdict(widget),
    }

    server.OBSERVED_OBJECTS[view_id] = obj, widget

    server.send_update(
        "snapshot",
        data=init_data,
    )
    from .server import send_update
    send_update("__init__", {})
    expl.initialised = True

    return obj
