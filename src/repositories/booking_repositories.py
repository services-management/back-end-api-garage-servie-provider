from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from src.models.booking_model import BookingCreate
from src.repositories.base_repositories import BaseRepository
from src.schemas.booking import Booking, BookingItem, User


class BookingRepository(BaseRepository[Booking]):

    def __init__(self, db:Session):
        super().__init__(db, model=Booking)

    def create_booking_with_service(self,scheme:BookingCreate,nested_services: List[Any]) -> Booking:
        '''
        Specialized method to handle the complex 'Shadow Account' flow.
        We don't use self.add() here because we want to control the 
        transaction (one commit at the end).
        '''
        # Handle User Identity (Check by phone)
        user = self.db.query(User).filter(User.phone == scheme.phone).first()
        if not user:
            user = User(
                phone = scheme.phone,
                full_name = scheme.full_name,
                is_active = False
            )
            self.db.add(user)
            self.db.flush()

            # Create the Booking Header
            new_booking = Booking(
                user_id=user.user_id,
                car_make=scheme.car_make,
                car_model=scheme.car_model,
                contact_phone=scheme.phone,
                appointment_date=scheme.appointment_date,
                start_time=scheme.start_time,
                service_location=scheme.service_location,
                source=scheme.source,
                status="PENDING",
                payment_status="pending",
                amount_paid=Decimal("0.00"),
                total_price=Decimal("0.00")
            )
            self.db.add(new_booking)
            self.db.flush() # get the booking_id
            # 3. Calculate total and create items
            total_price = Decimal("0.00")
            
            for service_data in nested_services:
                # Service line item
                service_total = service_data.service_price if hasattr(service_data, 'service_price') else Decimal("0.00")
                
                service_line = BookingItem(
                    booking_id=new_booking.booking_id,
                    service_id=service_data.service_id,
                    product_id=None,  # Service-only item
                    quantity=1,  # Default quantity for service
                    price_at_purchase=service_total,
                    item_type="service"  # Add this field to BookingItem model
                )
                self.db.add(service_line)
                total_price += service_total

                # Product line items
                for product_data in getattr(service_data, 'products', []):
                    product_total = product_data.price * Decimal(str(product_data.quantity))
                    
                    product_line = BookingItem(
                        booking_id=new_booking.booking_id,
                        service_id=service_data.service_id,
                        product_id=product_data.product_id,
                        quantity=product_data.quantity,
                        price_at_purchase=product_data.price,
                    )
                    self.db.add(product_line)
                    total_price += product_total

            # 4. Update booking total
            new_booking.total_price = total_price
            
            # 5. Commit everything
            self.db.commit()
            
            # 6. Return full booking details
            return self.get_full_booking_details(new_booking.booking_id)


    def get_full_booking_details(self, booking_id: int) -> Optional[Booking]:
        """
        Get booking with all related data
        """
       
        return self.db.query(Booking).options(
            joinedload(Booking.customer),
            selectinload(Booking.items).joinedload(BookingItem.product),
            selectinload(Booking.items).joinedload(BookingItem.service)
        ).filter(Booking.booking_id == booking_id).first()
       
    def update_payment(self, booking_id: int, amount: Decimal, payment_method: str) -> Optional[Booking]:
        """
        Update booking payment status
        """
        booking = self.get(booking_id)
        if not booking:
            return None
        
        booking.amount_paid += amount
        
        # Update payment status
        if booking.amount_paid >= booking.total_price:
            booking.payment_status = "paid"
        elif booking.amount_paid > 0:
            booking.payment_status = "partial"
        else:
            booking.payment_status = "pending"
        
        # Record payment (you might want a separate Payment table)
        # For now, we'll just update the booking
        
        self.db.commit()
        self.db.refresh(booking)
        return booking
    
    def assign_technical_team(self, booking_id: int, technical_team_id: UUID) -> Optional[Booking]:
        """
        Assign technical team to booking
        """
        booking = self.get(booking_id)
        if booking:
            booking.technical_team_id = technical_team_id
            booking.status = "CONFIRMED"  # Change status when team assigned
            booking.assigned_at = datetime.utcnow()  # Add this field to Booking model
            self.db.commit()
            self.db.refresh(booking)
        return booking
    
    def search_bookings(self, query: str = None, status: str = None, limit: int = 100)-> List[Booking]:
        """
        Search by phone number, customer name, or filter by status.
        """
        db_query = self.db.query(Booking).options(
            joinedload(Booking.customer),
            joinedload(Booking.items)
        )

        if query:
            # Search across multiple fields at once
            db_query = db_query.join(User).filter(
                or_(
                    User.phone.contains(query),
                    User.full_name.ilike(f"%{query}%"),
                    Booking.car_model.ilike(f"%{query}%")
                )
            )

        if status:
            db_query = db_query.filter(Booking.status == status)

        return db_query.order_by(Booking.appointment_date.desc()).limit(limit).all()
    
    def update_booking_status(self, booking_id: int, new_status: str) -> Booking:
        booking = self.get(booking_id) # Using BaseRepository get
        if booking:
            booking.status = new_status
            self.db.commit()
            self.db.refresh(booking)
        return booking

    def update_appointment(self, booking_id: int, new_date: date, new_time: time) -> Booking:
        booking = self.get(booking_id)
        if booking:
            booking.appointment_date = new_date
            booking.start_time = new_time
            self.db.commit()
            self.db.refresh(booking)
        return booking
    
    def update(self, booking_id: int, **update_data) -> Optional[Booking]:
        """Generic update method for any Booking field."""
        booking = self.get(booking_id)
        if booking:
            for key, value in update_data.items():
                setattr(booking, key, value)
            self.db.commit()
            self.db.refresh(booking)
        return booking

    def cancel_booking(self, booking_id: int):
        """
        Soft delete: keep the record but mark as cancelled.
        """
        booking = self.get(booking_id)
        if booking:
            booking.status = "CANCELLED"
            # If products were reserved, you could logic here to return them to stock
            self.db.commit()
            return True
        return False

    def hard_delete_booking(self, booking_id: int):
        """
        Only use this if the booking was a mistake/test data.
        BaseRepository.delete() handles this, but we must ensure 
        cascade delete is set in the Model for BookingItems.
        """
        return self.delete(booking_id) # Uses BaseRepository delete
    
    def get_bookings_by_range(self, start_date: date, end_date: date):
        return (
            self.db.query(Booking)
            .filter(Booking.appointment_date.between(start_date, end_date))
            .options(joinedload(Booking.customer))
            .order_by(Booking.appointment_date, Booking.start_time)
            .all()
        )
    
    def get_with_items(self, booking_id: int) -> Optional[Booking]:
        """Get booking with all related items"""
        return self.db.query(Booking).options(
            joinedload(Booking.items),
            joinedload(Booking.customer)
        ).filter(Booking.booking_id == booking_id).first()
    
    def exists(self, booking_id: int) -> bool:
        """Check if booking exists without loading full object"""
        return self.db.query(Booking.booking_id).filter(
            Booking.booking_id == booking_id
        ).first() is not None