3.1.0 (2023-05-25)
##################
- Adds official support for Neon modules
- New project name pupil-labs-lsl-relay

3.0.2 (2022-11-09)
##################
- Gracefully handle xdf files without required time alignment information

3.0.1 (2022-10-25)
##################
- Detect missing dependencies and provide instructions on how to install them
- Document how to install time alignment dependencies in the corresponding guide

3.0.0.post1 (2022-10-25)
########################
- Fix displayed version in docs

3.0.0 (2022-10-25)
##################
- Estimate and correct clock offset between Companion device and relay
  (:py:meth:`pupil_labs.lsl_relay.relay.DataReceiver.estimate_clock_offset`)
- Add estimated clock offset to acquisition info
- Add command line tool for lsl-to-cloud time alignment and vice versa
- Change the events sent for time alignment to include a unique session id
- Add command line tool for monitoring sampling rates in real time
- Add example on how to apply estimated time alignments
- Update module skeleton
- Update pre-commit config
- [Backwards-incompatible API change] Restructured
  (:py:class:`pupil_labs.lsl_relay.relay.Relay`) two-step setup into a single
  :py:meth:`class method call <pupil_labs.lsl_relay.relay.Relay.run>`

2.1.0
#####
- Add check for correct epoch
- Allow for direct device selection through command line argument
- Outlet prefix can be set though command line argument
- Restructure relay module to accept device ip and port explicitly, instead of accepting DiscoveredDeviceInfo
- Add an acquisition field to the outlet metadata, including manufacturer, model, version and the
  serial number of the world camera

2.0.2
#####
- Fix default duration of network search (10 seconds)
- Fix default interval for time synchronization events (60 seconds)

2.0.1
#####
- Document minimum Pupil Invisible Companion version required (v1.4.14)
- Add code example demonstrating post-hoc time sync between a Pupil Cloud download and
  a LSL recording
- Write debug logs to log file (path defined via ``--log_file_name`` parameter)

  - Requires `click <https://pypi.org/project/click/>`_ instead of `asyncclick
    <https://pypi.org/project/asyncclick/>`_

2.0.0
#####
- First release supporting the `Pupil Labs Network API <https://github.com/pupil-labs/realtime-network-api>`_
- The legacy NDSI-based relay application can be found
  `here <https://github.com/labstreaminglayer/App-PupilLabs/tree/legacy-pi-lsl-relay/pupil_invisible_lsl_relay>`_

- Pull project skeleton from `<https://github.com/pupil-labs/python-module-skeleton>`_
- Initial fork from `<https://github.com/labstreaminglayer/App-PupilLabs>`_
