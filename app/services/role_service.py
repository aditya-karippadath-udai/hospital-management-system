from app.models.user import User


class RoleService:
    """Service for role-based operations"""
    
    @staticmethod
    def check_role(user, allowed_roles):
        """Check if user has one of the allowed roles"""
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]
        
        return user.role in allowed_roles
    
    @staticmethod
    def get_user_role(user_id):
        """Get user's role"""
        user = User.query.get(user_id)
        return user.role if user else None
    
    @staticmethod
    def get_role_profile(user):
        """Get role-specific profile for user"""
        if user.role == 'doctor':
            return user.doctor_profile
        elif user.role == 'patient':
            return user.patient_profile
        return None