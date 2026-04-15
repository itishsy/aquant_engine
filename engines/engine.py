from abc import ABC, abstractmethod
from datetime import datetime
from typing import List


engines = {}


def job_engine(cls):
    cls_name = cls.__name__.lower()[0] + cls.__name__[1:]

    def register(clz):
        engines[cls_name] = clz
        return clz

    return register(cls)


class Searcher(ABC):
    cf = None

    def start(self):
        from components.candle_fetcher import CandleFetcher
        from models.choice import Choice

        searcher = self.__class__.__name__.lower()
        self.cf = CandleFetcher()
        Choice.delete().where(Choice.searcher == searcher).execute()
        chs = self.search()
        for cho in chs:
            cho.created = datetime.now()
            cho.searcher = searcher
            cho.save()
        print('[{0}] search {1} done!'.format(datetime.now(), searcher))

    @abstractmethod
    def search(self) -> List['Choice']:
        pass


class Watcher(ABC):
    cf = None

    def start(self):
        from components.candle_fetcher import CandleFetcher
        from components.notify import email, signal_notify
        from models.choice import Choice
        from models.signal import Signal

        self.cf = CandleFetcher()
        watcher = self.__class__.__name__.lower()
        choices = Choice.select().where(Choice.watcher == watcher)
        count = 0
        sis = []
        for cho in choices:
            try:
                count = count + 1
                sig = self.watch(cho.code)
                if sig and not Signal.select().where((Signal.dt == sig.dt)
                                                     & (Signal.freq == sig.freq)
                                                     & (Signal.code == cho.code)).exists():
                    sig.code = cho.code
                    sig.name = cho.name
                    sig.strategy = '{}-{}'.format(cho.searcher, watcher)
                    sig.notify = 0
                    sig.created = datetime.now()
                    sis.append(sig)
            except Exception as e:
                print(e)
        if sis:
            if email(f'{watcher} signal', signal_notify(sis)):
                for si in sis:
                    si.notify = 1
                    si.save()
            else:
                for si in sis:
                    si.notify = 0
                    si.save()

    @abstractmethod
    def watch(self, choice: 'Choice') -> 'Signal':
        pass


class Fetcher(ABC):
    strategy = 'fetcher'

    def start(self):
        self.strategy = self.__class__.__name__.lower()
        self.fetch()

    @abstractmethod
    def fetch(self):
        pass


class Sender(ABC):
    strategy = 'sender'

    def start(self):
        self.strategy = self.__class__.__name__.lower()
        self.send()

    @abstractmethod
    def send(self):
        pass
