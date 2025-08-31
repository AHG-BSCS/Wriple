"""Route handlers for the Human Presence Detection System"""

from flask import jsonify, request, render_template
from .validators import validate_recording_parameters, validate_class, validate_obstruction, validate_activity


def create_api_routes(app, detection_system):
    """Create and register all API routes with the Flask app"""
    
    # Set the detection_system instance object for usage reference
    from main import HumanDetectionSystem
    detection_system: HumanDetectionSystem = detection_system
    
    @app.route('/')
    def serve_index():
        """Serve the main HTML page"""
        return render_template('index.html')
    
    @app.route('/get_system_status', methods=['GET'])
    def get_system_status():
        """Get system component status"""
        status = detection_system.get_system_status()
        return jsonify(status), 200
    
    @app.route('/get_monitor_status', methods=['GET'])
    def get_monitor_status():
        """Get capturing data and presence predictions"""
        radar_status = detection_system.get_monitor_status()
        return jsonify(radar_status), 200
    
    @app.route('/start_monitoring', methods=['POST'])
    def start_monitoring():
        """Start monitoring mode"""
        detection_system.start_capturing(is_recording=False)
        return jsonify({'message': 'Monitoring started'}), 200
    
    @app.route('/start_recording', methods=['POST'])
    def start_recording():
        """Start recording mode with parameters"""
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
    
    @app.route('/stop_capturing', methods=['POST'])
    def stop_capturing():
        """Stop recording or monitoring"""
        detection_system.stop_operations()
        return jsonify({'message': 'Stopped capturing'}), 200
    
    @app.route('/get_amplitude_data', methods=['GET'])
    def get_amplitude_data():
        """Get latest amplitude data subset"""
        latest_amplitudes = detection_system.csi_processor.get_heatmap_data()
        return jsonify({'latestAmplitudes': latest_amplitudes}), 200
    
    @app.route('/get_phase_data', methods=['GET'])
    def get_phase_data():
        """Get latest phase data subset"""
        latest_phases = detection_system.csi_processor.get_latest_phase()
        return jsonify({'latestPhases': latest_phases}), 200
    
    @app.route('/get_radar_data', methods=['GET'])
    def get_radar_data():
        """Get radar data and presence predictions"""
        radar_status = detection_system.get_radar_status()
        return jsonify(radar_status), 200
    
    @app.route('/get_rdm_data', methods=['GET'])
    def get_rdm_data():
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
        
        return jsonify({'latestDoppler': heatmap}), 200
    
    @app.route('/get_3d_plot_data', methods=['GET'])
    def get_3d_plot_data():
        """Get processed signal data for visualization"""
        signal_coordinates = detection_system.csi_processor.get_3d_plot_data()
        return jsonify({'signalCoordinates': signal_coordinates}), 200
    
    # CSV File Management Routes
    
    @app.route('/get_csv_files', methods=['GET'])
    def get_csv_files():
        """List all recorded CSV files"""
        files = detection_system.file_manager.list_csv_files()
        return jsonify(files), 200
    
    @app.route('/read_csv_file', methods=['POST'])
    def read_csv_file(filename):
        """Set a CSV file for visualization"""
        filename = request.get_json()
        if (detection_system.file_manager.select_csv_file(filename)):
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'error'}), 404
    
    # Error Handlers
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
