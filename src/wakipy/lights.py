import sys
from time import sleep
from lifxlan import BLUE, COLD_WHITE, CYAN, GOLD, GREEN, ORANGE, PINK, PURPLE, RED, WARM_WHITE, WHITE, YELLOW, LifxLAN
import logging

logger = logging.getLogger(__name__)

colors = [BLUE, COLD_WHITE, CYAN, GOLD, GREEN, ORANGE, PINK, PURPLE, RED, WARM_WHITE, WHITE, YELLOW]


stop = False


def run_lighting_sequence(bulbs):
    global stop
    stop = False
    bulb.set_brightness(0)
    bulb.set_color(RED)
    colors = [BLUE, PURPLE, RED, ORANGE, YELLOW]
    ct = 0
    # Sequence runs over 10 minutes (20 iterations @ 30 seconds per)
    while ct <= 20 and not stop:
        ct += 1
        brightness = min(int(65535 * (ct / 20.0)), 65535)
        color = colors[min(ct // 4, len(colors)-1)]
        for bulb in bulbs:
            # Brightness is uint16 and delay is ms
            bulb.set_brightness(brightness, 10000)
            bulb.set_color(color, 10000)
            sleep(30)


def stop():
    global stop
    stop = True


def run():
    logger.info("Starting lighting sequence")
    lifx = LifxLAN(2)
    devices = lifx.get_lights()
    logger.info("Found %s devices", len(devices))
    if len(devices) == 0:
        logger.warning("No lights found; skipping sequence")
        return
    run_lighting_sequence(devices)
    logger.info("Lighting sequence complete")
