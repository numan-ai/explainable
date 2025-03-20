# Explainable

[![PyPI version](https://img.shields.io/pypi/v/explainable.svg)](https://pypi.org/project/explainable/)

Explainable is a project for real time visualisation of complex data structures with minimal effort.  
This project was created by [Numan Team](https://numan.ai/).  
Visualisation runs on our [website](https://explainable.numan.ai/), so you only need install the library and initialise it in your code.

![plot](./demo.png)

## Installation

```sh
pip install -U explainable
```

## Usage

1. Install using `pip`
2. Import the library in your code
3. Write a drawing function that returns a `Graph` object
3. Add `explainable.init(<draw_func>)` in your code to start the server
4. Add context using `explainable.add_context()` in your code
5. Go to https://explainable.numan.ai/

```python
import time

import explainable


def draw(cm: explainable.ContextManager):
    ctx = cm.get("my_var", default=0)

    return explainable.Graph([
        explainable.TextNode(f"My var: {ctx}"),
    ], edges=[])


explainable.init(draw)
explainable.add_context()

my_var = 1

while True:
    my_var += 1
    time.sleep(0.5)
```

![plot](./demo2.png)

## Requirements

Python 3.7 or higher.
