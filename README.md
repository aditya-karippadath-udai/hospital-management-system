# Hospital Management System (HMS)

A robust, enterprise-grade Hospital Management System built with Flask, providing comprehensive workflows for Administrators, Doctors, and Patients.

## 🚀 Project Overview
HMS is designed to digitize hospital operations, from appointment scheduling and medical prescriptions to specialized resource management (Pharmacy, Beds, and Ambulances). It features a dual-authentication system supporting both traditional Web sessions and JWT-based API access.

## ✨ Key Features
- **Admin Dashboard**: Real-time hospital metrics, staff approvals, and resource lifecycle management.
- **Doctor Portal**: Appointment agenda management, digital prescriptions, and patient history access.
- **Patient Workspace**: Doctor discovery, appointment booking, and personal medical records.
- **Resource Management**: Inventory tracking for Pharmacy (with expiry alerts), Ward occupancy, and Ambulance fleet coordination.
- **Security**: Role-based access control (RBAC), password hashing, and secure JWT integration.

## 📂 Project Structure
```text
app/
├── models/          # SQLAlchemy Database Models
├── routes/          # Blueprint-based API/Web Routes
├── services/        # Business Logic / Service Layer
├── templates/       # Jinja2 HTML Templates (Subdivided by Role)
├── utils/           # Decorators, JWT utilities, and Seeds
└── extensions.py    # Flask Extension Initializations
migrations/          # Database Migration Scripts
```

## 🛠️ Installation & Setup

1. **Clone the repository**
2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Configuration**:
   Create a `.env` file with `DATABASE_URL` and `SECRET_KEY`.
5. **Database Initialization**:
   ```bash
   flask db upgrade
   python -m app.utils.seed  # To seed default admin and resources
   ```

## 🗄️ Database Schema
The system utilizes PostgreSQL with the following core entities:
- **Users**: Central identity management.
- **Doctors/Patients**: Role-specific profiles linked to Users.
- **Appointments**: Core interaction record between staff and patients.
- **Prescriptions**: Medical orders with JSON-based itemization.
- **Resources**: Beds, Medicines (Inventory), and Ambulances.

## 🛤️ Routes & Templates
| Module | Core Route | Primary Template |
|--------|------------|------------------|
| Auth | `/login` | `auth/login.html` |
| Admin | `/admin/dashboard` | `admin/admin_dashboard.html` |
| Doctor | `/doctor/dashboard` | `doctor/doctor_dashboard.html` |
| Patient | `/patient/dashboard` | `patient/patient_dashboard.html` |

## 🛡️ Error Handling
Custom error pages are implemented for:
- `403 Forbidden`: Role-based access denial.
- `404 Not Found`: Missing resources.
- `500 Server Error`: Unexpected backend failures.

## 🔮 Future Enhancements
- [ ] **Billing Module**: Automated invoice generation for consultations and medicines.
- [ ] **Lab Reports**: Integration for pathology and radiology results.
- [ ] **Telemedicine**: Video consultation integration via WebRTC.
- [ ] **Mobile App**: React Native or Flutter client using the existing JWT API.
