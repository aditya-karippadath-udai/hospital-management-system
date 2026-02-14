from app.extensions import db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.resource import Bed, Medicine, Ambulance

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
            stats['low_stock_medicines'] = Medicine.query.filter(Medicine.stock_quantity < 10).count()
        except Exception as e:
            print(f"DEBUG: Medicines table error: {e}")

        try:
            stats['total_ambulances'] = Ambulance.query.count()
            stats['available_ambulances'] = Ambulance.query.filter_by(is_available=True).count()
        except Exception as e:
            print(f"DEBUG: Ambulances table error: {e}")
            
        return stats

    @staticmethod
    def create_bed(data):
        bed = Bed(bed_number=data['bed_number'], ward=data['ward'])
        db.session.add(bed)
        db.session.commit()
        return bed

    @staticmethod
    def create_medicine(data):
        medicine = Medicine(
            name=data['name'], 
            stock_quantity=data.get('stock_quantity', 0), 
            price=data.get('price', 0.0)
        )
        db.session.add(medicine)
        db.session.commit()
        return medicine

    @staticmethod
    def create_ambulance(data):
        ambulance = Ambulance(
            vehicle_number=data['vehicle_number'], 
            driver_name=data.get('driver_name')
        )
        db.session.add(ambulance)
        db.session.commit()
        return ambulance

    @staticmethod
    def approve_doctor(doctor_id):
        """Approve doctor registration"""
        doctor = Doctor.query.get(doctor_id)
        if doctor and doctor.user:
            doctor.user.is_active = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def deapprove_doctor(doctor_id):
        """Deactivate doctor account"""
        doctor = Doctor.query.get(doctor_id)
        if doctor and doctor.user:
            doctor.user.is_active = False
            db.session.commit()
            return True
        return False
