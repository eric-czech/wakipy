import sys
import traceback
from time import sleep
from lifxlan import BLUE, COLD_WHITE, CYAN, GOLD, GREEN, ORANGE, PINK, PURPLE, RED, WARM_WHITE, WHITE, YELLOW, LifxLAN
import logging

logger = logging.getLogger(__name__)

COLORS = [BLUE, PURPLE, RED, ORANGE, YELLOW, WARM_WHITE]
STOP = False


class Bulbs(object):

    def __init__(self, bulbs):
        self.bulbs = bulbs

    def set_prop(self, prop, *args):
        for b in self.bulbs:
            try:
                getattr(b, 'set_' + prop)(*args)
            except:
                logger.warning("Failure occurred for bulb %s (it will be ignored)", b.get_label())
                traceback.print_exc()


def run_lighting_sequence(bulbs):
    global STOP
    STOP = False

    # Brightness is uint16 and delay is ms
    delay, rapid = 10000, False

    bulbs.set_prop('brightness', 0, 0, True)
    bulbs.set_prop('color', BLUE, 0, True)
    bulbs.set_prop('power', 'on')

    ct = 0

    # Sequence runs over 12 minutes (24 iterations @ 30 seconds per)
    max_ct = 24
    while ct <= max_ct and not STOP:
        ct += 1
        brightness = min(int(65535 * (.66 * ct / max_ct)), 65535)
        idx = min(ct // 4, len(COLORS)-1)
        color = COLORS[idx]
        logger.info("Setting brightness = %s, color = %s (%s)", brightness, color, idx)
        bulbs.set_prop('brightness', brightness, delay, rapid)
        bulbs.set_prop('color', color, delay, rapid)
        sleep(30)

    bulbs.set_prop('brightness', int(65535 * .75), delay, rapid)
    bulbs.set_prop('color', WARM_WHITE, delay, rapid)


def stop():
    global STOP
    STOP = True


def run():
    logger.info("Starting lighting sequence")
    lifx = LifxLAN(2)
    devices = lifx.get_lights()
    logger.info("Found %s devices", len(devices))
    if len(devices) == 0:
        logger.warning("No lights found; skipping sequence")
        return
    run_lighting_sequence(Bulbs(devices))
    logger.info("Lighting sequence complete")
