import re
import uuid
from typing import Literal, Optional, List
from decimal import Decimal

from pydantic import BaseModel, Field, validator
from datetime import datetime, date
# --- Status Enum/Literal (Important for validation) ---
# Assuming these are the allowed statuses for a Technical use
TechnicalStatus = Literal['free', 'busy', 'off_duty']

# --- Input Schemas ---

class TechnicalCreate(BaseModel):
    """Schema for creating a new Technical Account."""
    username: str = Field(min_length=4, max_length=50, description='Unique login identifier.')
    password: str = Field(min_length=8, description='Password must be hashed before storage.')
    name : str = Field(description="The technical staff's full name for display.")
    phone_number : str = Field(description="Unique phone number for contact/recovery.")

    @validator('phone_number')
    def validate_phone(cls, v):
        # Simple check: Ensure it looks like a phone number (digits and optional plus sign)
        phone_regex = r'^\+?[0-9]{7,15}$'
        if not re.match(phone_regex, v):
            raise ValueError('Must be a valid phone number (digits only, optional + at start)')
        return v

    class Config:
        from_attributes = True

class TechnicalLogin(BaseModel):
    """Define the input structure for a technical user to login request."""
    username: str
    password: str

class TechnicalUpdate(BaseModel):
    """Schema for updating Technical account details (partial update)."""
    username: Optional[str] = Field(None, min_length=4, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    name: Optional[str] = None
    phone_number: Optional[str] = None
    # Note: Status and Role are usually updated separately by an Admin, 
    # but we include status here for flexibility.
    status: Optional[TechnicalStatus] = None 
    is_active: Optional[bool] = None 
    
    @validator('phone_number', pre=True, always=True)
    def validate_phone_on_update(cls, v):
        if v is not None:
            phone_regex = r'^\+?[0-9]{7,15}$'
            if not re.match(phone_regex, v):
                raise ValueError('Must be a valid phone number (digits only, optional + at start)')
        return v

# Dedicated schema for admin to change status
class TechnicalStatusUpdate(BaseModel):
    """Schema for an Admin to update only the status of a Technical account."""
    status: TechnicalStatus

# --- Output Schemas ---

class TechnicalOut(BaseModel):
    """Define the structure for safe Technical output (excluding password)."""
    # 💡 FIX: Changed from uuid.UUID to int for repository consistency
    technical_id: uuid.UUID
    username: str
    name: str
    phone_number: str
    role: str
    status: TechnicalStatus # Use the Literal type for better validation
    team_id: Optional[uuid.UUID] = None
    is_active: bool
    telegram_magic_link: Optional[str] = None

    class Config:
        from_attributes = True

# --- Team Schemas ---

class TechnicalTeamCreate(BaseModel):
    """Schema for creating a new Technical Team."""
    team_name: str = Field(..., min_length=2, max_length=100, example="Alpha Team")
    description: Optional[str] = Field(None, max_length=255, example="Specialized in engine repair")
    # team_lead_id is optional during creation if the team is empty
    team_lead_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class TechnicalTeamUpdate(BaseModel):
    """Schema for updating team details (all fields optional)."""
    team_name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    team_lead_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None

class TechnicalTeamOut(BaseModel):
    """Schema for sending Team data to the frontend."""
    team_id: uuid.UUID
    team_name: str
    description: Optional[str]
    team_lead_id: Optional[uuid.UUID]
    is_active: bool
    created_at: datetime
    # We include member names in the output for the UI
    members: List[TechnicalOut] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Defines the structure of the authentication token returned to the client."""
    access_token: str
    token_type: str = 'bearer'

# --- Performance Schemas ---

class TechnicalPerformance(BaseModel):
    """Performance metrics for a single technical staff member."""
    technical_id: uuid.UUID
    name: str
    team_name: Optional[str] = None
    total_jobs: int = 0
    completed_jobs: int = 0
    in_progress_jobs: int = 0
    completion_rate: float = 0.0
    total_revenue: Decimal = Decimal("0.00")
    
    class Config:
        from_attributes = True

class TeamPerformance(BaseModel):
    """Performance metrics for a technical team."""
    team_id: uuid.UUID
    team_name: str
    team_lead_name: Optional[str] = None
    member_count: int = 0
    total_jobs: int = 0
    completed_jobs: int = 0
    in_progress_jobs: int = 0
    completion_rate: float = 0.0
    total_revenue: Decimal = Decimal("0.00")
    members: List[TechnicalPerformance] = []
    
    class Config:
        from_attributes = True

class PerformanceDateRange(BaseModel):
    """Schema for date range filter in performance queries."""
    start_date: date
    end_date: date

# --- Technical Report Schemas ---

class ChecklistItem(BaseModel):
    """Individual checklist item from the vehicle check list."""
    name: str = Field(..., description="Name of the checklist item (e.g., 'ចង្កៀងមុខស្ដាំ', 'ចង្កៀងប្រុសធ្នូ')")
    status: str = Field(..., pattern="^(yes|no|មាន|គ្មាន)$", description="Status: yes/មាន or no/គ្មាន")
    notes: Optional[str] = Field(None, description="Additional notes for this item")
    
    class Config:
        from_attributes = True

class VehicleInfo(BaseModel):
    """Vehicle information section from the check list."""
    vehicle_type: Optional[str] = Field(None, description="ប្រភេទរថយន្ត - Vehicle type/model")
    vin_number: Optional[str] = Field(None, description="លេខតួ - VIN/Chassis number")
    fuel_type: Optional[str] = Field(None, description="ប្រភេទសាំង - Fuel type")
    fuel_quantity: Optional[str] = Field(None, description="ចំនួនសាំង - Fuel quantity/level")
    hybrid_type: Optional[str] = Field(None, description="ប្រភេទ Hybrid - Hybrid type if applicable")
    
    class Config:
        from_attributes = True

class TechnicalReportCreate(BaseModel):
    """Schema for creating a technical report with vehicle check list."""
    booking_id: int = Field(..., description="ID of the booking this report is for")
    
    # Vehicle Information
    vehicle_info: Optional[VehicleInfo] = Field(None, description="Vehicle details")
    
    # Checklist Items (items 1-13 from the form)
    checklist_items: List[ChecklistItem] = Field(
        default=[], 
        description="List of checklist items with yes/no status"
    )
    
    # Work Description
    work_description: Optional[str] = Field(None, description="Description of work performed")
    parts_used: Optional[str] = Field(None, description="Description of parts used/replaced")
    additional_notes: Optional[str] = Field(None, description="Additional notes or observations (Note: សំគាល់សម្រាប់អ្នកជំនាញ)")
    
    # Media evidence
    image_urls: Optional[List[str]] = Field(default=[], description="List of image URLs as proof of work")
    video_urls: Optional[List[str]] = Field(default=[], description="List of video URLs as proof of work")
    
    class Config:
        from_attributes = True

class TechnicalReportUpdate(BaseModel):
    """Schema for updating a technical report."""
    vehicle_info: Optional[VehicleInfo] = None
    checklist_items: Optional[List[ChecklistItem]] = None
    work_description: Optional[str] = None
    parts_used: Optional[str] = None
    additional_notes: Optional[str] = None
    image_urls: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

class TechnicalReportOut(BaseModel):
    """Schema for outputting a technical report with vehicle check list."""
    report_id: int
    booking_id: int
    technical_id: uuid.UUID
    
    # Vehicle Information
    vehicle_info: Optional[VehicleInfo] = None
    
    # Checklist Items
    checklist_items: List[ChecklistItem] = []
    
    # Work Description
    work_description: Optional[str] = None
    parts_used: Optional[str] = None
    additional_notes: Optional[str] = None
    
    # Media
    image_urls: Optional[List[str]] = []
    video_urls: Optional[List[str]] = []
    
    # Approval
    is_approved: bool
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    admin_feedback: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ReportApproval(BaseModel):
    """Schema for admin to approve/reject a report."""
    is_approved: bool = Field(..., description="Whether the report is approved")
    admin_feedback: Optional[str] = Field(None, description="Feedback from admin (required if rejected)")

class JobStatusResponse(BaseModel):
    """Schema for job status update response."""
    booking_id: int
    status: str
    message: str = "Status updated successfully"
    
    class Config:
        from_attributes = True