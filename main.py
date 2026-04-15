from datetime import datetime
from engines import *
from models.engine import Engine
import logging
import time
import threading
import os

logging.basicConfig(format='%(asctime)s %(message)s', filename='aquant.log')
logging.getLogger().setLevel(logging.INFO)


class EngineJob(threading.Thread):
    def run(self):
        while True:
            now = datetime.now()
            n_val = now.hour * 100 + now.minute
            ens = Engine.select().where(Engine.status >= 0).order_by(Engine.run_order)
            for eng in ens:
                print("[{}] start engine {}".format(datetime.now(), eng.name))
                if eng.job_from < n_val < eng.job_to or eng.status == 0:
                    if eng.status != 0:
                        if eng.job_times == 1 and eng.run_end > datetime.strptime(
                                datetime.now().strftime("%Y-%m-%d 00:00:01"),
                                "%Y-%m-%d %H:%M:%S"):
                            continue
                        if eng.job_times == 5 and now.weekday() != 5 and eng.run_end > datetime.strptime(
                                datetime.now().strftime("%Y-%m-%d 00:00:01"),
                                "%Y-%m-%d %H:%M:%S"):
                            continue
                    try:
                        eng.status = 1
                        eng.run_start = datetime.now()
                        eng.comment = None
                        eng.save()
                        if engine.engines.get(eng.method) is None:
                            eval(eng.name + '.' + eng.method + '()')
                        else:
                            engine.engines[eng.method]().start()
                        eng.run_end = datetime.now()
                    except Exception as e:
                        print(e)
                        error_message = ''
                        if e.args:  # 检查是否有消息
                            error_message = e.args[0]
                            print(f"错误消息: {error_message}")
                        eng.comment = f'err：{error_message}'
                    finally:
                        eng.status = 2
                        eng.save()
            time.sleep(60 * 10)


if __name__ == '__main__':
    et = EngineJob()
    et.start()


