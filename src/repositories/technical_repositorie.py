from typing import List, Optional, Union
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.models.technical_model import (  # Assuming AdminUpdate exists
    TechnicalCreate, TechnicalUpdate, TechnicalPerformance, TeamPerformance,
    TechnicalReportCreate, TechnicalReportUpdate)
from src.schemas.techincal import TechnicalModel
from src.schemas.techincal import TechnicalTeam  # Import your Team model
from src.models.technical_model import TechnicalTeamCreate, TechnicalTeamUpdate # Import schemas
from src.schemas.booking import Booking, TechnicalReport
from src.core.enums import BookingStatus
import json

class TechnicalRepository:
    """Implements the data access logic for the Technical entity."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique ID."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()

    def get_by_id(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Alias for get() to match common patterns."""
        return self.get(technical_id)

    def get_by_username(self, username: str) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique username."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.username == username).first()

    def get_by_phone_number(self, phone_number: str) -> Optional[TechnicalModel]:
        """Retrieves a Technical account by its unique phone number."""
        return self.db.query(TechnicalModel).filter(TechnicalModel.phone_number == phone_number).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[TechnicalModel]:
        """Get multiple technical accounts with pagination."""
        return self.db.query(TechnicalModel).offset(skip).limit(limit).all()

    def create(self, tech_in: TechnicalCreate, hashed_password: str) -> TechnicalModel:
        """Creates a new Technical account."""
        try:
            db_tech = TechnicalModel(
                username=tech_in.username,
                password=hashed_password,
                phone_number=tech_in.phone_number,
                name=tech_in.name,
                # Role and status defaults are assumed to be handled by the model
            )
            self.db.add(db_tech)
            self.db.commit()
            self.db.refresh(db_tech)
            return db_tech
        except IntegrityError as e:
            self.db.rollback()
            # Re-raise or handle the integrity error (e.g., duplicate key)
            raise e

    def update(self, db_obj: TechnicalModel, obj_in: Union[TechnicalUpdate, dict]) -> TechnicalModel:
        """Update an existing technical account record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Delete a technical account by ID."""
        obj = self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
    
    def get_staff_by_name(self, name: str) -> List[TechnicalModel]:
        """Finds staff by name for human-friendly selection."""
        return self.db.query(TechnicalModel).filter(
            TechnicalModel.name.ilike(f"%{name}%")
        ).all()

    # --- TECHNICAL TEAM CRUD ---

    def get_team_by_name(self, team_name: str) -> Optional[TechnicalTeam]:
        """Finds an exact team by name (useful for direct assignment)."""
        return self.db.query(TechnicalTeam).filter(
            TechnicalTeam.team_name.ilike(team_name)
        ).first()

    def create_team(self, team_in: TechnicalTeamCreate) -> TechnicalTeam:
        """Creates a new technical team."""
        db_team = TechnicalTeam(
            team_name=team_in.team_name,
            description=team_in.description,
            team_lead_id=team_in.team_lead_id
        )
        try:
            self.db.add(db_team)
            self.db.commit()
            self.db.refresh(db_team)
            return db_team
        except IntegrityError as e:
            self.db.rollback()
            raise e

    def search_teams_by_name(self, name_substr: str) -> List[TechnicalTeam]:
        """Searches for teams with names containing the given substring."""
        return self.db.query(TechnicalTeam).filter(TechnicalTeam.team_name.ilike(f"%{name_substr}%")).all()

    def get_team(self, team_id: uuid.UUID) -> Optional[TechnicalTeam]:
        """Retrieves a team by its UUID."""
        # Note: Changed from .get(id) to a filter because team_id is a UUID
        return self.db.query(TechnicalTeam).filter(TechnicalTeam.team_id == team_id).first()

    def get_all_teams(self, skip: int = 0, limit: int = 100) -> List[TechnicalTeam]:
        """Lists all teams with optional pagination."""
        return self.db.query(TechnicalTeam).offset(skip).limit(limit).all()

    def update_team(self, db_team: TechnicalTeam, obj_in: Union[TechnicalTeamUpdate, dict]) -> TechnicalTeam:
        """Updates team details like name, description, or team lead."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for key, value in update_data.items():
            if hasattr(db_team, key):
                setattr(db_team, key, value)

        self.db.add(db_team)
        self.db.commit()
        self.db.refresh(db_team)
        return db_team

    def assign_member_to_team(self, technical_id: uuid.UUID, team_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Assigns a technical user to a specific team."""
        tech_user = self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if tech_user:
            tech_user.team_id = team_id
            self.db.commit()
            self.db.refresh(tech_user)
        return tech_user
    
    def remove_member_from_team(self, technical_id: uuid.UUID) -> Optional[TechnicalModel]:
        """Removes a technical staff member from their current team."""
        tech_user = self.db.query(TechnicalModel).filter(TechnicalModel.technical_id == technical_id).first()
        if tech_user:
            tech_user.team_id = None  # Breaking the link
            self.db.commit()
            self.db.refresh(tech_user)
        return tech_user

    # --- PERFORMANCE METRICS ---

    def get_technical_performance(self, technical_id: uuid.UUID, start_date: date, end_date: date) -> Optional[TechnicalPerformance]:
        """Get performance metrics for a single technical staff member."""
        tech_user = self.get(technical_id)
        if not tech_user:
            return None
        
        # Get team name if assigned
        team_name = tech_user.team.team_name if tech_user.team else None
        
        # Query bookings for this technical's team in date range
        bookings_query = self.db.query(Booking).filter(
            Booking.technical_team_id == tech_user.team_id,
            Booking.appointment_date.between(start_date, end_date)
        )
        
        # Calculate metrics
        total_jobs = bookings_query.count()
        completed_jobs = bookings_query.filter(Booking.status == BookingStatus.COMPLETED).count()
        in_progress_jobs = bookings_query.filter(Booking.status == BookingStatus.IN_PROGRESS).count()
        
        # Calculate total revenue from completed jobs
        revenue_result = bookings_query.filter(
            Booking.status == BookingStatus.COMPLETED
        ).with_entities(func.sum(Booking.total_price)).scalar()
        total_revenue = Decimal(str(revenue_result)) if revenue_result else Decimal("0.00")
        
        # Calculate completion rate
        completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0.0
        
        return TechnicalPerformance(
            technical_id=tech_user.technical_id,
            name=tech_user.name,
            team_name=team_name,
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            in_progress_jobs=in_progress_jobs,
            completion_rate=round(completion_rate, 2),
            total_revenue=total_revenue
        )

    def get_team_performance(self, team_id: uuid.UUID, start_date: date, end_date: date) -> Optional[TeamPerformance]:
        """Get performance metrics for a technical team."""
        team = self.get_team(team_id)
        if not team:
            return None
        
        # Get team lead name
        team_lead_name = team.team_lead.name if team.team_lead else None
        
        # Count members
        member_count = len(team.members) if team.members else 0
        
        # Query bookings for this team in date range
        bookings_query = self.db.query(Booking).filter(
            Booking.technical_team_id == team_id,
            Booking.appointment_date.between(start_date, end_date)
        )
        
        # Calculate metrics
        total_jobs = bookings_query.count()
        completed_jobs = bookings_query.filter(Booking.status == BookingStatus.COMPLETED).count()
        in_progress_jobs = bookings_query.filter(Booking.status == BookingStatus.IN_PROGRESS).count()
        
        # Calculate total revenue from completed jobs
        revenue_result = bookings_query.filter(
            Booking.status == BookingStatus.COMPLETED
        ).with_entities(func.sum(Booking.total_price)).scalar()
        total_revenue = Decimal(str(revenue_result)) if revenue_result else Decimal("0.00")
        
        # Calculate completion rate
        completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0.0
        
        # Get individual member performances
        members_performance = []
        for member in (team.members or []):
            member_perf = self.get_technical_performance(member.technical_id, start_date, end_date)
            if member_perf:
                members_performance.append(member_perf)
        
        return TeamPerformance(
            team_id=team.team_id,
            team_name=team.team_name,
            team_lead_name=team_lead_name,
            member_count=member_count,
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            in_progress_jobs=in_progress_jobs,
            completion_rate=round(completion_rate, 2),
            total_revenue=total_revenue,
            members=members_performance
        )

    def get_all_teams_performance(self, start_date: date, end_date: date) -> List[TeamPerformance]:
        """Get performance metrics for all teams."""
        teams = self.get_all_teams(limit=1000)
        performances = []
        for team in teams:
            perf = self.get_team_performance(team.team_id, start_date, end_date)
            if perf:
                performances.append(perf)
        return performances

    def get_all_technicals_performance(self, start_date: date, end_date: date) -> List[TechnicalPerformance]:
        """Get performance metrics for all technical staff."""
        technicals = self.get_multi(limit=1000)
        performances = []
        for tech in technicals:
            perf = self.get_technical_performance(tech.technical_id, start_date, end_date)
            if perf:
                performances.append(perf)
        return performances


class TechnicalReportRepository:
    """Repository for managing technical reports."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, report_id: int) -> Optional[TechnicalReport]:
        """Get a report by ID."""
        return self.db.query(TechnicalReport).filter(TechnicalReport.report_id == report_id).first()
    
    def get_by_booking_id(self, booking_id: int) -> Optional[TechnicalReport]:
        """Get a report by booking ID. One report per booking."""
        return self.db.query(TechnicalReport).filter(TechnicalReport.booking_id == booking_id).first()
    
    def has_report(self, booking_id: int) -> bool:
        """Check if a booking has a submitted report."""
        return self.db.query(TechnicalReport).filter(TechnicalReport.booking_id == booking_id).first() is not None
    
    def create(self, report_in: TechnicalReportCreate, technical_id: uuid.UUID) -> TechnicalReport:
        """Create a new technical report with vehicle check list."""
        # Check if report already exists for this booking
        existing = self.get_by_booking_id(report_in.booking_id)
        if existing:
            raise ValueError(f"Report already exists for booking {report_in.booking_id}")
        
        # Convert lists and objects to JSON strings for storage
        image_urls_json = json.dumps(report_in.image_urls) if report_in.image_urls else None
        video_urls_json = json.dumps(report_in.video_urls) if report_in.video_urls else None
        checklist_items_json = json.dumps([item.model_dump() for item in report_in.checklist_items]) if report_in.checklist_items else None
        
        report = TechnicalReport(
            booking_id=report_in.booking_id,
            technical_id=technical_id,
            # Vehicle Info
            vehicle_type=report_in.vehicle_info.vehicle_type if report_in.vehicle_info else None,
            vin_number=report_in.vehicle_info.vin_number if report_in.vehicle_info else None,
            fuel_type=report_in.vehicle_info.fuel_type if report_in.vehicle_info else None,
            fuel_quantity=report_in.vehicle_info.fuel_quantity if report_in.vehicle_info else None,
            hybrid_type=report_in.vehicle_info.hybrid_type if report_in.vehicle_info else None,
            # Checklist
            checklist_items=checklist_items_json,
            # Work Description
            work_description=report_in.work_description,
            parts_used=report_in.parts_used,
            additional_notes=report_in.additional_notes,
            # Media
            image_urls=image_urls_json,
            video_urls=video_urls_json
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def update(self, report_id: int, report_in: TechnicalReportUpdate) -> Optional[TechnicalReport]:
        """Update an existing report."""
        report = self.get_by_id(report_id)
        if not report:
            return None
        
        update_data = report_in.model_dump(exclude_unset=True)
        
        # Handle vehicle_info separately
        if 'vehicle_info' in update_data and update_data['vehicle_info'] is not None:
            vehicle_info = update_data.pop('vehicle_info')
            if vehicle_info:
                report.vehicle_type = vehicle_info.get('vehicle_type')
                report.vin_number = vehicle_info.get('vin_number')
                report.fuel_type = vehicle_info.get('fuel_type')
                report.fuel_quantity = vehicle_info.get('fuel_quantity')
                report.hybrid_type = vehicle_info.get('hybrid_type')
        
        # Convert lists to JSON strings
        if 'checklist_items' in update_data and update_data['checklist_items'] is not None:
            checklist_items = update_data.pop('checklist_items')
            if checklist_items:
                report.checklist_items = json.dumps([item if isinstance(item, dict) else item.model_dump() for item in checklist_items])
        if 'image_urls' in update_data and update_data['image_urls'] is not None:
            report.image_urls = json.dumps(update_data.pop('image_urls'))
        if 'video_urls' in update_data and update_data['video_urls'] is not None:
            report.video_urls = json.dumps(update_data.pop('video_urls'))
        
        # Update remaining simple fields
        for key, value in update_data.items():
            if hasattr(report, key):
                setattr(report, key, value)
        
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def approve(self, report_id: int, admin_id: uuid.UUID, is_approved: bool, feedback: Optional[str] = None) -> Optional[TechnicalReport]:
        """Approve or reject a report."""
        report = self.get_by_id(report_id)
        if not report:
            return None
        
        report.is_approved = is_approved
        report.approved_by = admin_id
        report.approved_at = datetime.utcnow()
        report.admin_feedback = feedback
        
        self.db.commit()
        self.db.refresh(report)
        return report
    
    def get_reports_by_technical(self, technical_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[TechnicalReport]:
        """Get all reports by a technical user."""
        return self.db.query(TechnicalReport).filter(
            TechnicalReport.technical_id == technical_id
        ).order_by(TechnicalReport.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_pending_reports(self, skip: int = 0, limit: int = 100) -> List[TechnicalReport]:
        """Get all pending reports (not yet approved)."""
        return self.db.query(TechnicalReport).filter(
            not TechnicalReport.is_approved
        ).order_by(TechnicalReport.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_all_reports(self, skip: int = 0, limit: int = 100) -> List[TechnicalReport]:
        """Get all reports with pagination."""
        return self.db.query(TechnicalReport).order_by(
            TechnicalReport.created_at.desc()
        ).offset(skip).limit(limit).all()
    
    def delete(self, report_id: int) -> bool:
        """Delete a report."""
        report = self.get_by_id(report_id)
        if report:
            self.db.delete(report)
            self.db.commit()
            return True
        return False