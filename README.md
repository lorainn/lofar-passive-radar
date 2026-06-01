# lofar-passive-radar
Developed code for the use of LOFAR as a passive radar for space object detection and parameter determination, such as bistatic position and velocity.

This repository contains all the code developed during the bachelor’s thesis “Development of a System for Satellite Detection and Parameter Determination Using LOFAR as a Passive Radar”.

**Repository Contents**
- help-codes/: Third-party codes for comprehensive understanding of processing pipeline and data recording of beamforming observations on LOFAR stations. 
- ISSTrack.ini: Authentication for SpaceTrack historic TLE files. 
- spacetrack.py: Python code for TLE queries.
- map_iss.ipynb: Target's flight path visualization over European map.
- read_udp_pack.ipynb: Main data processing pipeline code for waterfall plot, UDP packet parsing, etc. 
- caf_pipeline.ipynb: Radar processing pipeline taking the beamlet data stream with the Doppler-Range map and temporal plots as outputs.

**Key Features**
- Parsing of UDP packets.
- Removal of beamlets containing exclusively null values.
- Three-dimensional waterfall plot of all 10 recorded beamlets.
- Model of reference signal.
- DPI and clutter cancellation from the surveillance signal.
- Cross-ambiguity function calculation.
- Doppler-range map plot.
- Bistatic range and velocity calculation.
- Bistatic parameters and SNR plot.

**Modes of Use**
- Jupyter Notebooks
- Google Colab
- Alternative IDEs

**System Requirements**
- Python 3.9.12

