:tocdepth: 3

************************************************************
Performing accurate time synchronization between two devices
************************************************************
You can use lsl to synchronize two Pupil Labs Companion Devices.


Description of the Choreography
===============================

We placed two Pupil Invisible Glasses in front of a light source, the eye cameras facing towards the light.
The scene cameras were detached from the glasses and the light source was switched off during setup. The Companion
Devices were set up such that both would upload the recorded data to the same Workspace.

An lsl relay was started for each of the Pupil Invisible Glasses, and the two lsl Event streams were recorded with
the LabRecorder. We did not record the lsl Gaze streams for this example.

After the lsl streams were running and being recording by the LabRecorder, we started recording in the Pupil Invisible
Companion App. After this step, the following data series were being recorded:

- Event data from each of the two Pupil Invisible Glasses (two data streams) are streamed and recorded via lsl and
  the LabRecorder.
- Event data from each pair of Pupil Invisible Glasses is saved locally on the Companion Device during the recording
  and uploaded to cloud once the recording completed.
- Eye Camera Images from each pair of Pupil Invisible Glasses are saved locally on the Companion Device and uploaded
  to Pupil Cloud when the recording completed. The 200 Hz Gaze position estimate is computed in Pupil Cloud.

With this setup in place and all recordings running, we switched the light source pointing at the eye cameras on
and off four times. This created a simultaneous signal recorded by the Eye Cameras (brightness increases).

After that, we stopped all recordings in the inverse order (first in the companion app, then in the LabRecorder) and
stopped the lsl relay.

Comparing NTP and LSL time sync
===============================

We used the :ref:`lsl_relay_time_alignment` tool to calculate the time alignments
between the two Companion devices and the computer running the LSL relay.

.. collapse:: Time Alignment Parameters - Subject 1

   .. literalinclude:: ../../examples/companion_app_exports/subject_1/time_alignment_parameters.json
      :language: json
      :linenos:

.. collapse:: Time Alignment Parameters - Subject 2

   .. literalinclude:: ../../examples/companion_app_exports/subject_2/time_alignment_parameters.json
      :language: json
      :linenos:

Then we extracted the illuminance for each eye video frame

.. collapse:: Illuminance Extraction Script

   .. literalinclude:: ../../tools/extract_eye_video_illuminance.py
      :language: python
      :linenos:

.. collapse:: Extracted Illuminance - Excerpt Subject 1 - Left Eye Video

   .. literalinclude:: ../../examples/companion_app_exports/subject_1/PI left v1 ps1.illuminance.csv
      :language: python
      :linenos:
      :lines: 1-10

With the script below, we load the time alignment configurations, apply them on the
extracted illuminance timestamps, and plot the illuminance for both recordings over
original and aligned timestamps.

.. collapse:: Script to Apply and Plot Time Alignment

   .. literalinclude:: ../../examples/device_vs_lsl_sync.py
      :language: python
      :linenos:

The resulting plot demonstrates the improved time sync when using the LSL-aligned
timestamps.

.. image:: ../../examples/illuminance_over_time.png
   :width: 800
   :alt: Illuminance over time
