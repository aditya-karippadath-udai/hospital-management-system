from flask import Blueprint, jsonify, render_template, request, session, abort, flash, redirect, url_for
from datetime import datetime
from flask_login import current_user, login_required
from app.services.admin_service import AdminService
from app.models.user import User
from app.models.doctor import Doctor
from app.models.resource import Bed, Medicine, Ambulance
from app.extensions import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Enhanced Admin Dashboard"""
    if current_user.role != 'admin': abort(403)
        
    stats = AdminService.get_dashboard_stats()
    try:
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    except Exception:
        db.session.rollback()
        recent_users = []
    
    if request.path.startswith('/api') or request.is_json:
        return jsonify({
            'statistics': stats,
            'recent_users': [u.to_dict() for u in recent_users]
        }), 200
        
    return render_template('admin/admin_dashboard.html', stats=stats, recent_users=recent_users)

@admin_bp.route('/beds', methods=['GET', 'POST'])
@login_required
def manage_beds():
    if current_user.role != 'admin': abort(403)
    
    if request.method == 'POST':
        # Detect if JSON or Form
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'bed_number': request.form.get('bed_number'),
                'ward': request.form.get('ward')
            }
            
        try:
            bed = AdminService.create_bed(data)
            if request.is_json:
                return jsonify({'message': 'Bed added', 'bed': bed.to_dict()}), 201
            flash('Bed added successfully', 'success')
            return redirect(url_for('admin.manage_beds'))
        except Exception as e:
            if request.is_json: return jsonify({'error': str(e)}), 400
            flash(f'Error adding bed: {str(e)}', 'danger')

    beds = Bed.query.all()
    if request.is_json: return jsonify({'beds': [b.to_dict() for b in beds]}), 200
    return render_template('admin/manage_beds.html', beds=beds)

@admin_bp.route('/beds/<int:bed_id>/toggle', methods=['POST'])
@login_required
def toggle_bed_status(bed_id):
    if current_user.role != 'admin': abort(403)
    try:
        AdminService.update_bed(bed_id, {'is_occupied': not Bed.query.get(bed_id).is_occupied})
        flash(f'Bed status updated', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_beds'))

@admin_bp.route('/beds/<int:bed_id>/delete', methods=['POST'])
@login_required
def delete_bed(bed_id):
    if current_user.role != 'admin': abort(403)
    try:
        AdminService.delete_bed(bed_id)
        flash('Bed removed', 'info')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_beds'))

@admin_bp.route('/medicines', methods=['GET', 'POST'])
@login_required
def manage_medicines():
    if current_user.role != 'admin': abort(403)
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'name': request.form.get('name'),
                'stock_quantity': int(request.form.get('stock_quantity', 0)),
                'price': float(request.form.get('price', 0))
            }
            
        try:
            # Safe date parsing
            expiry_date = None
            date_str = request.form.get('expiry_date')
            if date_str:
                try:
                    expiry_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    flash('Invalid date format. Please use YYYY-MM-DD.', 'warning')
                    return redirect(url_for('admin.manage_medicines'))

            data['expiry_date'] = expiry_date
            AdminService.create_medicine(data)
            if request.is_json: return jsonify({'message': 'Medicine added'}), 201
            flash('Medicine added to inventory', 'success')
            return redirect(url_for('admin.manage_medicines'))
        except Exception as e:
            flash(f'Error adding medicine: {str(e)}', 'danger')

    medicines = Medicine.query.all()
    if request.is_json: return jsonify({'medicines': [m.to_dict() for m in medicines]}), 200
    return render_template('admin/manage_medicines.html', medicines=medicines)

@admin_bp.route('/medicines/<int:medicine_id>/delete', methods=['POST'])
@login_required
def delete_medicine(medicine_id):
    if current_user.role != 'admin': abort(403)
    med = Medicine.query.get_or_404(medicine_id)
    db.session.delete(med)
    db.session.commit()
    flash('Medicine removed', 'info')
    return redirect(url_for('admin.manage_medicines'))

@admin_bp.route('/ambulances', methods=['GET', 'POST'])
@login_required
def manage_ambulances():
    if current_user.role != 'admin': abort(403)
    
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = {
                'vehicle_number': request.form.get('vehicle_number'),
                'driver_name': request.form.get('driver_name')
            }
        try:
            AdminService.create_ambulance(data)
            flash('Ambulance registered', 'success')
            return redirect(url_for('admin.manage_ambulances'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')

    ambulances = Ambulance.query.all()
    return render_template('admin/manage_ambulances.html', ambulances=ambulances)

@admin_bp.route('/ambulances/<int:ambulance_id>/toggle', methods=['POST'])
@login_required
def toggle_ambulance_status(ambulance_id):
    if current_user.role != 'admin': abort(403)
    try:
        amb = Ambulance.query.get_or_404(ambulance_id)
        AdminService.update_ambulance(ambulance_id, {'is_available': not amb.is_available})
        flash(f'Ambulance {amb.vehicle_number} status updated', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_ambulances'))

@admin_bp.route('/ambulances/<int:ambulance_id>/delete', methods=['POST'])
@login_required
def delete_ambulance(ambulance_id):
    if current_user.role != 'admin': abort(403)
    try:
        AdminService.delete_ambulance(ambulance_id)
        flash('Ambulance removed', 'info')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.manage_ambulances'))

@admin_bp.route('/doctors', methods=['GET'])
@login_required
def list_doctors():
    if current_user.role != 'admin': abort(403)
    doctors = Doctor.query.all()
    if request.is_json: return jsonify({'doctors': [d.to_dict() for d in doctors]}), 200
    return render_template('admin/doctor_approvals.html', doctors=doctors)

@admin_bp.route('/doctors/<int:doctor_id>/approve', methods=['POST'])
@login_required
def approve_doctor(doctor_id):
    if current_user.role != 'admin': abort(403)
    try:
        AdminService.approve_doctor(doctor_id)
        flash('Doctor approved', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.list_doctors'))

@admin_bp.route('/doctors/<int:doctor_id>/deapprove', methods=['POST'])
@login_required
def deapprove_doctor(doctor_id):
    if current_user.role != 'admin': abort(403)
    try:
        AdminService.deapprove_doctor(doctor_id)
        flash('Doctor deactivated', 'warning')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.list_doctors'))

@admin_bp.route('/users')
@login_required
def list_users():
    if current_user.role != 'admin': abort(403)
    users = User.query.all()
    if request.is_json: return jsonify({'users': [u.to_dict() for u in users]}), 200
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.role != 'admin': abort(403)
    if user_id == current_user.id:
        flash('You cannot deactivate yourself!', 'danger')
        return redirect(url_for('admin.list_users'))
    
    try:
        user = User.query.get_or_404(user_id)
        AdminService.toggle_user_status(user_id, not user.is_active)
        status = "toggled"
        flash(f'User status updated', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.list_users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin': abort(403)
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete yourself!', 'danger')
        return redirect(url_for('admin.list_users'))
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('admin.list_users'))