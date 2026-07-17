# <img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/app/static/images/icon.png" width="28" alt="Logo Thumbnail"> WRIPLE ![wriple badge][wriple-badge]
A cross-platform desktop application that uses Wi-Fi and millimeter wave (mmWave) signal to detect human presence behind obstruction. This system is possible by taking advantage of Wi-Fi CSI capable ESP32 module, a RDM-capable HLK-LD2420 mmWave radar, that the WRIPLE application designed to communicate with. Tools such as simple radar, signal heatmap, detection linechart, and data collection *(hidden tab)* are available to be used during operation. A Conv-LSTM deep learning model is being used to detect human presence based on the collected Wi-Fi CSI or mmWave RDM. Access the ESP32-WROOM-32U module firmware [here][wriple-firmware]. Email the developer for any questions and development that this software has been used.

## Table of Contents
- [Features](#features)
- [Data Collection](#data-collection)
- [Relevant Processes](#relevant-processes)
- [Installation](#installation)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features
### Monitoring Tab
<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-system-status.png" width="700" alt="System Status">

- **Status Bar** - System status bar indicates the different required components of the system to function properly. This includes the Wi-Fi, Server, ESP32, LD2420 and ML model. Missing one of those components will cause the application functionality dependent on a specific component to not work properly.

<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-system-info.png" width="700" alt="System Info">

- **Monitoring Mode** - Transmit and receive packets between the station and ESP32. Each packet contains a single sample of CSI data, and an RDM sample once every `~20 packets` or `333 ms`. Before the system detects human presence, for the first `15 seconds`, the application will first perform some calibration to adapt to the new environment, and ensure that the signal noise is below `50` for reliable prediction. To reduce the signal noise, adjust the setup position, LOS and height. A messages such as `Noisy`, `Calibrating`, and `Restart` will be displayed in the presence section depending on the status of the system to assist the user. After that, for every `120 samples or 2 seconds` of CSI data, one human presence detection will be performed, and its result is displayed in the `Presence` section. The total number of packets, loss of signal, signal noise and RSSI were all updated in real-time during monitoring mode.

<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-rdm-radar.png" width="700" alt="RDM Radar">

- **mmWave Radar** - This mmWave is not capable of detecting human presence behind obstruction, therefore, this radar can only be used for target with direct LOS. The radar detection is highly accurate but the distance estimation is still experimental. For future development, this radar can be used for visualization of other mmWave radar capability in the market.

<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-csi-heatmap.png" width="700" alt="CSI Heatmap">

- **Amplitude Heatmap** - Provides a real-time heatmap of CSI amplitudes and mmWave RDM. The heatmap data is composed of selected subcarriers, then preprocessed to improve visualization. The heatmap flows from right to left `10x/second`. The canvas is limited to store up to `15 seconds` of amplitude data since visualizing more data consumes significant processing power. This heatmap can be used by the user to manually identify patterns in case experimentation and unreliable model.

<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-rdm-heatmap.png" width="700" alt="RDM Heatmap">

- **RDM Heatmap** - Provides a real-time heatmap of range-doppler map (RDM). Unlike the Amplitude Heatmap, this heatmap refresh for every `333 ms` according to the HLK-LD2420 hardware limitation. The heatmap data is composed of `16 range-bins` and `20 doppler-bins` that's been normalized to improve visualization. Because of nature of range-doppler map, user can visualize the target position based on the position of hotspot in the heatmap.

<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-csi-noise-line-chart.png" width="700" alt="CSI Noise Linechart">

- **CSI Noise Linechart** - Show a line chart that tracks the noise level of the environment and sets up over time for up to `25 seconds`. The displayed data is similar to the `Noise` section of the status bar. Users are recommended to continuously adjust the setup and position of the AP and ESP32 until consistent noise level below `2.0` is achieved. The purpose of this feature is purely for achieving acceptable signal noise level for reliable human presence detection of the model and even during data collection.

<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-detection-line-chart.png" width="700" alt="Detection Linechart">

- **Detection Linechart** - Aside from looking at the `Presence` status in the status bar, detection results can also be tracked using a line chart for the past `50 seconds`. This allows the user to leave the station for a short amount of time, or have a better insights of the detection pattern over time. 


## Data Collection
### Data Collection Tool
<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/ui-dataset-collection.png" width="700" alt="Dataset Collection">

- **Record** - Record Wi-Fi CSI signal at `60 samples/second` and mmWave RDM signal at `3 samples/second` for `4 seconds` each recording, just enough to capture a single human breathing cycle. Clicking the button while recording will stop the recording and the CSV file will be incomplete or invalid for dataset. In this case, user have to manually delete the file.
- **Parameters Selection** - Set the parameters based on the data collection setup before taking the recording.
- **CSV Files Selection** - Review the selected CSV file metadata to ensure data integrity.

### Data Collection Setup
<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/fig-data-collection-setup.png" width="700" alt="Data Collection Setup">

1. Perform the data collection in a controlled environment with no other human presence and less Wi-Fi activity to maintain high quality signal.
2. Immediately perform the movement even before the recording starts.
3. Plan or keep track of group of files that contains different class to avoid confusion during data collection.
4. Keep the amount of recording for the different class and distance the same for balanced dataset classes.
5. Use the ESP32 DFWS prototype LED state as signal if the recording is complete.

## Relevant Processes
### System Use Case
<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/fig-system-use-case.png" width="700" alt="System Use Case">

- The WRIPLE system is composed of DFWS prototype, AP, and the application. To start the system to detect human presence, the user has to first connect all the system components. First, AP must be configured to use `WRIPLE` as SSID, `WRIPLE_ESP32` as password, and `2.4 GHz` as AP frequency
band to allow the DFWS prototype to automatically connect. Powering the DFWS prototype using a compatible power supply like power bank will automatically connect it to the AP on startup. The application status bar can be used to check for different system components in real-time. Once everything is connected, monitoring and visualization can be started to detect human presence.
> [!NOTE]
> If the application cannot establish connection to ESP32, try to enable the device (laptop) location.

### UDP Hole Punching
<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/fig-udp-hole-punching.png" width="700" alt="UDP Hole Punching">

- UDP hole punching method was used for the ESP32 and the Station to both connect to the same AP, establishing a simple two-way
communication channel. During the boot of ESP32, once connected to the AP, it starts listening to the broadcast messages of the AP. The Station sends a broadcast message on the local network so the ESP32 can learn its IP address. ESP32 then sends an outbound UDP packet to the discovered Station’s IP address so that Station can learn the ESP32 IP address. Because most operating systems and AP create a temporary state for outbound
UDP traffic, that outbound packet implicitly opens a short-lived `pinhole` that allows the corresponding inbound UDP packets to be received. This approach avoids having to add explicit firewall rules on the Station. However, it is good practice to send periodic packets so the temporary mapping does not time out. Because of this nature, the Station and ESP32 connection might be closed unexpectedly, therefore restarting the ESP32 is needed.

### System Data Flow
<img src="https://github.com/AHG-BSCS/Wriple/blob/abe944b6865218dda24bf8eb1fa18c492c6f438f/docs/fig-system-data-flow.png" width="700" alt="System Data Flow">

- The system data flow demonstrates how the system process and collects Wi-Fi CSI and mmWave RDM data. First, the Station will transmit a data request packet to the ESP32 that is forwarded by the AP. ESP32 is configured to respond to every CSI-compatible packet. The moment a request data packet is received, ESP32 begins reading CSI and RDM data, which is then sent back to the Station. After the Station receives the response packet, data is parsed and stored in a separate CSI and RDM data queue for prediction and visualization purposes.

## Installation
1. Download and install the latest version of [WRIPLE][release-page].

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
### Tools
- **[draw.io][draw-io]**: For generating diagrams and visual workflows.
- **[Jupyter Notebook][jupyter-notebook]**: For machine learning and deep learning prototyping.
- **[Phosphor Icons][phosphor-icon]**: For tab and button icons.
### Frontend
- **[Tailwind CSS][tailwind]**: For CSS framework.
- **[simpleheat][simple-heat]**: For real-time heatmaps.
- **[Chart.js][chart-js]**: For real-time line charts.
- **[D3.js][d3-js]**: For 3D scatter plot visualization.
### Backend
- **[uv][uv]**: For Python dependencies manager and virtual environment.
- **[Flask-CORS][flask-cors]**: For handling resource sharing between Python and JavaScript.
- **[Waitress][waitress]**: For production-ready WSGI server.
- **[psutil][psutil]**: For system performance monitoring.
### Data Science
- **[Scikit-learn][scikit-learn]**: For machine learning and statistical modeling.
- **[TensorFlow][tensorflow]**: For deep learning framework.
- **[Joblib][joblib]**: For saving and loading trained machine learning models.
- **[Numpy][numpy]**: For handling different types of arrays.
- **[Pandas][pandas]**: For data manipulation and analysis.
- **[SciPy][scipy]**: For scientific computation library.
- **[Matplotlib][matplotlib]**: For generating different charts.
- **[Plotly][plotly]**: For generating interactive charts.
### Wrapper and Installer
- **[PyWebview][pywebview]**: For standalone web app wrapper.
- **[PyQt5][pyqt5]**: For native desktop window for Linux.
- **[QtPy][qtpy]**: For compatibility layer that PyWebview and PyQt5 used.
- **[PyQtWebEngine][pyqt-web-engine]**: For providing a chromium-based webview.
- **[PyInstaller][pyinstaller]**: For packaging the app into executables.
- **[Inno Setup][inno-setup]**: For installer.

<!-- Reference -->
[wriple-badge]: https://img.shields.io/badge/Desktop-Human_Presence_Detection_System-8B4513
[wriple-firmware]: https://github.com/AHG-BSCS/Wriple_ESP32

[release-page]: https://github.com/AHG-BSCS/Wriple/releases

[draw-io]: https://github.com/jgraph/drawio-desktop
[jupyter-notebook]: https://docs.jupyter.org/en/latest/
[phosphor-icon]: https://phosphoricons.com/?weight=%22fill%22&color=%221f2937%22&size=32&q=%22arrow%22
[tailwind]: https://tailwindcss.com/docs/installation
[simple-heat]: https://github.com/mourner/simpleheat
[chart-js]: https://www.chartjs.org/
[d3-js]: https://github.com/Niekes/d3-3d
[uv]: https://pypi.org/project/uv/
[flask-cors]: https://pypi.org/project/flask-cors/
[waitress]: https://pypi.org/project/waitress/
[psutil]: https://pypi.org/project/psutil/
[scikit-learn]: https://pypi.org/project/scikit-learn/
[tensorflow]: https://pypi.org/project/tensorflow/
[joblib]: https://joblib.readthedocs.io/en/stable/
[numpy]: https://pypi.org/project/numpy/
[pandas]: https://pypi.org/project/pandas/
[scipy]: https://pypi.org/project/scipy/
[matplotlib]: https://pypi.org/project/matplotlib/
[plotly]: https://pypi.org/project/plotly/
[pywebview]: https://pypi.org/project/pywebview/
[pyqt5]: https://pypi.org/project/PyQt5/
[qtpy]: https://pypi.org/project/QtPy/
[pyqt-web-engine]: https://pypi.org/project/PyQtWebEngine/
[pyinstaller]: https://pypi.org/project/pyinstaller/
[inno-setup]: https://jrsoftware.org/ishelp/
