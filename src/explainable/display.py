from explainable.base_entities import BaseWidget


DISPLAY_REGISTRY: dict[str, BaseWidget] = {}


def display_as(widget: BaseWidget):
    def decorator(cls):
        DISPLAY_REGISTRY[cls.__name__] = widget

        return cls
    
    return decorator
