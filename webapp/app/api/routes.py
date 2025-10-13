"""Route handlers for the Human Presence Detection System"""

from flask import jsonify, request, render_template
from .validators import validate_recording_parameters


def create_api_routes(app, detection_system):
    """Create and register all API routes with the Flask app"""
    
    # Set the detection_system instance object for usage reference
    from app.main import HumanDetectionSystem
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
        """Get monitoring information"""
        radar_status = detection_system.get_monitor_status()
        return jsonify(radar_status), 200
    
    @app.route('/get_presence_status', methods=['GET'])
    def get_presence_status():
        """Get presence detection information"""
        pred = detection_system.get_presence_status()
        return jsonify(pred), 200
    
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
            return jsonify({'message': 'Invalid required field'}), 400
        
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
        raw = detection_system.rdm_data[-1]
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
        # TODO: Visualize the phase using 3D plot
        latestPhases = detection_system.csi_processor._phase_queue[-1]
        return jsonify({'latestPhases': []}), 200
    
    # CSV File Management Routes
    
    @app.route('/get_csv_files', methods=['GET'])
    def get_csv_files():
        """List all recorded CSV files"""
        files = detection_system.file_manager.list_csv_files()
        return jsonify(files), 200
    
    @app.route('/read_csv_file_meta', methods=['POST'])
    def read_csv_file_meta():
        """Read metadata of a selected CSV file"""
        filename = request.get_json()
        meta = detection_system.file_manager.read_csv_file_meta(filename)

        if meta:
            return jsonify(meta), 200
        else:
            return jsonify({'message': 'File not found'}), 404
    
    # Error Handlers
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
