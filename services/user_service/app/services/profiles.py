from sqlalchemy.orm import Session
from app.models.profiles import StudentProfile, ParentProfile, Counsellor

def create_role_profile(db: Session, user_id: int, role: str, school_id: int = None, **profile_data):
    """
    Automatically creates a role-specific profile record for a new user.
    Accepts extra profile_data to populate fields like juniorcollege, college, etc.
    """
    if role == "STUDENT":
        # StudentProfile is now mapped to the 'student' table
        profile = StudentProfile(user_id=user_id, **profile_data)
        db.add(profile)
    elif role == "PARENT":
        profile = ParentProfile(user_id=user_id, **profile_data)
        db.add(profile)
    elif role == "COUNSELLOR":
        profile = Counsellor(user_id=user_id, **profile_data)
        db.add(profile)
    elif role == "SCHOOL":
        from app.models.user import School
        existing = db.query(School).filter(School.user_id == user_id).first()
        if not existing:
            profile = School(user_id=user_id, **profile_data)
            db.add(profile)
    
    # We don't commit here, as this is usually part of a larger transaction
    db.flush()
