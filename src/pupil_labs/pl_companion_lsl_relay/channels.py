from typing import Any, Callable, Dict, List

import pylsl
from typing_extensions import Literal, Protocol


class Gaze(Protocol):
    x: float
    y: float


class CompanionChannel:
    def __init__(
        self,
        sample_query: Callable[[Any], Any],
        channel_information_dict: Dict[str, str],
    ):
        self.sample_query = sample_query
        self.information_dict = channel_information_dict

    def append_to(self, channels: pylsl.XMLElement):
        chan = channels.append_child("channel")
        for entry in self.information_dict:
            chan.append_child_value(entry, self.information_dict[entry])


def companion_event_channels():
    return [
        CompanionChannel(
            sample_query=pi_extract_from_sample("name"),
            channel_information_dict={"label": "Event", "format": "string"},
        )
    ]


def companion_gaze_channels() -> List[CompanionChannel]:
    channels: List[CompanionChannel] = []
    # ScreenX, ScreenY: screen coordinates of the gaze cursor
    channels.extend(
        [
            CompanionChannel(
                sample_query=pi_extract_gaze_query(i),
                channel_information_dict={
                    "label": "xy"[i],
                    "eye": "both",
                    "metatype": "Screen" + "XY"[i],
                    "unit": "pixels",
                    "coordinate_system": "world",
                },
            )
            for i in range(2)
        ]
    )
    return channels


def pi_extract_gaze_query(dim: Literal[0, 1]) -> Callable[[Gaze], float]:
    return lambda gaze: [gaze.x, gaze.y][dim]


def pi_extract_from_sample(value: str) -> Callable[[Any], Any]:
    return lambda sample: getattr(sample, value)
