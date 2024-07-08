# Explainable

[![PyPI version](https://img.shields.io/pypi/v/explainable.svg)](https://pypi.org/project/explainable/)

Explainable is a project for visualising complex data structures in real time with minimal effort.
This project was created by [Numan Team](https://numan.ai/).

## Installation

```sh
pip install -U explainable
```

## Usage

```python
import time

import explainable

# start the server
explainable.init()

# create your data
lst = [0, 1, 2]

# start observing
lst = explainable.observe("view1", lst)

# chagne your data
while True:
  lst[0] += 1
  lst[1] -= 1

  time.sleep(1)
```

Currently supported data structures:
- dataclass
- list
- dict

## Requirements

Python 3.7 or higher.
