from SimConnect import *
import logging
from SimConnect.Enum import *
from time import sleep

from vkb.devices import find_all_vkb
from vkb import led

ext = find_all_vkb()[0]

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)
LOGGER.info("START")

sm = SimConnect()
aq = AircraftRequests(sm)
ae = AircraftEvents(sm)

FSM_LED_BASE = 18

APPR_LED = FSM_LED_BASE + 3
ALT_LED = FSM_LED_BASE + 4

ALT_MODE = 50
APPR_MODE = 51
GEAR_MODE = 52

SEM_LED_BASE = 10
GEAR_LED_BASE = SEM_LED_BASE + 5

# { led: simvar }
ledmap = {
    FSM_LED_BASE + 0:  aq.find('AUTOPILOT_HEADING_LOCK'),
    FSM_LED_BASE + 2:  aq.find('AUTOPILOT_NAV1_LOCK'),
    FSM_LED_BASE + 7:  aq.find('AUTOPILOT_FLIGHT_LEVEL_CHANGE'),
    FSM_LED_BASE + 8:  aq.find('AUTOPILOT_MASTER'),
    FSM_LED_BASE + 9:  aq.find('AUTOPILOT_FLIGHT_DIRECTOR_ACTIVE'),
    FSM_LED_BASE + 10: aq.find('AUTOPILOT_YAW_DAMPER'),
    FSM_LED_BASE + 11: aq.find('AUTOPILOT_VERTICAL_HOLD'),

    # altitude
    ALT_MODE: [
        aq.find('AUTOPILOT_ALTITUDE_ARM'),
        aq.find('AUTOPILOT_ALTITUDE_LOCK')],

    # approach
    APPR_MODE: [
        aq.find('AUTOPILOT_APPROACH_ARM'),
        aq.find('AUTOPILOT_APPROACH_ACTIVE'),
        aq.find('AUTOPILOT_APPROACH_CAPTURED'),
        aq.find('AUTOPILOT_GLIDESLOPE_ARM'),
        aq.find('AUTOPILOT_GLIDESLOPE_ACTIVE')],

    GEAR_LED_BASE + 0: aq.find('GEAR_LEFT_POSITION'),
    GEAR_LED_BASE + 1: aq.find('GEAR_CENTER_POSITION'),
    GEAR_LED_BASE + 2: aq.find('GEAR_RIGHT_POSITION')
}

previous_state = {}

while not sm.quit:
    current_state = {}
    led_config = []

    for k, v in ledmap.items():
        if type(v) == list:
            current_state[k] = [w.get() for w in v]
        else:
            current_state[k] = v.get()

    for k, v in current_state.items():
        if v != previous_state.get(k):
            previous_state[k] = v

            if k == ALT_MODE:
                if v[1] == 1.0: # altitude lock
                    led_config.append(led.LEDConfig(ALT_LED, led.ColorMode.COLOR1, led.LEDMode.CONSTANT, '#fff', '#fff'))
                elif v[0] == 1.0: # altitude arm
                    led_config.append(led.LEDConfig(ALT_LED, led.ColorMode.COLOR1_p_2, led.LEDMode.CONSTANT, '#444', '#fff'))
                else:
                    led_config.append(led.LEDConfig(ALT_LED, led.ColorMode.COLOR1, led.LEDMode.OFF, '#fff', '#fff'))

            elif k == APPR_MODE:
                if v[4] == 1.0: # glideslope active
                    led_config.append(led.LEDConfig(APPR_LED, led.ColorMode.COLOR1, led.LEDMode.CONSTANT, '#fff', '#fff'))
                elif v[2] == 1.0 and v[3] == 1.0: # approach captured, glideslope arm
                    led_config.append(led.LEDConfig(APPR_LED, led.ColorMode.COLOR1, led.LEDMode.SLOW_BLINK, '#fff', '#fff'))
                elif v[1] == 1.0: # approach active
                    led_config.append(led.LEDConfig(APPR_LED, led.ColorMode.COLOR1_p_2, led.LEDMode.CONSTANT, '#444', '#fff'))
                elif v[0] == 1.0: # approach arm
                    led_config.append(led.LEDConfig(APPR_LED, led.ColorMode.COLOR1_p_2, led.LEDMode.SLOW_BLINK, '#444', '#fff'))
                else:
                    led_config.append(led.LEDConfig(APPR_LED, led.ColorMode.COLOR1, led.LEDMode.OFF, '#fff', '#fff'))

            elif k >= GEAR_LED_BASE and k <= GEAR_LED_BASE + 2:
                if v == 0.0: # gear is up
                    led_config.append(led.LEDConfig(k, led.ColorMode.COLOR2, led.LEDMode.CONSTANT, '#fff', '#fff'))
                elif v == 1.0: # gear is down
                    led_config.append(led.LEDConfig(k, led.ColorMode.COLOR1, led.LEDMode.CONSTANT, '#fff', '#fff'))
                else: # gear in transit
                    led_config.append(led.LEDConfig(k, led.ColorMode.COLOR1_p_2, led.LEDMode.SLOW_BLINK, '#444', '#fff'))

            else:
                # generic flag, 1.0 = BRIGHT GREEN LED, 0.0 = dim green led
                if v == 1.0:
                    led_config.append(led.LEDConfig(k, led.ColorMode.COLOR1, led.LEDMode.CONSTANT, '#fff', '#fff'))
                elif v == 0.0:
                    led_config.append(led.LEDConfig(k, led.ColorMode.COLOR1, led.LEDMode.OFF, '#fff', '#fff'))

    if led_config:
        ext.update_leds(led_config)

    sleep(0.2)
