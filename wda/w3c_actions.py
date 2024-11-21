# coding: utf-8

from math import sqrt
from typing import Any, Dict, List, Optional, Union

class FingerMovement:
    """Represents a single finger movement action in W3C format.
    
    This class helps construct pointer movement actions with coordinates,
    origin element, and duration specifications.
    """

    def __init__(self):
        """Initialize a new finger movement with default type 'pointerMove'."""
        self.__data: Dict[str, Any] = {
            "type": "pointerMove"
        }
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the W3C action data representing this movement."""
        return self.__data
    
    def with_xy(self, x: Union[int, float], y: Union[int, float]) -> "FingerMovement":
        """Set the target coordinates for this movement.

        Args:
            - x (Union[int, float]): X-coordinate of the target position
            - y (Union[int, float]): Y-coordinate of the target position

        Returns:
            Self for method chaining
        """
        self.__data["x"] = x
        self.__data["y"] = y
        return self
    
    def with_origin(self, element_uid: Optional[str]=None) -> "FingerMovement":
        """Set the origin element for relative coordinates.

        Args:
            - element_uid (Optional[str]): The unique identifier of the origin element. If None, 
                                         coordinates are relative to viewport

        Returns:
            Self for method chaining
        """
        if element_uid is not None:
            self.__data["origin"] = element_uid
        return self
    
    def with_duration(self, second: Optional[float]=None) -> "FingerMovement":
        """Set the duration of this movement.

        Args:
            - second (Optional[float]): Duration in seconds. If None, movement is instantaneous

        Returns:
            Self for method chaining
        """
        if second is not None:
            self.__data["duration"] = second * 1000
        return self


class FingerAction:
    """Represents a sequence of finger actions including movements, taps, and pauses."""

    def __init__(self):
        """Initialize an empty sequence of finger actions."""
        self.__data: List[Dict[str, Any]] = []

    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get the W3C actions data representing this sequence."""
        return self.__data
    
    def move(self, movement: FingerMovement) -> "FingerAction":
        """Add a movement to the sequence.

        Args:
            - movement (FingerMovement): A FingerMovement instance describing the movement

        Returns:
            Self for method chaining
        """
        self.__data.append(movement.data)
        return self
    
    def down(self) -> "FingerAction":
        """Add a finger press action to the sequence.

        Returns:
            Self for method chaining
        """
        self.__data.append({"type": "pointerDown"})
        return self
    
    def up(self) -> "FingerAction":
        """Add a finger release action to the sequence.

        Returns:
            Self for method chaining
        """
        self.__data.append({"type": "pointerUp"})
        return self
    
    def pause(self, second: float=0.5) -> "FingerAction":
        """Add a pause to the sequence.

        Use with caution, this might create unexpected effect when followed by a `move` action.

        For example, the duration of the pause won't actually make the pointer pause;
        instead, it'll apply to the move function.
        
        See [github issue](https://github.com/appium/WebDriverAgent/issues/936) for more information.

        In order to perform a move-down-pause-move sequence, a possible workaround might be:
        `move(fm_start).down().pause(t).move(fm_start).move(fm_end)`

        Args:
            - second (float): Duration to pause in seconds, defaults to 0.5

        Returns:
            Self for method chaining
        """
        if second < 0:
            second = 0.5
        self.__data.append({"type": "pause", "duration": second * 1000})
        return self


class W3CActions:
    """Main class for constructing W3C WebDriver actions sequences.
    
    This class supports both keyboard input and touch actions, with helper methods
    for common touch gestures like tap, press, and swipe.
    """

    def __init__(self):
        """Initialize an empty W3C actions sequence."""
        self.__data: List[Dict[str, Any]] = []
    
    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get the complete W3C actions sequence data."""
        return self.__data

    def send_keys(self, text: str) -> "W3CActions":
        """Add keyboard input actions to the sequence.

        Args:
            - text (str): The text to type

        Returns:
            Self for method chaining
        """
        keyboard: Dict[str, Any] = {
            "type": "key",
            "id": f"keyboard{len(self.__data)}",
            "actions": [
                (a for a in [
                    {"type": "keyDown", "value": v},
                    {"type": "keyUp", "value": v}
                ]) for v in text
            ]
        }
        self.__data.append(keyboard)
        return self
    
    def inject_touch_actions(self, *actions: FingerAction) -> "W3CActions":
        """Add touch action sequences to the W3C actions.

        Args:
            - actions (FingerAction): One or more FingerAction instances

        Returns:
            Self for method chaining
        """
        for action in actions:
            pointer: Dict[str, Any] = {
                "type": "pointer",
                "id": f"finger{len(self.__data)}",
                "parameters": {
                    "pointerType": "touch"
                },
                "actions": action.data
            }
            self.__data.append(pointer)
        return self
    
    def tap(self, x: Union[int, float], y: Union[int, float], element_uid: Optional[str]=None, second: float=0.1) -> "W3CActions":
        """Add a tap gesture at the specified coordinates.

        Args:
            - x (Union[int, float]): X-coordinate to tap
            - y (Union[int, float]): Y-coordinate to tap
            - element_uid (Optional[str]): Optional element to use as coordinate origin
            - second (float): Duration of the tap in seconds

        Returns:
            Self for method chaining
        """
        movement = FingerMovement().with_xy(x, y).with_origin(element_uid)
        action = FingerAction().move(movement).down().pause(second).up()
        self.inject_touch_actions(action)
        return self
    
    def press(self, x: Union[int, float], y: Union[int, float],
              element_uid: Optional[str]=None, second: float=2.0) -> "W3CActions":
        """Add a long press gesture at the specified coordinates.

        Args:
            - x (Union[int, float]): X-coordinate to press
            - y (Union[int, float]): Y-coordinate to press
            - element_uid (Optional[str]): Optional element to use as coordinate origin
            - second (float): Duration of the press in seconds

        Returns:
            Self for method chaining
        """
        movement = FingerMovement().with_xy(x, y).with_origin(element_uid)
        action = FingerAction().move(movement).down().pause(second).up()
        self.inject_touch_actions(action)
        return self
    
    def swipe(self, from_x: Union[int, float], from_y: Union[int, float],
              to_x: Union[int, float], to_y: Union[int, float], element_uid: Optional[str]=None,
              press_seconds: float=0.25, swipe_seconds: Optional[float]=None, hold_seconds: float=0.25) -> "W3CActions":
        """Add a swipe gesture from one point to another.

        Args:
            - from_x (Union[int, float]): Starting X-coordinate
            - from_y (Union[int, float]): Starting Y-coordinate
            - to_x (Union[int, float]): Ending X-coordinate
            - to_y (Union[int, float]): Ending Y-coordinate
            - element_uid (Optional[str]): Optional element to use as coordinate origin
            - press_seconds (float): Duration to hold before starting the swipe
            - swipe_seconds (Optional[float]): Duration of the swipe movement (None for instant)
            - hold_seconds (float): Duration to hold after completing the swipe

        Returns:
            Self for method chaining
        """
        movement_from = FingerMovement().with_xy(from_x, from_y).with_origin(element_uid)
        movement_to = FingerMovement().with_xy(to_x, to_y).with_origin(element_uid).with_duration(swipe_seconds)
        action = FingerAction().move(movement_from).down().pause(press_seconds).move(movement_from).move(movement_to).pause(hold_seconds).up()
        self.inject_touch_actions(action)
        return self
    

class TouchMovement:
    """Represents a touch movement action in WebDriver format.
    
    This class helps construct touch movement actions with coordinates
    and origin element specifications.
    """

    def __init__(self):
        """Initialize a new touch movement with default action 'moveTo'."""
        self.__data: Dict[str, Any] = {
            "action": "moveTo",
            "options": dict()
        }
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the WebDriver action data representing this movement."""
        return self.__data
    
    def with_xy(self, x: Union[int, float], y: Union[int, float]) -> "TouchMovement":
        """Set the target coordinates for this movement.

        Args:
            - x (Union[int, float]): X-coordinate of the target position
            - y (Union[int, float]): Y-coordinate of the target position

        Returns:
            Self for method chaining
        """
        self.__data["options"]["x"] = x
        self.__data["options"]["y"] = y
        return self
    
    def with_origin(self, element_uid: Optional[str]=None) -> "TouchMovement":
        """Set the origin element for relative coordinates.

        Args:
            - element_uid (Optional[str]): The unique identifier of the origin element. If None,
                                         coordinates are relative to viewport

        Returns:
            Self for method chaining
        """
        if element_uid is not None:
            self.__data["options"]["element"] = element_uid
        return self


class TouchPress:
    """Represents a touch press action in WebDriver format.
    
    This class helps construct touch press actions with coordinates,
    origin element, and pressure specifications.
    """

    def __init__(self):
        """Initialize a new touch press with default action 'press'."""
        self.__data: Dict[str, Any] = {
            "action": "press",
            "options": dict()
        }
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the WebDriver action data representing this press."""
        return self.__data
    
    def with_xy(self, x: Union[int, float], y: Union[int, float]) -> "TouchPress":
        """Set the target coordinates for this press.

        Args:
            - x (Union[int, float]): X-coordinate of the press position
            - y (Union[int, float]): Y-coordinate of the press position

        Returns:
            Self for method chaining
        """
        self.__data["options"]["x"] = x
        self.__data["options"]["y"] = y
        return self
    
    def with_origin(self, element_uid: Optional[str]=None) -> "TouchPress":
        """Set the origin element for relative coordinates.

        Args:
            - element_uid (Optional[str]): The unique identifier of the origin element. If None,
                                         coordinates are relative to viewport

        Returns:
            Self for method chaining
        """
        if element_uid is not None:
            self.__data["options"]["element"] = element_uid
        return self

    def with_pressure(self, pressure: float) -> "TouchPress":
        """Set the pressure level for this press.

        Args:
            - pressure (float): The pressure level of the press, typically between 0.0 and 1.0

        Returns:
            Self for method chaining
        """
        self.__data["options"]["pressure"] = pressure
        return self


class TouchLongPress:
    """Represents a touch long press action in WebDriver format.
    
    This class helps construct touch long press actions with coordinates
    and origin element specifications.
    """

    def __init__(self):
        """Initialize a new touch long press with default action 'longPress'."""
        self.__data: Dict[str, Any] = {
            "action": "longPress",
            "options": dict()
        }
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the WebDriver action data representing this long press."""
        return self.__data
    
    def with_xy(self, x: Union[int, float], y: Union[int, float]) -> "TouchLongPress":
        """Set the target coordinates for this long press.

        Args:
            - x (Union[int, float]): X-coordinate of the long press position
            - y (Union[int, float]): Y-coordinate of the long press position

        Returns:
            Self for method chaining
        """
        self.__data["options"]["x"] = x
        self.__data["options"]["y"] = y
        return self
    
    def with_origin(self, element_uid: Optional[str]=None) -> "TouchLongPress":
        """Set the origin element for relative coordinates.

        Args:
            - element_uid (Optional[str]): The unique identifier of the origin element. If None,
                                         coordinates are relative to viewport

        Returns:
            Self for method chaining
        """
        if element_uid is not None:
            self.__data["options"]["element"] = element_uid
        return self


class TouchTap:
    """Represents a touch tap action in WebDriver format.
    
    This class helps construct touch tap actions with coordinates,
    origin element, and tap count specifications.
    """

    def __init__(self):
        """Initialize a new touch tap with default action 'tap'."""
        self.__data: Dict[str, Any] = {
            "action": "tap",
            "options": dict()
        }
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the WebDriver action data representing this tap."""
        return self.__data
    
    def with_xy(self, x: Union[int, float], y: Union[int, float]) -> "TouchTap":
        """Set the target coordinates for this tap.

        Args:
            - x (Union[int, float]): X-coordinate of the tap position
            - y (Union[int, float]): Y-coordinate of the tap position

        Returns:
            Self for method chaining
        """
        self.__data["options"]["x"] = x
        self.__data["options"]["y"] = y
        return self
    
    def with_origin(self, element_uid: Optional[str]=None) -> "TouchTap":
        """Set the origin element for relative coordinates.

        Args:
            - element_uid (Optional[str]): The unique identifier of the origin element. If None,
                                         coordinates are relative to viewport

        Returns:
            Self for method chaining
        """
        if element_uid is not None:
            self.__data["options"]["element"] = element_uid
        return self
    
    def with_count(self, count: int) -> "TouchTap":
        """Set the number of taps to perform.

        Args:
            - count (int): Number of times to perform the tap

        Returns:
            Self for method chaining
        """
        self.__data["options"]["count"] = count
        return self


class TouchActions:
    """Main class for constructing WebDriver touch actions sequences.
    
    This class supports various touch actions including movement, press,
    long press, tap, pause, release, and cancel operations.

    Removed after wda v7.0.0, use `W3CActions` instead.
    """

    def __init__(self):
        """Initialize an empty touch actions sequence."""
        self.__data: List[Dict[str, Any]] = []
    
    @property
    def data(self) -> List[Dict[str, Any]]:
        """Get the complete WebDriver touch actions sequence data."""
        return self.__data
    
    def move(self, movement: TouchMovement) -> "TouchActions":
        """Add a movement action to the sequence.

        Args:
            - movement (TouchMovement): A TouchMovement instance describing the movement

        Returns:
            Self for method chaining
        """
        self.__data.append(movement.data)
        return self
    
    def press(self, press: TouchPress) -> "TouchActions":
        """Add a press action to the sequence.

        Args:
            - press (TouchPress): A TouchPress instance describing the press

        Returns:
            Self for method chaining
        """
        self.__data.append(press.data)
        return self
    
    def long_press(self, long_press: TouchLongPress) -> "TouchActions":
        """Add a long press action to the sequence.

        Args:
            - long_press (TouchLongPress): A TouchLongPress instance describing the long press

        Returns:
            Self for method chaining
        """
        self.__data.append(long_press.data)
        return self

    def tap(self, tap: TouchTap) -> "TouchActions":
        """Add a tap action to the sequence.

        Args:
            - tap (TouchTap): A TouchTap instance describing the tap

        Returns:
            Self for method chaining
        """
        self.__data.append(tap.data)
        return self
    
    def pause(self, second: float=0.5) -> "TouchActions":
        """Add a pause to the sequence.

        Args:
            - second (float): Duration to pause in seconds, defaults to 0.5. If negative,
                            defaults to 0.5

        Returns:
            Self for method chaining
        """
        if second < 0:
            second = 0.5
        self.__data.append({
            "action": "wait",
            "options": {
                "ms": second * 1000
            }
        })
        return self
    
    def up(self) -> "TouchActions":
        """Add a touch release action to the sequence.

        Returns:
            Self for method chaining
        """
        self.__data.append({"action": "release"})
        return self
    
    def cancel(self) -> "TouchActions":
        """Add a cancel action to the sequence.

        Returns:
            Self for method chaining
        """
        self.__data.append({"action": "cancel"})
        return self
    
    def swipe(self, from_x: Union[int, float], from_y: Union[int, float],
              to_x: Union[int, float], to_y: Union[int, float], element_uid: Optional[str]=None,
              press_seconds: float=0.25, swipe_seconds: Optional[float]=None,
              delta: float=10, hold_seconds: float=0.25, up: bool=True) -> "TouchActions":
        """Add a swipe gesture from one point to another.

        Args:
            - from_x (Union[int, float]): Starting X-coordinate
            - from_y (Union[int, float]): Starting Y-coordinate
            - to_x (Union[int, float]): Ending X-coordinate
            - to_y (Union[int, float]): Ending Y-coordinate
            - element_uid (Optional[str]): Optional element to use as coordinate origin
            - press_seconds (float): Duration to hold before starting the swipe
            - swipe_seconds (Optional[float]): Duration of the swipe movement (None for instant)
            - delta (float): The movement is broken down to small steps,
                             this delta describes the delta of each step
            - hold_seconds (float): Duration to hold after completing the swipe
            - up (bool): Whether to lift up after swiping, default to true

        Returns:
            Self for method chaining
        """
        if swipe_seconds is None:
            self.press(TouchPress().with_xy(from_x, from_y).with_origin(element_uid)).pause(press_seconds)
            self.move(TouchMovement().with_xy(to_x, to_y).with_origin(element_uid)).pause(hold_seconds)
            if up:
                self.up()
        else:
            distance = sqrt(pow(to_y - from_y, 2) + pow(to_x - from_x, 2))
            steps = int(distance / delta)

            dx = float(to_x - from_x) / steps
            dy = float(to_y - from_y) / steps
            interval = float(swipe_seconds) / steps
            
            self.press(TouchPress().with_xy(from_x, from_y).with_origin(element_uid)).pause(press_seconds)
            for i in range(1, steps + 1):
                self.move(TouchMovement().with_xy(from_x + i * dx, from_y + i * dy).with_origin(element_uid)).pause(interval)
            self.move(TouchMovement().with_xy(from_x + steps * dx, from_y + steps * dy).with_origin(element_uid)).pause(hold_seconds)
            if up:
                self.up()
        return self
