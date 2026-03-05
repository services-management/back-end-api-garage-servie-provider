from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session,joinedload, selectinload
from sqlalchemy import or_
from src.schemas.booking import User, Booking, BookingItem, BookingStatus
from src.models.booking_model import BookingCreate, AdminBookingCreate
from src.schemas.product import Service, Product, ServiceCategoryAssociation, ProductVehicleCompatibility, ProductStatus
from src.core.enums import ServiceType
from src.repositories.user_respositories import UserRepository
from src.repositories.inventory_repositories import InventoryRepository
from src.schemas.product import Inventory
import re
class BookingRepository:
    def __init__(self, db: Session ):
        self.db = db
        self.user_repo = UserRepository(db)
        self.inven_repo = InventoryRepository(db)
    def create_booking_with_items(self, booking_info: BookingCreate, user_id: UUID) -> Booking:
        """
        Optimized: Creates booking and items in a single transaction with eager loading.
        """
        # 1. Initialize booking
        new_booking = Booking(
            user_id=user_id,
            contact_phone=booking_info.contact_phone,
            vehicle_id=booking_info.vehicle_id,
            car_make=booking_info.car_make,
            car_model=booking_info.car_model,
            car_year=booking_info.car_year,
            car_engine=booking_info.car_engine,
            appointment_date=booking_info.appointment_date,
            start_time=booking_info.start_time,
            service_location=booking_info.service_location,
            note=booking_info.note,
            source=booking_info.source,
            status=BookingStatus.PENDING,
            payment_status="pending",
            amount_paid=Decimal("0.0"),
            total_price=Decimal("0.0")
        )

        self.db.add(new_booking)
        self.db.flush()  # Secure the booking_id for foreign keys

        # 2. Process items using optimized helper
        items_to_save, final_total = self._prepare_and_calculate_items(
            new_booking.booking_id, 
            booking_info.items,
            new_booking.vehicle_id,
            booking_info.service_mode
        )
        
        # 3. Finalize and save
        new_booking.total_price = final_total
        self.db.add_all(items_to_save) # Batch add items
        
        try:
            self.db.commit()
            return self.db.query(Booking).options(
                joinedload(Booking.items).joinedload(BookingItem.service),
                joinedload(Booking.items).joinedload(BookingItem.product)
            ).filter(Booking.booking_id == new_booking.booking_id).first()
        except Exception as e:
            self.db.rollback()
            raise e

    def _prepare_and_calculate_items(self, booking_id: int, items_in: list, vehicle_id: Optional[int] = None, service_mode: ServiceType = ServiceType.GARAGE) -> tuple[list[BookingItem], Decimal]:
        prepared_items = []
        total_accumulated_price = Decimal("0.0")

        # 1. Collect all Product IDs and Service IDs first for batch fetching
        service_ids = [i.service_id for i in items_in if i.service_id]
        direct_product_ids = [i.product_id for i in items_in if i.product_id and i.product_id != 0]

        # 2. Batch fetch Services with associations
        services_map = {}
        if service_ids:
            services = (
                self.db.query(Service)
                .options(joinedload(Service.associations).joinedload(ServiceCategoryAssociation.category))
                .filter(Service.service_id.in_(service_ids))
                .all()
            )
            services_map = {s.service_id: s for s in services}

        # 3. Batch fetch Direct Products
        products_map = {}
        if direct_product_ids:
            products = self.db.query(Product).filter(Product.product_id.in_(direct_product_ids)).all()
            products_map = {p.product_id: p for p in products}

        # 4. Process each item
        for item_in in items_in:
            item_qty = Decimal(str(item_in.quantity)) if item_in.quantity > 0 else Decimal("1.0")
            unit_price = Decimal("0.0")
            db_product_id = None
            current_service_id = None
            if item_in.service_id:
                service = services_map.get(item_in.service_id)
                if not service:
                    raise ValueError(f"Service ID {item_in.service_id} not found.")
                
                current_service_id = item_in.service_id
                # Pricing Logic: Labor based on service mode
                unit_price += service.home_price if service_mode == ServiceType.HOME else service.garage_price
                
                # Add bundled products from categories
                if vehicle_id:
                    for assoc in service.associations:
                        category = assoc.category
                        # Find compatible product in this category
                        product_stmt = (
                            self.db.query(Product)
                            .join(ProductVehicleCompatibility, Product.product_id == ProductVehicleCompatibility.product_id)
                            .filter(
                                Product.category_id == category.categoryID,
                                ProductVehicleCompatibility.vehicle_id == vehicle_id,
                                Product.status == ProductStatus.ACTIVE
                            )
                        )
                        product = product_stmt.first()
                        
                        if product:
                            compat = self.db.query(ProductVehicleCompatibility).filter(
                                ProductVehicleCompatibility.product_id == product.product_id,
                                ProductVehicleCompatibility.vehicle_id == vehicle_id
                            ).first()
                            
                            p_qty = Decimal("1.0")
                            if compat and compat.quantity_required:
                                match = re.search(r"(\d+\.?\d*)", compat.quantity_required)
                                if match:
                                    p_qty = Decimal(match.group(1))
                            
                            # Pricing Logic: (Selling Price + Price Adjustment) * Qty for Home
                            base_unit_price = product.selling_price
                            if service_mode == ServiceType.HOME:
                                final_prod_price = base_unit_price + product.price_adjustment
                            else:
                                final_prod_price = base_unit_price
                                
                            unit_price += (final_prod_price * p_qty)
                            total_stock_to_remove = p_qty * item_qty
                            self.deduct_stock_safe(product.product_id, total_stock_to_remove)
            # --- BRANCH B: Standalone Product Item ---
            elif item_in.product_id and item_in.product_id != 0:
                product = products_map.get(item_in.product_id)
                if not product:
                    raise ValueError(f"Product ID {item_in.product_id} not found.")
                
                db_product_id = item_in.product_id
                # Pricing Logic for standalone product
                if service_mode == ServiceType.HOME:
                    unit_price = product.selling_price + product.price_adjustment
                else:
                    unit_price = product.selling_price
                self.deduct_stock_safe(db_product_id, item_qty)
            # --- BRANCH C: Final Calculation ---
            # Multiplies the UNIT PRICE (bundle or product) by the QUANTITY
            line_subtotal = unit_price * item_qty

            # Add names to the object for the Pydantic validator to find
            new_item = BookingItem(
                booking_id=booking_id,
                product_id=db_product_id,
                service_id=current_service_id,
                quantity=item_qty,
                price_at_purchase=unit_price
            )
            
            # Attach relationship objects for the Pydantic 'resolve_names' validator
            if current_service_id:
                service_obj = services_map.get(current_service_id)
                new_item.service = service_obj 
                # This is the key: set the name so Pydantic can find it
                new_item.service_name = service_obj.name
            if db_product_id:
                product_obj = products_map.get(db_product_id)
                new_item.product = product_obj
                # This is the key: set the name so Pydantic can find it
                new_item.product_name = product_obj.name


            prepared_items.append(new_item)
            total_accumulated_price += line_subtotal

        return prepared_items, total_accumulated_price
    
    def deduct_stock_safe(self, product_id: int, quantity: Decimal):
        # Lock the row to prevent other bookings from stealing the stock
        inventory = (
            self.db.query(Inventory)
            .filter(Inventory.product_id == product_id)
            .with_for_update()
            .first()
        )

        if not inventory:
            raise ValueError(f"Inventory record not found for product ID {product_id}.")

        if inventory.current_stock < quantity:
            raise ValueError(f"Insufficient stock for Product {product_id}. Available: {inventory.current_stock}")

        inventory.current_stock -= quantity
        
        # Optional: Low stock alert
        if inventory.min_stock_level and inventory.current_stock <= inventory.min_stock_level:
            print(f"ALERT: Product {product_id} is running low!")
            
        return inventory
    
    def get_bookings_by_user_id(self,user_id:UUID) -> List[Booking]:
        """
        Get all bookings for a specific user
        """
        return self.db.query(Booking).filter(Booking.user_id == user_id).order_by(Booking.appointment_date.desc()).all()    

    def create_admin_booking(self, booking_info:AdminBookingCreate, user_id: UUID)-> Booking:
        """
        Create booking by admin with assigned garage
        """
        # initialize booking object 
        new_booking = Booking(
            user_id = user_id,
            contact_phone=booking_info.contact_phone,
            vehicle_id=booking_info.vehicle_id,
            car_make=booking_info.car_make,
            car_model=booking_info.car_model,
            car_year=booking_info.car_year,
            car_engine=booking_info.car_engine,
            appointment_date=booking_info.appointment_date,
            start_time=booking_info.start_time,
            service_location=booking_info.service_location,
            note=booking_info.note,
            source=booking_info.source,
            internal_note=booking_info.internal_note,
            assigned_garage_id=booking_info.assigned_garage_id,
            technician_id=getattr(booking_info, 'technician_id', None),
            service_mode=booking_info.service_mode,
            status=BookingStatus.CONFIRMED,
            payment_status="pending",
            amount_paid=Decimal("0.0"),
            total_price=Decimal("0.0")  # Will calculate below
        )
        
        
        self.db.add(new_booking)
        self.db.flush() # get booking_id
        
        items_to_save, final_total = self._prepare_and_calculate_items(
        new_booking.booking_id, 
        booking_info.items,
        new_booking.vehicle_id,
        new_booking.service_mode
    )
    
        new_booking.total_price = final_total
        self.db.add_all(items_to_save)

        try:
            self.db.commit()
            return self.db.query(Booking).options(
                joinedload(Booking.items).joinedload(BookingItem.service),
                joinedload(Booking.items).joinedload(BookingItem.product)
            ).filter(Booking.booking_id == new_booking.booking_id).first()
        except Exception as e:
            self.db.rollback()
            raise e

    def get_full_booking_details(self, booking_id: int) -> Optional[Booking]:
        """
        Get booking with all related data
        """
        return self.db.query(Booking).options(
            joinedload(Booking.customer),
            selectinload(Booking.items).joinedload(BookingItem.product),
            selectinload(Booking.items).joinedload(BookingItem.service)
        ).filter(Booking.booking_id == booking_id).first()

    def get_booking_counts_by_status(self, target_date: date) -> dict:
        """
        Returns a summary for the Admin: 
        {'PENDING': 5, 'IN_PROGRESS': 2, 'COMPLETED': 10}
        """
        from sqlalchemy import func
        results = self.db.query(
            Booking.status, func.count(Booking.booking_id)
        ).filter(Booking.appointment_date == target_date).group_by(Booking.status).all()
    
        return {status.value: count for status, count in results}

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
            booking.status = BookingStatus.CONFIRMED  # Change status when team assigned
            booking.assigned_at = datetime.utcnow()  # Add this field to Booking model
            self.db.commit()
            self.db.refresh(booking)
        return booking
    
    def get_technical_jobs(self, technical_team_id: UUID,target_date:date) -> List[Booking]:
        """
        The 'To-Do List' for a specific technical team.  
        """
        return self.db.query(Booking).filter(
            Booking.technical_team_id == technical_team_id,
            Booking.appointment_date == target_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS])
        ).order_by(Booking.start_time).all()

    def search_bookings(self, query: str = None, status: str = None, limit: int = 100)-> List[Booking]:
        """
        Search by phone number, customer name, or filter by status.
        """
        db_query = self.db.query(Booking).options(
            joinedload(Booking.customer),
            # Chain the load: Booking -> Items -> Service
            joinedload(Booking.items).joinedload(BookingItem.service),
            # Chain the load: Booking -> Items -> Product
            joinedload(Booking.items).joinedload(BookingItem.product)
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
            .options(
                joinedload(Booking.customer),
                # Chain the loads: Booking -> Items -> Service/Product
                joinedload(Booking.items).joinedload(BookingItem.service),
                joinedload(Booking.items).joinedload(BookingItem.product),
                # Load the invoice link if it exists
                joinedload(Booking.invoice) 
            )
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
    
    def get(self, booking_id: int) -> Optional[Booking]:
        """Fetch a single booking by its ID"""
        return self.db.query(Booking).filter(Booking.booking_id == booking_id).first()

    def get_booking_for_invoice(self, booking_id: int):
        return self.db.query(Booking).options(
            joinedload(Booking.items).joinedload(BookingItem.service),
            joinedload(Booking.items).joinedload(BookingItem.product),
            joinedload(Booking.customer)
        ).filter(Booking.booking_id == booking_id).first()
