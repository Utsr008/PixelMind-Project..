from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import base64
import os
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)
CORS(app)

COLAB_BACKEND_URL = 'https://1cfcd564d39b.ngrok-free.app'


NGROK_HEADERS = {
    'ngrok-skip-browser-warning': 'true',
    'User-Agent': 'Mozilla/5.0'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.json
        
        payload = {
            'model': data.get('model'),
            'lora': data.get('lora'),
            'prompt': data.get('prompt'),
            'seed': data.get('seed', 0)
        }
        
        print(f"Sending request to: {COLAB_BACKEND_URL}/generate")
        print(f"Payload: {payload}")
        
        response = requests.post(
            f'{COLAB_BACKEND_URL}/generate',
            json=payload,
            headers=NGROK_HEADERS,
            timeout=360,  
            verify=False 
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'image': result['image'],
                'seed': result.get('seed', data.get('seed'))
            })
        else:
            error_msg = f'Backend error: {response.status_code}'
            try:
                error_detail = response.json()
                error_msg += f' - {error_detail}'
            except:
                error_msg += f' - {response.text[:200]}'
            
            print(f"Error: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 500
            
    except requests.exceptions.Timeout:
        print("Error: Request timeout")
        return jsonify({
            'success': False,
            'error': 'Request timeout - generation took too long (>3 min)'
        }), 504
    except requests.exceptions.ConnectionError as e:
        print(f"Error: Connection failed - {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Cannot connect to Colab backend. Make sure it is running and URL is correct. Current URL: {COLAB_BACKEND_URL}'
        }), 503
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        
        response = requests.get(
            f'{COLAB_BACKEND_URL}/health', 
            headers=NGROK_HEADERS,
            timeout=10,
            verify=False 
        )
        backend_status = response.status_code == 200
        backend_info = response.json() if backend_status else None
        print(f"Backend health check: {backend_status}")
        if backend_info:
            print(f"Backend info: {backend_info}")
    except Exception as e:
        print(f"Backend health check failed: {str(e)}")
        backend_status = False
        backend_info = None
    
    return jsonify({
        'status': 'healthy',
        'backend_connected': backend_status,
        'backend_url': COLAB_BACKEND_URL,
        'backend_info': backend_info
    })

@app.route('/update-backend-url', methods=['POST'])
def update_backend_url():
    """Endpoint to update backend URL without restarting"""
    global COLAB_BACKEND_URL
    data = request.json
    new_url = data.get('url', '').strip()
    
    if not new_url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    new_url = new_url.rstrip('/')
    
    COLAB_BACKEND_URL = new_url
    
    print(f"\n{'='*50}")
    print(f"🔄 Backend URL updated to: {COLAB_BACKEND_URL}")
    print(f"{'='*50}\n")
    
    return jsonify({
        'success': True,
        'backend_url': COLAB_BACKEND_URL
    })

if __name__ == '__main__':
    
    os.makedirs('templates', exist_ok=True)
    
    print("\n" + "="*50)
    print("🎨 AI Image Generator Server")
    print("="*50)
    print(f"\n📡 Server running on: http://localhost:5000")
    print(f"🔗 Colab backend URL: {COLAB_BACKEND_URL}")
    print(f"\n💡 Tip: Visit http://localhost:5000/health to check backend connection")
    print(f"💡 Tip: Update URL without restart: POST to /update-backend-url")
    print("\n" + "="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)