from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.repositories.booking_repositories import BookingRepository
from src.models.booking_model import BookingCreate
from src.schemas.booking import User
from src.config.telegram_client import telegram_client
from src.repositories.user_respositories import UserRepository
from src.config.settings import settings
import logging
from src.schemas.booking import Booking
import html
logger = logging.getLogger(__name__)
class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.user_repo = UserRepository(db)


    async def _send_status_notification(self, user, booking):
        """Internal helper to handle status-based Telegram alerts"""
        if not user or not user.telegram_chat_id:
            return # Skip if user hasn't linked Telegram yet

        status_messages = {
            "Pending": "⏳ Your booking is being reviewed by our team.",
            "Confirmed": "✅ Great news! Your booking has been approved.",
            "Cancelled": "❌ Your booking has been cancelled.",
            "Rejected": "🚫 Sorry, we cannot fulfill this request at the moment.",
            "Completed": "🏁 Your car is ready! Thank you for choosing us."
        }

        friendly_text = status_messages.get(booking.status, "Your booking status has been updated.")

        message = (
            f"🚗 *Booking Update*\n\n"
            f"Status: *{booking.status}*\n"
            f"{friendly_text}\n\n"
            f"Order ID: #{booking.booking_id}\n"
            f"Car: {booking.car_make} {booking.car_model}"
        )

        try:
            await telegram_client.send_message(user.telegram_chat_id, message)
        except Exception as e:
            logger.error(f"Telegram notification failed for user {user.user_id}: {e}")

    async def process_new_booking(self, booking_info: BookingCreate):
        '''
        1. (Optional) Check if garage is overbooked for that date.
        2. Call repository to handle Shadow Account and initial save.
        3. Trigger a notification (SMS/Telegram) to the user with their tracking link.
        '''
        try:
            # 1. User Resolution (Check if account exists)
            user = self.user_repo.get_user_by_phone(booking_info.contact_phone)
            is_new_user = False

            if not user:
                is_new_user = True
                user = self.user_repo.create_shadow_account(
                    phone=booking_info.contact_phone,
                    full_name=booking_info.full_name
                )
            else:
                # 2. Conflict Check for existing users
                if self.user_repo.has_booking_conflict(
                    user_id=user.user_id,
                    appointment_date=booking_info.appointment_date,
                    start_time=booking_info.start_time
                ):
                    raise ValueError(f"You already have a booking scheduled for {booking_info.appointment_date}.")

            # 3. Create the Booking (Repo handles its own commit/rollback)
            booking = self.booking_repo.create_booking_with_items(booking_info, user.user_id)

            try:
                await self._notify_admin_of_new_booking(booking, user)
            except Exception as admin_err:
                logger.error(f"⚠️ Admin notification failed: {admin_err}")

            # 4. Notification Branching Logic
            magic_link = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={user.user_id}"

            try:
                chat_id_val = int(user.telegram_chat_id) if user.telegram_chat_id else 0
            except (ValueError, TypeError):
                chat_id_val = 0
                
            if is_new_user or chat_id_val == 0:
                # Scenario A: New User / No Telegram Linked
                # We can't send a Telegram message yet, so we return the link for SMS or Frontend
                return{
                    "booking": booking,
                    "is_new_user": is_new_user,
                    "telegram_link": magic_link
                }
               
            else:
                # Scenario B: Existing User with Telegram linked
                msg = (
                    f"*Booking Received!*\n\n"
                    f"Hello {user.full_name}, we've received your request for a {booking.car_make}.\n"
                    f"Status: ⏳ *Pending Approval*\n"
                    f"Date: {booking.appointment_date}"
                )
                try:
                    await telegram_client.send_message(
                    chat_id=user.telegram_chat_id, 
                    text=msg, 
                    parse_mode="HTML"
                )
                    print(f"DEBUG: Push notification sent to {user.telegram_chat_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to send user notification: {e}")

            return {
                "booking": booking,
                "is_new_user": False,
                "telegram_link": None
            }
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
        except Exception as e:
            logger.error(f"Booking process crashed: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="An internal error occurred.")
        
    async def _notify_admin_of_new_booking(self, booking: Booking, user: User):
        """
        Alerts the shop owner/admin via Telegram.
        """
        # 1. Check if Admin ID exists
        if not hasattr(settings, 'ADMIN_CHAT_ID') or not settings.ADMIN_CHAT_ID:
            logger.warning("Admin alert skipped: ADMIN_CHAT_ID not configured.")
            return

        # 2. Sanitize data (Prevents crashes if user types '<' or '>' in notes)
        safe_name = html.escape(user.full_name or "Unknown")
        safe_note = html.escape(booking.note or "No notes.")
        safe_car = html.escape(f"{booking.car_make} {booking.car_model}")

        # 3. Build HTML Message
        admin_msg = (
            "🔔 <b>NEW WEB BOOKING</b>\n"
            "----------------------------\n"
            f"👤 <b>Customer:</b> {safe_name}\n"
            f"📞 <b>Phone:</b> <code>{user.phone}</code>\n"
            f"🚗 <b>Vehicle:</b> {safe_car}\n"
            f"📅 <b>Date:</b> {booking.appointment_date}\n"
            f"⏰ <b>Time:</b> {booking.start_time}\n"
            f"💰 <b>Total:</b> ${booking.total_price}\n"
            "----------------------------\n"
            f"📝 <b>Note:</b> <i>{safe_note}</i>\n\n"
            "👉 <a href='https://yourdashboard.com/bookings'>Open Admin Dashboard</a>"
        )

        # 4. Send using the global telegram_client
        try:
            await telegram_client.send_message(
                chat_id=settings.ADMIN_CHAT_ID,
                text=admin_msg,
                parse_mode="HTML" 
            )
            logger.info(f"✅ Admin notified for booking {booking.booking_id}")
        except Exception as e:
            logger.error(f"❌ Telegram Admin Alert Failed: {e}")

    async def update_booking_status(self, booking_id: str, new_status: str,admin_id: str = None):

        """Admin logic to change status and alert user"""
        booking = self.booking_repo.get_with_items(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # Update the status in DB
        updated_booking = self.booking_repo.update_booking_status(booking_id, new_status)
        
        # Fetch user to get telegram_chat_id
        user = self.user_repo.get_user_by_id(updated_booking.user_id)

        # If completed, generate and upload invoice 
        if new_status == "Completed":
            try:
                await self._handle_job_completion(user, updated_booking,admin_id)
            except Exception as e:
                logger.error(f"Invoice upload failed for booking {booking_id}: {e}")

        # Notify user of the change (Confirmed, Completed, etc.)
        await self._send_status_notification(user, updated_booking)

        return updated_booking
    
    # async def _handle_job_completion(self,user,booking,admin_id):
    #     pdf_content = generate_invoice_pdf(booking)
    #     from src.service.s3_service import s3_service
    #     s3_key = f"invoices/booking_{booking.booking_id}.pdf"
    #     invoice_url = s3_service.upload_file_from_bytes(
    #         file_bytes=pdf_content,
    #         s3_key=s3_key,
    #         content_type="application/pdf"
    #     )
    #     if invoice_url:
    #         from src.models.booking_model import BookingInvoice
    #         new_invoice = BookingInvoice(
    #             booking_id=booking.booking_id,
    #             external_invoice_url=invoice_url,
    #             uploaded_by=admin_id
    #         )
    #         self.db.add(new_invoice)
    #         if user.telegram_chat_id:
    #             caption = f"📄 Your invoice for booking #{booking.booking_id} is ready."
    #             await telegram_client.send_document(
    #                 chat_id=user.telegram_chat_id,
    #                 document_url=invoice_url,
    #                 caption=f"Your car is ready! 🏁 Attached is your digital invoice for #{booking.booking_id}."
    #             )
    #         # 5. Create Maintenance Alert (6 months later)
    #         from src.models.booking_model import MaintenanceAlert
    #         from datetime import datetime, timedelta
    #         alert = MaintenanceAlert(
    #             user_id=user.user_id,
    #             booking_id=booking.booking_id,
    #             alert_date=datetime.now() + timedelta(days=180),
    #             message="Time for your next maintenance check-up! 🚗💨"
    #         )
    #         self.db.add(alert)
    #         self.db.commit()
    
    async def get_user_dashboard(self, user_id: int):
        """
        1. Find user by ID.
        2. If not found, they have no history.
        3. Fetch all bookings, invoices, and alerts via repository.
        """
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No history found for this user."
            )
        
        return self.booking_repo.get_bookings_by_user_id(user.user_id)
    
    async def get_booking_details_for_user(self, booking_id: int):
        booking = self.booking_repo.get_with_items(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
