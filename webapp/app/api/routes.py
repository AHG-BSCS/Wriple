"""Route handlers for the Human Presence Detection System"""

from flask import jsonify, request, render_template
from .validators import validate_recording_parameters, validate_target_count
from config.settings import VisualizerConfiguration as config


def create_api_routes(app, detection_system):
    """Create and register all API routes with the Flask app"""
    
    @app.route('/')
    def serve_index():
        """Serve the main HTML page"""
        return render_template('index.html')
    
    @app.route('/check_system_status', methods=['POST'])
    def check_system_status():
        """Get system component status"""
        try:
            status = detection_system.get_system_status()
            return jsonify(status)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/start_recording/<mode>', methods=['GET'])
    def start_recording(mode):
        """Start recording or monitoring mode"""
        if mode == 'recording':
            detection_system.start_recording_mode()
        elif mode == 'monitoring':
            detection_system.start_monitoring_mode()
        else:
            return jsonify({'status': 'error',
                            'error': 'Invalid mode'}), 400
        
        return jsonify({'status': 'success'})
    
    @app.route('/stop_recording', methods=['POST'])
    def stop_recording():
        """Stop recording or monitoring"""
        try:
            detection_system.stop_operations()
            return jsonify({'status': 'stopped'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/set_record_parameter', methods=['POST'])
    def set_record_parameter():
        """Set parameters for recording session"""
        data = request.get_json()
        
        if not validate_recording_parameters(data):
            return jsonify({'status': 'error'}), 400
        
        data = validate_target_count(data)
        detection_system.set_recording_parameters(data)
        return jsonify({'status': 'success'})
    
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
    
    @app.route('/fetch_amplitude_data', methods=['POST'])
    def fetch_amplitude_data():
        """Get latest amplitude data subset"""
        try:
            amplitude_points = detection_system.csi_processor.get_latest_amplitude(
                config.AMP_HEATMAP_START, config.AMP_HEATMAP_END)
            return jsonify({'latestAmplitude': amplitude_points})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/fetch_phase_data', methods=['POST'])
    def fetch_phase_data():
        """Get latest phase data subset"""
        try:
            phase_points = detection_system.csi_processor.get_latest_phase(
                config.PHASE_HEATMAP_START, config.PHASE_HEATMAP_END)
            return jsonify({'latestPhase': phase_points})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # CSV File Management Routes
    
    @app.route('/list_csv_files', methods=['GET'])
    def list_csv_files():
        """List all recorded CSV files"""
        try:
            files = detection_system.file_manager.list_csv_files()
            return jsonify(files)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/visualize_csv_file/<filename>', methods=['GET'])
    def select_csv_file(filename):
        """Set a CSV file for visualization"""
        if (detection_system.file_manager.select_csv_file(filename)):
            detection_system.csi_processor.set_max_packets = detection_system.record_packet_limit
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