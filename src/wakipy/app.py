# rsync -Pr /Users/eczech/repos/misc/wakipy/* pi@rb1:/home/pi/repos/wakipy/
from flask import Flask
from flask import request
from flask import jsonify
import argparse
import traceback
import lights
import schedule
import threading
import time
import os.path as osp
import music
import logging
import config

logging.basicConfig(level='INFO', format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
app = Flask(__name__)


def start_scheduler(interval=10):
    cancel = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cancel.is_set():
                schedule.run_pending()
                time.sleep(interval)

    thread = ScheduleThread()
    thread.daemon = True
    thread.start()
    return cancel


def run_threaded(fn):
    thread = threading.Thread(target=fn)
    thread.daemon = True
    thread.start()


def run_alarm_music():
    run_threaded(_run_alarm_music)


def _run_alarm_music():
    logger.info("Running alarm music")
    try:
        music.play_all()
        pass
    except:
        traceback.print_exc()
    finally:
        return schedule.CancelJob


def run_alarm_lights():
    run_threaded(_run_alarm_lights)


def _run_alarm_lights():
    logger.info("Running alarm lights")
    try:
        lights.run()
    except:
        traceback.print_exc()
    finally:
        return schedule.CancelJob


@app.route("/get_songs")
def get_songs():
    return jsonify([s['title'] + ' | ' + s['id'] for s in music.get_manifest().values()])


@app.route("/set_top_song")
def set_top_song():
    id = request.args.get('id').strip()
    music.prioritize(id)
    return u"Moved it to the top! \U0001F970"


@app.route("/add_song")
def add_song():
    id = request.args.get('id').strip()
    video = music.download(id)
    return video['title']


@app.route("/rename_song")
def rename_song():
    id = request.args.get('id').strip()
    name = request.args.get('name').strip()
    music.rename(id, name)
    return 'Added song: "{}"'.format(name)


@app.route("/log_jobs")
def log_jobs():
    logging.info("Currently scheduled jobs (%s):", len(schedule.jobs))
    for job in schedule.jobs:
        logging.info("\t%s", job)
    return "Job logging complete"


@app.route("/show_alarm")
def show_alarm():
    alarm_time = 'Not Set'
    for job in schedule.jobs:
        if job.job_func.__name__ == 'run_alarm_music':
            alarm_time = job.next_run
    logging.info("Found alarm with time '%s'", alarm_time)
    return str(alarm_time)


@app.route("/set_alarm")
def set_alarm():
    """ Time must have format like 2019-11-07T16:01:11-0500 (day is ignored) """
    # Make sure to remove any existing alarms first
    disable_alarm()

    # Parse out time component from argument
    date = request.args.get('time')
    # Convert 2019-11-07T16:01:11-0500 -> 16:01:11
    time = str(date.split('T')[1].split('-')[0])
    # Convert 16:01:11 -> 16:01:00
    time = ':'.join(time.split(':')[:2]) + ':00'
    logger.info("Setting alarm for time '%s'", time)

    # Schedule the alarm components
    schedule.every(1).day.at(time).do(run_alarm_music).tag('alarm')
    schedule.every(1).day.at(time).do(run_alarm_lights).tag('alarm')
    return u'Alarm set for time {} \U0001F634 -- sleep well my goob!'.format(time)


@app.route("/trigger_alarm")
def trigger_alarm():
    run_alarm_music()
    run_alarm_lights()
    return u'Alarm triggered'


@app.route("/stop_alarm")
def stop_alarm():
    music.stop()
    lights.stop()
    return u'Alarm stopped'


@app.route("/disable_alarm")
def disable_alarm():
    logger.info("Disabling current alarms")
    schedule.clear('alarm')
    return u'\U0001F97A Alarm schedule canceled'


def run(args):
    logger.info("Launching alarm server")
    config.set_from_args(args)
    # No sync needed yet
    # schedule.every(30).seconds.do(run_threaded, music.sync).tag('sync')
    start_scheduler()
    app.run(host='0.0.0.0', debug=args.debug)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("-e", "--data-dir")
    args = parser.parse_args()
    run(args)
