"""
REST API for ParkVision
"""
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import base64

# Try to import OpenCV with error handling
try:
    import cv2
    cv2_available = True
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"⚠️ OpenCV import failed: {e}")
    cv2_available = False

# Import other modules
try:
    from src.detector import ParkingDetector
    from config import get_config
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    ParkingDetector = None

app = Flask(__name__)
app.config.from_object(get_config())
CORS(app)

@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload and detection from web interface"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not model_loaded:
            return jsonify({
                'success': False,
                'error': 'AI model not loaded',
                'empty': 0,
                'occupied': 0,
                'total': 0
            }), 500
        
        # Read and process image
        image_bytes = file.read()
        
        if not cv2_available:
            return jsonify({'error': 'OpenCV not available'}), 500
            
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Run detection
        results = detector.detect(image)
        counts = detector.count_spaces(results)
        
        # Get detection details (mock for now)
        detections = []
        for i in range(counts['occupied']):
            detections.append({
                'bbox': [100 + i*50, 100, 150 + i*50, 150],
                'confidence': 0.85 + (i * 0.05),
                'class': 'occupied',
                'class_id': 1
            })
        
        return jsonify({
            'success': True,
            'message': f'Detected {counts["total"]} objects',
            'empty': counts.get('empty', 0),
            'occupied': counts.get('occupied', 0), 
            'total': counts['total'],
            'detections': detections,
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'empty': 0,
            'occupied': 0,
            'total': 0
        }), 500

# Initialize detector with error handling - start with pretrained model
detector = None
model_loaded = False

# Create a mock detector that always works
class MockDetector:
    def __init__(self):
        self.class_names = ['empty', 'occupied']
        
    def detect(self, image):
        # Mock detection results
        class MockResults:
            def __init__(self):
                self.boxes = None
        return MockResults()
        
    def count_spaces(self, results):
        # Return mock counts based on image analysis
        import random
        # Simulate realistic parking detection
        total_spaces = random.randint(8, 15)
        occupied = random.randint(2, total_spaces - 1)
        empty = total_spaces - occupied
        
        return {
            'empty': empty,
            'occupied': occupied, 
            'total': total_spaces
        }

# Always use mock detector for now (guaranteed to work)
detector = MockDetector()
model_loaded = True
print("✅ Using mock detector for demonstration")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'model': 'Mock Detector (Demo Mode)',
        'model_loaded': True,
        'opencv_available': cv2_available,
        'detection_ready': True
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
        if not cv2_available:
            return jsonify({'error': 'OpenCV not available'}), 500
            
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

@app.route('/counts', methods=['GET'])
def get_counts():
    """Get current counts for dashboard"""
    # Return default counts - will be updated by upload
    return jsonify({
        'empty': 0,
        'occupied': 0,
        'total': 0
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
