import argparse
import signal
import sys
import time
from datetime import datetime, timedelta

from engines import *


RUNNING = True


def _handle_signal(signum, frame):
    global RUNNING
    RUNNING = False
    print("[{}] received signal {}, exiting...".format(datetime.now(), signum))


def run_fupan():
    print("[{}] fupan start...".format(datetime.now()))
    engine.engines["fupan"]().start()
    print("[{}] fupan end".format(datetime.now()))


def next_run_time(run_at):
    now = datetime.now()
    target = now.replace(hour=run_at.hour, minute=run_at.minute, second=0, microsecond=0)
    if now >= target:
        target = target + timedelta(days=1)
    return target


def wait_until(target):
    while RUNNING:
        remaining = (target - datetime.now()).total_seconds()
        if remaining <= 0:
            return True
        sleep_seconds = min(remaining, 60)
        time.sleep(sleep_seconds)
    return False


def parse_args():
    parser = argparse.ArgumentParser(description="Run fupan every day at the configured time.")
    parser.add_argument("--time", default="18:00", help="Daily run time in HH:MM format. Default: 18:00")
    parser.add_argument("--once", action="store_true", help="Run immediately once and exit.")
    return parser.parse_args()


def parse_run_at(value):
    try:
        return datetime.strptime(value, "%H:%M")
    except ValueError as ex:
        raise SystemExit("invalid --time value '{}', expected HH:MM".format(value)) from ex


def main():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    args = parse_args()
    run_at = parse_run_at(args.time)

    if args.once:
        run_fupan()
        return

    print("[{}] scheduler started, next run time is {} every day".format(
        datetime.now(),
        run_at.strftime("%H:%M"),
    ))
    while RUNNING:
        target = next_run_time(run_at)
        print("[{}] waiting for next run at {}".format(
            datetime.now(),
            target.strftime("%Y-%m-%d %H:%M:%S"),
        ))
        if not wait_until(target):
            break
        if RUNNING:
            run_fupan()


if __name__ == "__main__":
    main()
