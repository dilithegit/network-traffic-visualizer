"""
API Routes
Additional route definitions (currently handled in app.py)
This file is reserved for future API expansion
"""

from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

# Future API endpoints can be added here
# Example:
# @api.route('/detailed-stats', methods=['GET'])
# def detailed_stats():
#     # Implementation
#     pass
