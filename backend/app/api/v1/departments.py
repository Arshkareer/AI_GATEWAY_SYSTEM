from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_current_active_user, get_admin_user, get_db, require_permission
from app.core.exceptions import ValidationException, ResourceNotFoundException
from app.models.user import User
from app.models.department import Department
from app.schemas.analytics import DepartmentStats

router = APIRouter()


# Department schemas (defined inline since we don't have a separate file)
from pydantic import BaseModel

class DepartmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    monthly_budget: float = 0.0
    budget_alert_threshold: float = 0.8
    auto_budget_alerts: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    monthly_budget: Optional[float] = None
    budget_alert_threshold: Optional[float] = None
    auto_budget_alerts: Optional[bool] = None
    is_active: Optional[bool] = None

class DepartmentResponse(DepartmentBase):
    id: int
    is_active: bool
    user_count: int = 0
    total_requests: int
    total_cost: float
    current_month_cost: float
    budget_utilization: float
    remaining_budget: float
    
    class Config:
        orm_mode = True


@router.get("/", response_model=List[DepartmentResponse])
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List departments with filtering and pagination."""
    
    query = db.query(Department)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(Department.name.ilike(search_term))
    
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)
    
    # Get departments with pagination
    departments = query.offset(skip).limit(limit).all()
    
    # Add user count for each department
    result = []
    for dept in departments:
        dept_dict = dept.__dict__.copy()
        user_count = db.query(User).filter(User.department_id == dept.id).count()
        dept_dict['user_count'] = user_count
        result.append(DepartmentResponse(**dept_dict))
    
    return result


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific department by ID."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    # Add user count
    user_count = db.query(User).filter(User.department_id == department.id).count()
    dept_dict = department.__dict__.copy()
    dept_dict['user_count'] = user_count
    
    return DepartmentResponse(**dept_dict)


@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(require_permission("write:departments")),
    db: Session = Depends(get_db)
):
    """Create a new department (admin only)."""
    
    # Check if department name already exists
    existing_dept = db.query(Department).filter(Department.name == department_data.name).first()
    if existing_dept:
        raise ValidationException("Department name already exists")
    
    # Create new department
    new_department = Department(
        name=department_data.name,
        description=department_data.description,
        monthly_budget=department_data.monthly_budget,
        budget_alert_threshold=department_data.budget_alert_threshold,
        auto_budget_alerts=department_data.auto_budget_alerts,
        is_active=True
    )
    
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    
    # Add user count (will be 0 for new department)
    dept_dict = new_department.__dict__.copy()
    dept_dict['user_count'] = 0
    
    return DepartmentResponse(**dept_dict)


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    current_user: User = Depends(require_permission("write:departments")),
    db: Session = Depends(get_db)
):
    """Update department (admin only)."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    update_data = department_update.dict(exclude_unset=True)
    
    # Check for duplicate name
    if "name" in update_data:
        existing = db.query(Department).filter(
            Department.name == update_data["name"],
            Department.id != department_id
        ).first()
        if existing:
            raise ValidationException("Department name already exists")
    
    # Update department
    for field, value in update_data.items():
        setattr(department, field, value)
    
    db.commit()
    db.refresh(department)
    
    # Add user count
    user_count = db.query(User).filter(User.department_id == department.id).count()
    dept_dict = department.__dict__.copy()
    dept_dict['user_count'] = user_count
    
    return DepartmentResponse(**dept_dict)


@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    current_user: User = Depends(require_permission("delete:departments")),
    db: Session = Depends(get_db)
):
    """Delete department (admin only)."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    # Check if department has users
    user_count = db.query(User).filter(User.department_id == department_id).count()
    if user_count > 0:
        raise ValidationException(f"Cannot delete department with {user_count} users. Move users first.")
    
    # Soft delete - just deactivate the department
    department.is_active = False
    db.commit()
    
    return {"message": f"Department {department.name} has been deactivated"}


@router.get("/{department_id}/users", response_model=List[dict])
async def get_department_users(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all users in a department."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    users = db.query(User).filter(User.department_id == department_id).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "total_requests": user.total_requests,
            "total_cost": user.total_cost
        }
        for user in users
    ]


@router.get("/{department_id}/stats", response_model=DepartmentStats)
async def get_department_stats(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get department usage statistics."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    # Get users in department
    users = db.query(User).filter(User.department_id == department_id).all()
    user_count = len(users)
    
    # TODO: Calculate real statistics from request logs
    # This will be implemented when we have the analytics engine
    
    return DepartmentStats(
        department_id=department.id,
        department_name=department.name,
        user_count=user_count,
        stats={
            "total_requests": department.total_requests,
            "successful_requests": department.total_requests,  # Placeholder
            "failed_requests": 0,  # Placeholder
            "total_tokens": 0,  # Placeholder
            "prompt_tokens": 0,  # Placeholder
            "completion_tokens": 0,  # Placeholder
            "total_cost": department.total_cost,
            "avg_latency_ms": 1200.0,  # Placeholder
            "success_rate": 98.5,  # Placeholder
            "avg_cost_per_request": 0.0,  # Placeholder
            "avg_tokens_per_request": 0.0,  # Placeholder
            "cost_per_1k_tokens": 0.0  # Placeholder
        },
        monthly_budget=department.monthly_budget,
        budget_utilization=department.budget_utilization,
        remaining_budget=department.remaining_budget,
        is_over_budget=department.is_over_budget,
        top_users=[],  # Placeholder
        usage_by_model=[]  # Placeholder
    )


@router.post("/{department_id}/users/{user_id}/assign")
async def assign_user_to_department(
    department_id: int,
    user_id: int,
    current_user: User = Depends(require_permission("write:departments")),
    db: Session = Depends(get_db)
):
    """Assign user to department."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found")
    
    user.department_id = department_id
    db.commit()
    
    return {"message": f"User {user.username} assigned to department {department.name}"}


@router.delete("/{department_id}/users/{user_id}")
async def remove_user_from_department(
    department_id: int,
    user_id: int,
    current_user: User = Depends(require_permission("write:departments")),
    db: Session = Depends(get_db)
):
    """Remove user from department."""
    
    user = db.query(User).filter(
        User.id == user_id, 
        User.department_id == department_id
    ).first()
    
    if not user:
        raise ResourceNotFoundException(f"User with ID {user_id} not found in department {department_id}")
    
    user.department_id = None
    db.commit()
    
    return {"message": f"User {user.username} removed from department"}


@router.get("/{department_id}/budget")
async def get_department_budget_info(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get department budget information."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    return {
        "department_id": department.id,
        "department_name": department.name,
        "monthly_budget": department.monthly_budget,
        "current_month_cost": department.current_month_cost,
        "budget_utilization": department.budget_utilization,
        "remaining_budget": department.remaining_budget,
        "is_over_budget": department.is_over_budget,
        "budget_alert_threshold": department.budget_alert_threshold,
        "auto_budget_alerts": department.auto_budget_alerts
    }


@router.put("/{department_id}/budget")
async def update_department_budget(
    department_id: int,
    monthly_budget: float,
    budget_alert_threshold: Optional[float] = None,
    current_user: User = Depends(require_permission("write:departments")),
    db: Session = Depends(get_db)
):
    """Update department budget."""
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise ResourceNotFoundException(f"Department with ID {department_id} not found")
    
    department.monthly_budget = monthly_budget
    
    if budget_alert_threshold is not None:
        if not 0.0 <= budget_alert_threshold <= 1.0:
            raise ValidationException("Budget alert threshold must be between 0.0 and 1.0")
        department.budget_alert_threshold = budget_alert_threshold
    
    db.commit()
    
    return {"message": f"Budget updated for department {department.name}"}