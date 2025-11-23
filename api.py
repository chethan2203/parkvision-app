"""
REST API for ParkVision
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import cv2
from src.detector import ParkingDetector
from config import get_config
import base64
import os

app = Flask(__name__)
app.config.from_object(get_config())
CORS(app)

# Initialize detector with error handling
try:
    detector = ParkingDetector(app.config['MODEL_PATH'])
    model_loaded = True
except Exception as e:
    print(f"Warning: Could not load model: {e}")
    detector = None
    model_loaded = False


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if model_loaded else 'model_error',
        'version': app.config.get('APP_VERSION', '1.0.0'),
        'model': app.config.get('MODEL_PATH', 'models/best.pt'),
        'model_loaded': model_loaded
    })


@app.route('/api/detect', methods=['POST'])
def detect():
    """
    Detect parking spaces in uploaded image
    
    Request:
        - image: base64 encoded image or multipart file
    
    Response:
        - empty: number of empty spaces
        - occupied: number of occupied spaces
        - total: total spaces detected
        - detections: list of detection details
    """
    try:
        if not model_loaded:
            return jsonify({'error': 'Model not loaded'}), 500
            
        # Get image from request
        if 'image' in request.files:
            file = request.files['image']
            image_bytes = file.read()
        elif 'image' in request.json:
            image_data = request.json['image']
            image_bytes = base64.b64decode(image_data)
        else:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode image
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Invalid image'}), 400
        
        # Run detection
        results = detector.detect(image)
        counts = detector.count_spaces(results)
        
        # Get detection details
        detections = []
        if results.boxes is not None:
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': conf,
                    'class': detector.class_names[cls],
                    'class_id': cls
                })
        
        return jsonify({
            'empty': counts['empty'],
            'occupied': counts['occupied'],
            'total': counts['total'],
            'detections': detections
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get current parking statistics"""
    # This would typically come from a database or cache
    # For now, return mock data
    return jsonify({
        'empty': 0,
        'occupied': 0,
        'total': 0,
        'availability': 0.0,
        'timestamp': None
    })


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get historical parking data"""
    # Query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 100, type=int)
    
    # This would query from database
    # For now, return empty list
    return jsonify({
        'data': [],
        'count': 0
    })


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
