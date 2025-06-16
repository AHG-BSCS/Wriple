"""Route handlers for the human detection system"""

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
            signal_coordinates = detection_system.csi_processor.filter_amp_phase()
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
            files = detection_system.data_recorder.list_csv_files()
            return jsonify(files)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/visualize_csv_file/<filename>', methods=['GET'])
    def visualize_csv_file(filename):
        """Set a CSV file for visualization"""
        try:
            from core.data_recorder import CSVVisualizer
            
            visualizer = CSVVisualizer(detection_system.data_recorder)
            visualizer.set_visualization_file(filename)
            
            # Set recording packet limit for visualization
            from config.settings import RecordingConfiguration
            detection_system.csi_processor.set_max_packets(
                RecordingConfiguration.RECORD_PACKET_LIMIT
            )
            
            return jsonify({'status': 'CSV file set for visualization'})
            
        except FileNotFoundError:
            return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/load_csv_visualization', methods=['POST'])
    def load_csv_visualization():
        """Load and process CSV data for visualization"""
        try:
            data = request.get_json()
            filename = data.get('filename')
            
            if not filename:
                return jsonify({'error': 'Filename required'}), 400
            
            from core.data_recorder import CSVVisualizer
            
            visualizer = CSVVisualizer(detection_system.data_recorder)
            visualizer.set_visualization_file(filename)
            
            # Process the CSV data
            signal_coordinates = visualizer.get_csi_data_for_processing(
                detection_system.csi_processor
            )
            
            return jsonify({'signalCoordinates': signal_coordinates})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Error Handlers
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500