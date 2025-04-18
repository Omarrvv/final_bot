from flask import render_template
from src.utils.auth import admin_required
from flask_login import login_required
from flask_admin import Admin

admin_routes = Admin()

@admin_routes.route('/analytics', methods=['GET'])
@login_required
@admin_required
def analytics_dashboard():
    """
    Render the analytics dashboard.
    
    Returns:
        Rendered analytics dashboard template
    """
    return render_template('admin/analytics.html') 
