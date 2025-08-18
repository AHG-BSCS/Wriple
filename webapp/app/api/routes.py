"""Route handlers for the Human Presence Detection System"""

from flask import jsonify, request, render_template
from .validators import validate_recording_parameters, validate_class, validate_obstruction, validate_activity


def create_api_routes(app, detection_system):
    """Create and register all API routes with the Flask app"""
    
    # A trick to explicitly set the detection_system instance variable
    from main import HumanDetectionSystem
    detection_system: HumanDetectionSystem = detection_system
    
    @app.route('/')
    def serve_index():
        """Serve the main HTML page"""
        return render_template('index.html')
    
    @app.route('/fetch_system_icon_status', methods=['POST'])
    def fetch_system_icon_status():
        """Get system component status"""
        try:
            status = detection_system.get_system_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/fetch_monitor_status', methods=['POST'])
    def fetch_monitor_status():
        """Get capturing data and presence predictions"""
        try:
            radar_status = detection_system.get_monitor_status()
            return jsonify(radar_status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/capture_data/monitor', methods=['POST'])
    def start_monitoring():
        """Start monitoring mode"""
        if not detection_system.network_manager.check_esp32():
            return jsonify({'message': 'ESP32 is not connected'}), 400
        
        detection_system.start_capturing(is_recording=False)
        return jsonify({'message': 'Monitoring started'}), 200
    
    @app.route('/capture_data/record', methods=['POST'])
    def start_recording():
        """Start recording mode with parameters"""
        if not detection_system.network_manager.check_esp32():
            return jsonify({'message': 'ESP32 is not connected'}), 400
        
        params = request.get_json()
        
        if not validate_recording_parameters(params):
            return jsonify({'message': 'Missing required field'}), 400
        
        if not validate_class(params):
            return jsonify({'message': 'Invalid recording class parameter'}), 400
        
        if not validate_obstruction(params):
            return jsonify({'message': 'Invalid recording obstruction parameter'}), 400
        
        if not validate_activity(params):
            return jsonify({'message': 'Invalid recording activity parameter'}), 400
        
        detection_system.set_recording_parameters(params)
        detection_system.start_capturing(is_recording=True)
        return jsonify({'message': 'Recording started'}), 200
    
    @app.route('/capture_data/stop', methods=['POST'])
    def stop_capturing():
        """Stop recording or monitoring"""
        try:
            # TODO: Log the number of packets captured during stop
            detection_system.stop_operations()
            return jsonify({'status': 'stopped'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/visualize_3d_plot', methods=['POST'])
    def visualize_3d_plot():
        """Get processed signal data for visualization"""
        try:
            signal_coordinates = detection_system.csi_processor.get_amp_phase_3d_coords()
            return jsonify({'signalCoordinates': signal_coordinates})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/get_radar_data', methods=['POST'])
    def get_radar_data():
        """Get radar data and presence predictions"""
        try:
            radar_status = detection_system.get_radar_status()
            return jsonify(radar_status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/get_mmwave_heatmap_data', methods=['POST'])
    def mmwave_heatmap():
        raw = detection_system.mmwave_data[-1]
        heatmap = []
        
        # Apply Thresholds
        thresholds = detection_system.model_manager.mmWave_thresholds
        for doppler_idx, row in enumerate(raw):
            for gate_idx, value in enumerate(row):
                threshold = thresholds[doppler_idx][gate_idx]
                if value <= threshold:
                    value = 0.0
                heatmap.append([doppler_idx, gate_idx, value])
        
        return jsonify({'latestDoppler': heatmap})

    @app.route('/fetch_amplitude_data', methods=['POST'])
    def fetch_amplitude_data():
        """Get latest amplitude data subset"""
        try:
            latest_amplitudes = detection_system.csi_processor.get_latest_amplitude()
            return jsonify({'latestAmplitudes': latest_amplitudes})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/fetch_phase_data', methods=['POST'])
    def fetch_phase_data():
        """Get latest phase data subset"""
        try:
            latest_phases = detection_system.csi_processor.get_latest_phase()
            return jsonify({'latestPhases': latest_phases})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # CSV File Management Routes
    
    @app.route('/list_csv_files', methods=['POST'])
    def list_csv_files():
        """List all recorded CSV files"""
        try:
            files = detection_system.file_manager.list_csv_files()
            return jsonify(files)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/visualize_csv_file', methods=['POST'])
    def select_csv_file(filename):
        """Set a CSV file for visualization"""
        filename = request.get_json()
        if (detection_system.file_manager.select_csv_file(filename)):
            detection_system.csi_processor.set_max_packets(0)
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'}), 404
    
    # Error Handlers
    
    # @app.errorhandler(404)
    # def not_found(error):
    #     return jsonify({'error': 'Endpoint not found'}), 404
    
    # @app.errorhandler(500)
    # def internal_error(error):
    #     return jsonify({'error': 'Internal server error'}), 500
