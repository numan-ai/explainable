import random
import time

import explainable


def draw(cm: explainable.ContextManager):
    var = cm.get("my_var", default=0)
    chart_data = cm.get("my_chart_data", default=[0])

    return explainable.Graph([
        explainable.PixelNode({
            "size": chart_data[-1],
            "color": "red",
        })
    ], edges=[])


explainable.init(draw)
explainable.add_context()

my_chart_data = [0]
my_var = 1

while True:
    my_chart_data.append(my_chart_data[-1] + random.randint(-10, 10))
    my_var += 1
    time.sleep(0.5)
