from dataclasses import dataclass, fields
import json
import re
import time
from typing import Any, List, Literal, Optional, Protocol, \
        Tuple, Type, TypeVar, TypeAlias, TypedDict, \
        Union, overload, dataclass_transform

import win32api
import win32con
import win32gui


# Constants for simulating mouse clicks
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# Constants for simulating keyboard events
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

import time
import win32api
import win32con

def addField(cls):

    return cls

class HasPosition:
    __positionType: TypeAlias = Tuple[int, int] | Tuple[float, float]
    position: __positionType
    def __getitem__(self, name: Literal["position"]) -> __positionType:
        return self.position


class Event(Protocol):
    """
    position:
        int tuple is pixels,
        float tuple is screen/window ratio

    duration:   
        in millis
    """
    __typeType: TypeAlias = Literal["mouse", "keyboard", "sleep"]
    type: __typeType


class MouseEvent(Event):
    type = "mouse"
    button = ["left", "right", "middle"]
    action = [ "down", "up", "click", "move", "move_delta" ]
    x: int
    y: int
    duration: Optional[int]

class KeybaordEvent(Event):
    type = "keyboard"

class SleepEvent(Event):
    type = "sleep"
    duration: int = 1000

@overload
def createEvent(type: Literal["mouse"], *args) -> MouseEvent: ...
@overload
def createEvent(type: Literal["keyboard"]) -> KeybaordEvent: ...
@overload
def createEvent(type: Literal["sleep"]) -> SleepEvent: ...
def createEvent(type: Literal["mouse", "keyboard", "sleep"], *args) -> Any:
    if type == "mouse":
        return MouseEvent(*args)
    elif type == "keyboard":
        return KeybaordEvent(*args)
    elif type == "sleep":
        return SleepEvent(*args)
    
    raise ValueError("invalid type for create event")

def process_key(event: Event):
    duration = event['duration']
    vk_code = event['vk_code']
    key_down = event['key_down']
    if key_down:
        win32api.keybd_event(vk_code, 0, 0, 0)
    else:
        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    time.sleep(duration)

def process_mouse_down(event):
    button = event['button']
    x, y = event['position']
    win32api.SetCursorPos((x, y))
    if button == 'left':
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    elif button == 'right':
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
    elif button == 'middle':
        win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
    else:
        raise ValueError(f"Invalid mouse button: {button}")

def process_mouse_up(event):
    button = event['button']
    x, y = event['position']
    win32api.SetCursorPos((x, y))
    if button == 'left':
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    elif button == 'right':
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
    elif button == 'middle':    
        win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
    else:
        raise ValueError(f"Invalid mouse button: {button}")

def process_click(event: Event):
    duration = event['duration']
    button = event['button']
    x, y = event['position']
    win32api.SetCursorPos((x, y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(duration)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)

def process_input(input_file):
    events: List[Event] = []
    busy_until = dict()
    separator = re.compile(r"[,\W+]")


    click_duration = 10 # click duration (in millis) if unspecified
    
    with open(input_file, 'r') as f:
        for line in f:
            parts = separator.split(line.strip())
            event_type = parts[0]
            if "_click" in event_type:
                event_type = event_type.replace("_click", "")
            
            if event_type in [
                "down", "up", "click", "left", "right", "middle",
            ]:
                button = parts[1] if event_type in [
                    "click", "left", "right", "middle"
                ] else "left"
                
                timestamp = int(parts[2])
                if event_type in ["click", "right_click"]:
                    duration = int(parts[3])
                else:
                    duration = 0

                if busy_until[button] <= timestamp:
                    event = createEvent(
                        "mouse",button,event_type,duration
                    )
                    events.append(event)

                    if duration == 0:
                        busy_until[button] = timestamp + 1
                    else:
                        busy_until[button] = timestamp + duration

            elif event_type == "key":
                key = parts[1]
                timestamp = int(parts[2])
                event = {
                    "type": "keyboard",
                    "key": key,
                    "event_type": event_type
                }
                events.append(event)

    return events





def process_mouse(event: MouseEvent):
    pass

def process_keyboard(event: KeybaordEvent):
    pass

def process_events(events: List[Event]):
    for event in events:
        if isinstance(event, MouseEvent):
            process_mouse(event)
        elif isinstance(event, KeyboardEvent):
            process_keyboard(event)
        elif event.type == 'sleep':
            assert isinstance(event, MouseEvent)
            duration = event.duration
        
            time.sleep(duration)


def main():
    # Load the mouse and keyboard recording file in JSON format
    with open("mouse_and_keyboard_recording.json") as f:
        data = json.load(f)

    # Get the handle to the desktop window
    desktop_hwnd = win32gui.GetDesktopWindow()

    # Set the foreground window to the desktop
    win32gui.SetForegroundWindow(desktop_hwnd)

    # Simulate the mouse and keyboard inputs
    for event in data:
        if event["type"] == "mouse":
            x = event["x"]
            y = event["y"]
            button = event["button"]
            simulate_mouse_click(x, y, button)
        elif event["type"] == "keyboard":
            key = event["key"]
            is_keyup = event["is_keyup"]
            simulate_keyboard_input(key, is_keyup)
        
        # Wait for a short period of time to simulate real-time playback
        time.sleep(0.01)


if __name__ == "__main__":
    main()
