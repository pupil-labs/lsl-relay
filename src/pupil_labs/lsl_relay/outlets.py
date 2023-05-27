import logging
import time
from typing import Callable, Dict, List

import pylsl as lsl
from typing_extensions import Literal, Protocol

from pupil_labs.lsl_relay import __version__
from pupil_labs.lsl_relay.channels import (
    CompanionChannel,
    companion_event_channels,
    companion_gaze_channels,
)

VERSION: str = __version__

# lsl.cf_float32, lsl.cf_double64, lsl.cf_string, lsl.cf_int32, lsl.cf_int16,
# lsl.cf_int8, lsl.cf_int64, lsl.cf_undefined
LSLChannelFormatConstant = Literal[1, 2, 3, 4, 5, 6, 7, 0]

logger = logging.getLogger(__name__)


class Sample(Protocol):
    timestamp_unix_seconds: float
    "Unix-epoch timestamp in seconds"


class PupilCompanionOutlet:
    def __init__(
        self,
        channel_func: Callable[[], List[CompanionChannel]],
        outlet_type: str,
        outlet_format: LSLChannelFormatConstant,
        outlet_name_prefix: str,
        outlet_uuid: str,
        acquisition_info: Dict[str, str],
    ):
        self._outlet_uuid = outlet_uuid
        self._channels = channel_func()
        self._outlet = pi_create_outlet(
            self._outlet_uuid,
            self._channels,
            outlet_type,
            outlet_format,
            outlet_name_prefix,
            acquisition_info,
        )

    def push_sample_to_outlet(self, sample: Sample):
        try:
            sample_to_push = [chan.sample_query(sample) for chan in self._channels]
            timestamp_to_push = sample.timestamp_unix_seconds - get_lsl_time_offset()
        except Exception as exc:
            logger.error(f"Error extracting from sample: {exc}")
            logger.debug(str(sample))
            return
        self._outlet.push_sample(sample_to_push, timestamp_to_push)


class PupilCompanionGazeOutlet(PupilCompanionOutlet):
    def __init__(
        self,
        device_id: str,
        outlet_prefix: str,
        model: str,
        module_serial: str,
        session_id: str,
        clock_offset_ns: int = 0,
    ):
        PupilCompanionOutlet.__init__(
            self,
            channel_func=companion_gaze_channels,
            outlet_type="Gaze",
            outlet_format=lsl.cf_double64,
            outlet_name_prefix=outlet_prefix,
            outlet_uuid=f"{device_id}_Gaze",
            acquisition_info=compose_acquisition_info(
                version=VERSION,
                module_serial=module_serial,
                model=model,
                session_id=session_id,
                clock_offset_ns=clock_offset_ns,
            ),
        )


class PupilCompanionEventOutlet(PupilCompanionOutlet):
    def __init__(
        self,
        device_id: str,
        outlet_prefix: str,
        model: str,
        module_serial: str,
        session_id: str,
        clock_offset_ns: int = 0,
    ):
        PupilCompanionOutlet.__init__(
            self,
            channel_func=companion_event_channels,
            outlet_type="Event",
            outlet_format=lsl.cf_string,
            outlet_name_prefix=outlet_prefix,
            outlet_uuid=f"{device_id}_Event",
            acquisition_info=compose_acquisition_info(
                version=VERSION,
                module_serial=module_serial,
                session_id=session_id,
                clock_offset_ns=clock_offset_ns,
                model=model,
            ),
        )


def pi_create_outlet(
    outlet_uuid: str,
    channels: List[CompanionChannel],
    outlet_type: str,
    outlet_format: LSLChannelFormatConstant,
    outlet_name_prefix: str,
    acquisition_info: Dict[str, str],
):
    stream_info = pi_streaminfo(
        outlet_uuid,
        channels,
        outlet_type,
        outlet_format,
        outlet_name_prefix,
        acquisition_info,
    )
    return lsl.StreamOutlet(stream_info)


def pi_streaminfo(
    outlet_uuid: str,
    channels: List[CompanionChannel],
    type_name: str,
    channel_format: LSLChannelFormatConstant,
    outlet_name_prefix: str,
    acquisition_info: Dict[str, str],
):
    stream_info = lsl.StreamInfo(
        name=f"{outlet_name_prefix}_{type_name}",
        type=type_name,
        channel_count=len(channels),
        channel_format=channel_format,
        source_id=outlet_uuid,
    )
    xml_acquisition = stream_info.desc().append_child("acquisition")
    for key in acquisition_info.keys():
        xml_acquisition.append_child_value(key, acquisition_info[key])
    xml_channels = stream_info.desc().append_child("channels")
    [chan.append_to(xml_channels) for chan in channels]
    return stream_info


def get_lsl_time_offset():
    return time.time() - lsl.local_clock()


def compose_acquisition_info(
    version: str,
    module_serial: str,
    session_id: str,
    manufacturer: str = "Pupil Labs",
    model: str = "Pupil Labs Device",
    clock_offset_ns: int = 0,
) -> Dict[str, str]:
    return {
        "manufacturer": manufacturer,
        "model": model,
        "serial_number": module_serial,
        "lsl_relay_version": version,
        "session_id": str(session_id),
        "clock_offset_ns": str(clock_offset_ns),
    }
