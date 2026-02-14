from app.extensions import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.resource import Bed, Medicine, Ambulance
from sqlalchemy import func

class AdminService:
    @staticmethod
    def get_dashboard_stats():
        """Aggregate stats for admin dashboard with safety for missing tables"""
        stats = {
            'total_users': 0,
            'total_doctors': 0,
            'total_patients': 0,
            'total_appointments': 0,
            'pending_appointments': 0,
            'total_beds': 0,
            'available_beds': 0,
            'total_medicines': 0,
            'medicine_stock_sum': 0,
            'low_stock_medicines': 0,
            'total_ambulances': 0,
            'available_ambulances': 0,
            'pending_doctor_approvals': 0
        }
        
        try:
            stats['total_users'] = User.query.count()
            stats['total_doctors'] = Doctor.query.count()
            stats['total_patients'] = Patient.query.count()
            stats['total_appointments'] = Appointment.query.count()
            stats['pending_appointments'] = Appointment.query.filter_by(status='pending').count()
            stats['pending_doctor_approvals'] = User.query.filter_by(role='doctor', is_active=False).count()
        except Exception as e:
            print(f"DEBUG: Core user/appointment tables error: {e}")

        try:
            stats['total_beds'] = Bed.query.count()
            stats['available_beds'] = Bed.query.filter_by(is_occupied=False).count()
        except Exception as e:
            print(f"DEBUG: Beds table error: {e}")

        try:
            stats['total_medicines'] = Medicine.query.count()
            stats['medicine_stock_sum'] = db.session.query(func.sum(Medicine.stock_quantity)).scalar() or 0
            stats['low_stock_medicines'] = Medicine.query.filter(Medicine.stock_quantity < 10).count()
        except Exception as e:
            print(f"DEBUG: Medicines table error: {e}")

        try:
            stats['total_ambulances'] = Ambulance.query.count()
            stats['available_ambulances'] = Ambulance.query.filter_by(is_available=True).count()
        except Exception as e:
            print(f"DEBUG: Ambulances table error: {e}")
            
        return stats

    # Bed Management
    @staticmethod
    def create_bed(data):
        try:
            bed = Bed(bed_number=data['bed_number'], ward=data['ward'])
            db.session.add(bed)
            db.session.commit()
            return bed
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_bed(bed_id, data):
        try:
            bed = Bed.query.get(bed_id)
            if bed:
                bed.bed_number = data.get('bed_number', bed.bed_number)
                bed.ward = data.get('ward', bed.ward)
                bed.is_occupied = data.get('is_occupied', bed.is_occupied)
                db.session.commit()
                return bed
            return None
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_bed(bed_id):
        try:
            bed = Bed.query.get(bed_id)
            if bed:
                db.session.delete(bed)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    # Medicine Management
    @staticmethod
    def create_medicine(data):
        try:
            medicine = Medicine(
                name=data['name'], 
                stock_quantity=data.get('stock_quantity', 0), 
                price=data.get('price', 0.0),
                expiry_date=data.get('expiry_date')
            )
            db.session.add(medicine)
            db.session.commit()
            return medicine
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_medicine(medicine_id, data):
        try:
            medicine = Medicine.query.get(medicine_id)
            if medicine:
                medicine.name = data.get('name', medicine.name)
                medicine.stock_quantity = data.get('stock_quantity', medicine.stock_quantity)
                medicine.price = data.get('price', medicine.price)
                medicine.expiry_date = data.get('expiry_date', medicine.expiry_date)
                db.session.commit()
                return medicine
            return None
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_medicine(medicine_id):
        try:
            medicine = Medicine.query.get(medicine_id)
            if medicine:
                db.session.delete(medicine)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    # Ambulance Management
    @staticmethod
    def create_ambulance(data):
        try:
            ambulance = Ambulance(
                vehicle_number=data['vehicle_number'], 
                driver_name=data.get('driver_name')
            )
            db.session.add(ambulance)
            db.session.commit()
            return ambulance
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def update_ambulance(ambulance_id, data):
        try:
            ambulance = Ambulance.query.get(ambulance_id)
            if ambulance:
                ambulance.vehicle_number = data.get('vehicle_number', ambulance.vehicle_number)
                ambulance.driver_name = data.get('driver_name', ambulance.driver_name)
                ambulance.is_available = data.get('is_available', ambulance.is_available)
                db.session.commit()
                return ambulance
            return None
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def delete_ambulance(ambulance_id):
        try:
            ambulance = Ambulance.query.get(ambulance_id)
            if ambulance:
                db.session.delete(ambulance)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    # Doctor Approval & User Management
    @staticmethod
    def approve_doctor(doctor_id):
        try:
            doctor = Doctor.query.get(doctor_id)
            if doctor and doctor.user:
                doctor.user.is_active = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def deapprove_doctor(doctor_id):
        try:
            doctor = Doctor.query.get(doctor_id)
            if doctor and doctor.user:
                doctor.user.is_active = False
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def toggle_user_status(user_id, active):
        """Enable or disable any user account"""
        try:
            user = User.query.get(user_id)
            if user:
                user.is_active = active
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e
