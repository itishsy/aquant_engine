from engines import *
from datetime import datetime
from models.symbol import Symbol
from models.engine import Engine
import sys

"""
ToDesk:
设备代码:780 106 551
临时密码:Huangsh1
"""


def test_engine(eng_name):
    # eng.strategy = eng_name
    print("[{}] {} start...".format(datetime.now(), eng_name))
    engine.engines[eng_name]().start()
    print("[{}] {} end".format(datetime.now(), eng_name))


engine_name = "fupan"
test_engine(engine_name)
