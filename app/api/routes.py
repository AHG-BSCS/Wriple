"""Route handlers for the Human Presence Detection System"""

from flask import jsonify, request, render_template

from .validators import validate_recording_parameters


def create_api_routes(app, wriple_system):
    """Create and register all API routes with the Flask app"""
    
    # Set the detection_system instance object for usage reference
    from app.main import WripleSystem
    wriple_system: WripleSystem = wriple_system
    
    @app.route('/')
    def serve_index():
        """Serve the main HTML page"""
        return render_template('index.html')
    
    @app.route('/get_system_status', methods=['GET'])
    def get_system_status():
        """Get system component status"""
        status = wriple_system.get_system_status()
        return jsonify(status), 200
    
    @app.route('/get_monitor_status', methods=['GET'])
    def get_monitor_status():
        """Get monitoring information"""
        radar_status = wriple_system.get_monitor_status()
        return jsonify(radar_status), 200
    
    @app.route('/get_presence_status', methods=['GET'])
    def get_presence_status():
        """Get presence detection information"""
        pred = wriple_system.get_presence_status()
        return jsonify(pred), 200
    
    @app.route('/start_monitoring', methods=['POST'])
    def start_monitoring():
        """Start monitoring mode"""
        wriple_system.start_capturing(is_recording=False)
        return jsonify({'message': 'Monitoring started'}), 200
    
    @app.route('/start_recording', methods=['POST'])
    def start_recording():
        """Start recording mode with parameters"""
        params = request.get_json()
        
        if not validate_recording_parameters(params):
            return jsonify({'message': 'Invalid required field'}), 400
        
        wriple_system.set_recording_parameters(params)
        wriple_system.start_capturing(is_recording=True)
        return jsonify({'message': 'Recording started'}), 200
    
    @app.route('/stop_capturing', methods=['POST'])
    def stop_capturing():
        """Stop recording or monitoring"""
        wriple_system.stop_operations()
        return jsonify({'message': 'Stopped capturing'}), 200
    
    @app.route('/get_amplitude_data', methods=['GET'])
    def get_amplitude_data():
        """Get latest amplitude data subset"""
        latest_amplitudes = wriple_system.csi_processor.get_amps_heatmap_data()
        return jsonify({'latestAmplitudes': latest_amplitudes}), 200
    
    @app.route('/get_radar_data', methods=['GET'])
    def get_radar_data():
        """Get radar data and presence predictions"""
        radar_status = wriple_system.get_radar_status()
        return jsonify(radar_status), 200
    
    @app.route('/get_rdm_data', methods=['GET'])
    def get_rdm_data():
        filtered_rdm = wriple_system.rdm_processor.get_filtered_data()
        return jsonify({'filteredRdm': filtered_rdm}), 200
    
    @app.route('/get_signal_var', methods=['GET'])
    def get_signal_var():
        ampVariance = wriple_system.csi_processor.amplitude_variance
        return jsonify({'ampVariance': ampVariance}), 200
    
    # CSV File Management Routes
    
    @app.route('/get_csv_files', methods=['GET'])
    def get_csv_files():
        """List all recorded CSV files"""
        files = wriple_system.file_manager.list_csv_files()
        return jsonify(files), 200
    
    @app.route('/read_csv_file_meta', methods=['POST'])
    def read_csv_file_meta():
        """Read metadata of a selected CSV file"""
        filename = request.get_json()
        meta = wriple_system.file_manager.read_csv_file_meta(filename)

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
