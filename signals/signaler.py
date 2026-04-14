from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from models.signal import Signal
from models.symbol import Symbol
from common.utils import *
import candles.finance as fet
from candles.candle import Candle
from typing import List
from candles.storage import dba, find_candles

import traceback
import time

category = {}


def signaler(cls):
    cls_name = cls.__name__

    def register(clz):
        category[cls_name] = clz

    return register(cls)


class Signaler(ABC):
    category = 'signaler'

    def start(self):
        self.category = self.__class__.__name__.lower()

        symbols = Symbol.select()
        for sym in symbols:
            try:
                candles = find_candles(sym.code)
                sis = self.search(candles)
                print('search single code=', sym.code, 'result:',len(sis))
                if len(sis) > 0:
                    for si in sis:
                        si = self.analyze(si)
                        si.save()
            except Exception as e:
                print(e)

    @abstractmethod
    def search(self, candles: List[Candle]) -> List[Signal]:
        pass

    @abstractmethod
    def analyze(self, sig: Signal) -> Signal:
        pass

