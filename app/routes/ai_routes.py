from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
import requests
import os
import logging

ai_bp = Blueprint('ai', __name__)
logger = logging.getLogger(__name__)

AI_SERVICE_URL = os.getenv('AI_SERVICE_URL', 'http://ai-service:8000')

@ai_bp.route('/chatbot')
@login_required
def chatbot():
    """Render the AI Medical Assistant interface."""
    return render_template('ai/chatbot.html', title="AI Medical Assistant")

@ai_bp.route('/api/chat', methods=['POST'])
@login_required
def chat_proxy():
    """
    Proxy requests to the FastAPI AI microservice.
    Enforces role-based context and security tokens.
    """
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Missing query'}), 400

    # Prepare payload for AI Service
    # Note: In a real system, we would generate a short-lived JWT here
    # for the AI service to validate the user.
    payload = {
        "query": query,
        "role": current_user.role,
        "department": getattr(current_user, 'department', None),
        "sub": str(current_user.id)
    }

    try:
        # Mocking the AI Service call (would use requests/httpx in prod)
        # Using a dummy response for now if service is unavailable
        response = requests.post(
            f"{AI_SERVICE_URL}/v1/query",
            json=payload,
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_AI_TOKEN')}"},
            timeout=10
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            logger.error(f"AI Service error: {response.text}")
            return jsonify({'error': 'AI Service unavailable', 'details': response.text}), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"Connection to AI Service failed: {e}")
        return jsonify({
            'error': 'Connection failed',
            'response': 'I am currently having trouble connecting to my clinical knowledge base. Please check back shortly.'
        }), 503
