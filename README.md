# ![wriple thumbnail][wriple-thumbnail] Wriple ![wriple badge][wriple-badge]
A webpage application that can detect motion in the environment using Wi-Fi signal. This application provides basic tools for data collection, model generation and model application. Using ESP32 module, Wi-Fi CSI data can be collected and process in real-time. Data collection can be done conveniently in Windows OS and perform real-time motion detection using webapp. It is a great startup to understanding Wi-Fi signal that can lead to other potential applications.

## Table of Contents
- [Features](#features)
- [Data Collection Guidelines](#data-collection-guidelines)
- [Installation](#installation)
- [Model Generation](#model-generation)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features
![wriple-main][wriple-main]
### Monitoring Mode
- **Monitor Movement** - Detect movement in real-time using the model prediction.
- **Visualize Signal** - Visualize the changes in signal in real-time for better signal understanding.
- **Signal Sensitivity** - Adjust the amount of signal to plot based on standard deviation.

### Data Collection Mode
- **Record Signal** - Record Wi-Fi signal for 2.5 seconds/250 packet each recording.
- **CSV Files Selection** - Visualize the selected CSV file.
- **Class Selection** - Set the class of Wi-Fi signal recording.
- **Activity Selection** - Set the activity of Wi-Fi signal recording.

### Additional Features
![wriple-visualization][wriple-visualization]
- **Movement Detection State** - Display 'Movement Detected' if movement is detected.
- **Signal Packet Counter** - Display the amount of packet received.

> [!NOTE]
> In monitoring mode, the system prediction is based on 3 seconds/300 packets, divided into 2 prediction with 200 combined packet each ([0:200], [100:300]).

> [!NOTE]
> Visualizer displays a 3D plot chart of amplitude, phase and subcarrier.

## Data Collection Guidelines
![data-collection-room][data-collection-room]
![data-collection-open-field][data-collection-open-field]

*Data Collection Setup*

![data-collection-process][data-collection-process] 
1. Perform the data collection in a controlled environment with no any movement and less Wi-Fi activity to maintain high quality dataset.
2. Performing the data collection for 'no movement' at night where there is no moving person, pet and appliances is recommended.
3. Place the ESP32 module in a mid to high open place with proper distancing and minimal obstruction to the station.
4. Immediately perform the movement even before the recording starts.
5. Plan or keep a note of range of files that contains 'no movement and 'movement' for better dataset quantity control.
6. Keep the type of movement the same for consistent number of times for easier recording process and avoid potential mislabeled dataset.
7. Use the ESP32 blue LED blinking state as queue if the recording already complete.

## Model Generation
![dataset-features][dataset-features]
![model-training-process][model-training-process]

The collected Channel State Information (CSI) from ESP32 is composed of 306 subcarriers. Subcarrier 66 to 123 was selected for having the highest performance while reducing the dataset into 57 subcarrier. Moving average and phase unwrapping was perform in the dataset to reduce the noise and subcarrier to 23. Finally, the amplitudes and phase standard deviation, phases 75th percentile count, and phases entropy was calculated for every 200 packets. With 23 subcarrier for each calculation, there is a total of 92 features in the dataset.

According to evaluation of different models, Extra Trees Classifier produced the best performance in different metrics. The Extra Trees Classifier is then trained, tuned and evaluate using the dataset to achieve the best performance. Producing the highest score with lowest margin between training, testing and cross-validation score was the main focus of the evaluation to be able for the model to perform close to the real-life application.

## Installation
1. Download the latest version of [Wriple][release-page].
2. Install [Wriple-1.0.0-Beta.exe][latest-release].
3. Make sure to include `pip` during Python installation.
9. Open [127.0.0.3:3000](http://127.0.0.3:3000) using browser to access the web application.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments
- **[Visual Studio Code][visual-studio-code]**: For development environment.
- **[Draw.io][matplotlib]**: For generating diagrams and visual workflows.
- **[Advanced Installer][advanced-installer]**: For installer.
- **[Jupyter Notebook][matplotlib]**: For prototyping, testing, and visualizing machine learning models.
- **[ESP-IDF][matplotlib]**: For development framework on the ESP32 microcontroller.
- **[D3.js][matplotlib]**: For JavaScript library for 3D visualization.
- **[css.gg][css-gg]**: For icons.
- **[Flask-CORS][flask-cors]**: For handling resource sharing between Python and JavaScript.
- **[waitress][waitress]**: For production-ready WSGI server.
- **[NumPy][numpy]**: For handling different types of arrays.
- **[Pandas][pandas]**: For data manipulation and analysis of Excel data.
- **[Matplotlib ][matplotlib]**: For generating scatter-plot chart.
- **[Scikit-learn][scikit-learn]**: For machine learning and statistical modeling.
- **[SciPy][matplotlib]**: For scientific computation library.
- **[Scapy][matplotlib]**: For packet manipulation library.
- **[Npcap][matplotlib]**: For packet capturing.

<!-- Reference -->
[wriple-thumbnail]: https://github.com/user-attachments/assets/82e654fb-5a38-4e94-8d7a-98edb4133038
[wriple-badge]: https://img.shields.io/badge/Web_App-Real_time_Motion_Sensing_System-8B4513

[wriple-main]: https://github.com/user-attachments/assets/de860e1f-ffcc-4517-a8f5-f4801f4fae0f
[wriple-visualization]: https://github.com/user-attachments/assets/c567c433-c610-45ee-8383-0c36c0e201d0

[data-collection-room]: https://github.com/user-attachments/assets/14a989c5-07d8-4bc1-8dc7-66615efc4c57
[data-collection-open-field]: https://github.com/user-attachments/assets/fc1fcc61-c445-4ead-85a8-3d66b25e385c
[data-collection-process]: https://github.com/user-attachments/assets/1f20ace4-ea5c-4af1-8054-751f81f2111a

[dataset-features]: https://github.com/user-attachments/assets/a80f3a9b-b766-447d-b1e2-0d5398c7bd54
[model-training-process]: https://github.com/user-attachments/assets/1fbbc33c-68c7-4f7e-8ec0-75ebcf6ff656

[release-page]: https://github.com/AHG-BSCS/Wiremap/releases
[latest-release]: https://github.com/AHG-BSCS/Wiremap/releases/download/v1.0.0-Beta/Wriple-1.0.0-Beta.exe
[visual-studio-code]: https://code.visualstudio.com/docs
[advanced-installer]: https://www.advancedinstaller.com/user-guide/using.html
[css-gg]: https://css.gg/
[flask-cors]: https://flask-cors.readthedocs.io/en/latest/api.html
[waitress]: https://docs.pylonsproject.org/projects/waitress/en/stable/index.html
[numpy]: https://numpy.org/doc/stable/index.html
[scikit-learn]: https://scikit-learn.org/0.21/documentation.html
[pandas]: https://pandas.pydata.org/docs/
[matplotlib]: https://matplotlib.org/stable/users/index
