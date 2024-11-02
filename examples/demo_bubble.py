import time
import random

import explainable
from explainable import widget, source

explainable.init()

test_list = [random.randint(0, 100) for _ in range(30)]

print("The original list is : " + str(test_list))

test_list = explainable.observe("view1", test_list, widget=widget.ListWidget(
  source=source.Reference("item"),
  item_widget=widget.TileWidget(
    height=source.Reference("item"),
    width=source.Number(6),
  ),
))

def bubble_sort(elements):
  for n in range(len(elements) - 1, 0, -1):
    swapped = False
    for i in range(n):
      if elements[i] > elements[i + 1]:
        swapped = True
        time.sleep(0.5)
        elements[i], elements[i + 1] = elements[i + 1], elements[i]
    if not swapped:
      return


bubble_sort(test_list)

print("The sorted list is : " + str(test_list))
