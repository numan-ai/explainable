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
