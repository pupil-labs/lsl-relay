import asyncio
import logging
import uuid
from typing import Iterable, List, NoReturn, Optional

from pupil_labs.realtime_api import Device, StatusUpdateNotifier, receive_gaze_data
from pupil_labs.realtime_api.models import Component, Event, Sensor
from pupil_labs.realtime_api.streaming import GazeData
from pupil_labs.realtime_api.time_echo import TimeOffsetEstimator

from pupil_labs.lsl_relay import outlets

logger = logging.getLogger(__name__)
logging.getLogger("pupil_labs.realtime_api.time_echo").setLevel("WARNING")


class Relay:
    @classmethod
    async def run(
        cls,
        device_ip: str,
        device_port: int,
        device_identifier: str,
        outlet_prefix: str,
        model: str,
        module_serial: str,
        time_sync_interval: int,
    ):
        receiver = DataReceiver(device_ip, device_port)
        await receiver.estimate_clock_offset()
        relay = cls(
            device_ip,
            device_port,
            receiver,
            device_identifier,
            outlet_prefix,
            model,
            module_serial,
            time_sync_interval,
        )
        await relay.relay_receiver_to_publisher()
        await receiver.cleanup()

    def __init__(
        self,
        device_ip: str,
        device_port: int,
        receiver: "DataReceiver",
        device_identifier: str,
        outlet_prefix: str,
        model: str,
        module_serial: str,
        time_sync_interval: int,
    ):
        self.device_ip = device_ip
        self.device_port = device_port
        self.receiver = receiver
        self.session_id = str(uuid.uuid4())
        self.gaze_outlet = outlets.PupilCompanionGazeOutlet(
            device_id=device_identifier,
            outlet_prefix=outlet_prefix,
            model=model,
            module_serial=module_serial,
            session_id=self.session_id,
            clock_offset_ns=self.receiver.clock_offset_ns,
        )
        self.event_outlet = outlets.PupilCompanionEventOutlet(
            device_id=device_identifier,
            outlet_prefix=outlet_prefix,
            model=model,
            module_serial=module_serial,
            session_id=self.session_id,
            clock_offset_ns=self.receiver.clock_offset_ns,
        )
        self.gaze_sample_queue: asyncio.Queue[GazeAdapter] = asyncio.Queue()
        self.publishing_gaze_task = None
        self.publishing_event_task = None
        self.receiving_task = None
        self._time_sync_interval = time_sync_interval

    async def receive_gaze_sample(self):
        while True:
            if self.receiver.gaze_sensor_url:
                async for gaze in receive_gaze_data(
                    self.receiver.gaze_sensor_url, run_loop=True, log_level=30
                ):
                    if isinstance(gaze, GazeData):
                        await self.gaze_sample_queue.put(
                            GazeAdapter(gaze, self.receiver.clock_offset_ns)
                        )
                    else:
                        logger.warning(f"Dropping unknown gaze data type: {gaze}")
            else:
                logger.debug("The gaze sensor was not yet identified.")
                await asyncio.sleep(1)

    async def publish_gaze_sample(self, timeout: float):
        missing_sample_duration = 0
        while True:
            try:
                sample = await asyncio.wait_for(self.gaze_sample_queue.get(), timeout)
                self.gaze_outlet.push_sample_to_outlet(sample)
                if missing_sample_duration:
                    missing_sample_duration = 0
            except asyncio.TimeoutError:
                missing_sample_duration += timeout
                logger.warning(
                    "No gaze sample was received for %i seconds.",
                    missing_sample_duration,
                )

    async def publish_event_from_queue(self):
        while True:
            event = await self.receiver.event_queue.get()
            self.event_outlet.push_sample_to_outlet(event)

    async def start_receiving_task(self):
        if self.receiving_task:
            logger.debug("Tried to set a new receiving task, but the task is running.")
            return
        self.receiving_task = asyncio.create_task(self.receive_gaze_sample())

    async def start_publishing_gaze(self):
        if self.publishing_gaze_task:
            logger.debug(
                "Tried to set a new gaze publishing task, but the task is running."
            )
            return
        self.publishing_gaze_task = asyncio.create_task(self.publish_gaze_sample(10))

    async def start_publishing_event(self):
        if self.publishing_event_task:
            logger.debug(
                "Tried to set new event publishing task, but the task is running."
            )
            return
        self.publishing_event_task = asyncio.create_task(
            self.publish_event_from_queue()
        )

    async def relay_receiver_to_publisher(self):
        tasks = await self.initialise_tasks()
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        handle_done_pending_tasks(done, pending)

    async def initialise_tasks(self) -> List["asyncio.Task[NoReturn]"]:
        await self.receiver.make_status_update_notifier()
        await self.start_receiving_task()
        await self.start_publishing_gaze()
        await self.start_publishing_event()
        tasks = [
            self.receiving_task,
            self.publishing_gaze_task,
            self.publishing_event_task,
        ]
        # start time sync task
        if self._time_sync_interval:
            time_sync_task = asyncio.create_task(
                send_events_in_interval(
                    self.device_ip,
                    self.device_port,
                    self.session_id,
                    self._time_sync_interval,
                )
            )
            tasks.append(time_sync_task)
        return [t for t in tasks if t is not None]


class DataReceiver:
    def __init__(self, device_ip: str, device_port: int):
        self.device_ip = device_ip
        self.device_port = device_port
        self.notifier: Optional[StatusUpdateNotifier] = None
        self.gaze_sensor_url: Optional[str] = None
        self.event_queue: asyncio.Queue[EventAdapter] = asyncio.Queue()
        self.clock_offset_ns: int = 0

    async def on_update(self, component: Component):
        if isinstance(component, Sensor):
            if component.sensor == "gaze" and component.conn_type == "DIRECT":
                self.gaze_sensor_url = component.url
        elif isinstance(component, Event):
            adapted_event = EventAdapter(component, self.clock_offset_ns)
            await self.event_queue.put(adapted_event)

    async def make_status_update_notifier(self):
        async with Device(self.device_ip, self.device_port) as device:
            self.notifier = StatusUpdateNotifier(device, callbacks=[self.on_update])
            await self.notifier.receive_updates_start()

    async def estimate_clock_offset(self):
        """Estimate the Companion-Device-to-Relay clock offset.

        Uses the :py:mod:`Pupil Labs Time Echo Protocol
        <pupil_labs.realtime_api.time_echo>` to measure the clock offset between the
        Companion Device and the relay. The offset is used to transform incoming gaze
        and event timestamps from Companion to relay time domain. If the Companion app
        version does not support the time echo protocol or the clock offset estimation
        fails, the relay will fall back to NTP-based time sync.
        """
        async with Device(self.device_ip, self.device_port) as device:
            status = await device.get_status()

            if status.phone.time_echo_port is None:
                logger.warning(
                    "Pupil Companion app is out-of-date and does not support "
                    "accurate time sync! Relying on less accurate NTP time sync."
                )
                return
            logger.debug(f"Device Time Echo port: {status.phone.time_echo_port}")

            time_offset_estimator = TimeOffsetEstimator(
                status.phone.ip, status.phone.time_echo_port
            )
            estimated_offset = await time_offset_estimator.estimate()
            if estimated_offset is None:
                logger.warning(
                    "Estimating clock offset failed. Relying on less accurate NTP time "
                    "sync."
                )
                return
            self.clock_offset_ns = round(estimated_offset.time_offset_ms.mean * 1e6)
            logger.info(f"Estimated clock offset: {self.clock_offset_ns:_} ns")

    async def cleanup(self):
        if self.notifier is not None:
            await self.notifier.receive_updates_stop()


class GazeAdapter:
    def __init__(self, sample: GazeData, clock_offset_ns: int):
        self.x = sample.x
        self.y = sample.y
        self.timestamp_unix_seconds = (
            sample.timestamp_unix_seconds + clock_offset_ns * 1e-9
        )


class EventAdapter:
    def __init__(self, sample: Event, clock_offset_ns: int):
        self.name = sample.name
        self.timestamp_unix_seconds = (sample.timestamp + clock_offset_ns) * 1e-9


def handle_done_pending_tasks(
    done: Iterable["asyncio.Task[NoReturn]"],
    pending: Iterable["asyncio.Task[NoReturn]"],
):
    for done_task in done:
        try:
            done_task.result()
        except asyncio.CancelledError:
            logger.warning(f"Cancelled: {done_task}")

    for pending_task in pending:
        try:
            pending_task.cancel()
        except asyncio.CancelledError:
            # cancelling is the intended behaviour
            pass


# send events in intervals
async def send_events_in_interval(
    device_ip: str, device_port: int, session_id: str, sec: int = 60
):
    n_events_sent = 0
    while True:
        await send_timesync_event(
            device_ip, device_port, f"lsl.time_sync.{session_id}.{n_events_sent}"
        )
        await asyncio.sleep(sec)
        n_events_sent += 1
        logger.debug(f"sent time synchronization event no {n_events_sent}")


async def send_timesync_event(device_ip: str, device_port: int, message: str):
    async with Device(device_ip, device_port) as device:
        # NOTE: No need to set timestamp with clock offset. Device already timestamps
        # events on reception in target time domain.
        await device.send_event(message)
