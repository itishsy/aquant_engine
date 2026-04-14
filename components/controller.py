from datetime import datetime
from models.component import Component
from models.symbol import Symbol
import candles.finance as fet
from engines import *


def start_component(name, act):
    print('============', name, act)
    comp = Component.get(Component.name == name)
    comp.status = Component.Status.RUNNING
    comp.run_start = datetime.now()
    comp.save()
    if name == 'fetcher':
        if act == 'candle':
            pass
            # fet.fetch_all()
        elif act == 'symbol':
            Symbol().fetch()
    elif name == 'engine':
        if act == 'init':
            init_engine()
        else:
            for eng_name in engine.strategy:
                start_component(eng_name, act)
    else:
        eng = engine.strategy[name]()
        eng.strategy = name
        if act == 'search' or act == 'all':
            print('engine', name, 'action: search, start...')
            eng.do_search()
            print('engine', name, 'action: search, done!')
        if act == 'watch' or act == 'all':
            print('engine', name, 'action: watch, start...')
            eng.start_watch()
            print('engine', name, 'action: watch, done!')
    comp.status = Component.Status.READY
    comp.run_end = datetime.now()
    comp.save()


def init_engine():
    init_time = datetime(datetime.now().year, 1, 1)
    default_components = ['engine', 'fetcher']
    for comp in default_components:
        if not Component.select().where(Component.name == comp).exists():
            Component.create(name=comp, clock_time=datetime.now(), run_start=init_time, run_end=init_time, status=Component.Status.READY)
        else:
            Component.update(clock_time=datetime.now(), status=Component.Status.READY).where(Component.name == comp).execute()
    Component.delete().where(~(Component.name << default_components)).execute()
    for name in engine.strategy:
        Component.create(name=name.lower()[0] + name[1:], clock_time=datetime.now(), run_start=init_time,
                         run_end=init_time, status=Component.Status.READY)


if __name__ == '__main__':
    init_engine()
