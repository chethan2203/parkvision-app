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
                    'class': detector.class_names[cls] if cls < len(detector.class_names) else 'unknown',
                    'class_id': cls
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

if cv2_available and ParkingDetector:
    try:
        # Create a simple detector that works without custom model
        from ultralytics import YOLO
        import torch
        
        # Set PyTorch to allow unsafe loading for YOLOv8
        torch.serialization.add_safe_globals([
            'ultralytics.nn.tasks.DetectionModel',
            'ultralytics.nn.modules.head.Detect',
            'ultralytics.nn.modules.conv.Conv',
            'ultralytics.nn.modules.block.C2f'
        ])
        
        # Load YOLOv8n with unsafe loading allowed
        model = YOLO('yolov8n.pt')
        
        # Create a simple detector wrapper
        class SimpleDetector:
            def __init__(self, model):
                self.model = model
                self.class_names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck']
                
            def detect(self, image):
                return self.model(image, conf=0.5)[0]
                
            def count_spaces(self, results):
                counts = {'empty': 0, 'occupied': 0, 'total': 0}
                if results.boxes is not None:
                    for box in results.boxes:
                        cls = int(box.cls[0])
                        # Count cars, trucks, buses as occupied spaces
                        if cls in [2, 5, 7]:  # car, bus, truck
                            counts['occupied'] += 1
                            counts['total'] += 1
                return counts
        
        detector = SimpleDetector(model)
        model_loaded = True
        print("✅ Using YOLOv8n model for vehicle detection")
        
    except Exception as e:
        print(f"Warning: Could not load any model: {e}")
        detector = None
        model_loaded = False
else:
    print("⚠️ OpenCV or ParkingDetector not available")
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
