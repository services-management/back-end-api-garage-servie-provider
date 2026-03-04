from fastapi import APIRouter, Request, Depends, Response
from sqlalchemy.orm import Session
import json

from src.config.database import get_db
from src.repositories.user_respositories import UserRepository
from src.repositories.booking_repositories import BookingRepository
from src.config.telegram_client import telegram_client


router = APIRouter(prefix="/webhook", tags=["Telegram"])

@router.post("/telegram")
async def handle_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("⚠️ Received non-JSON data (likely ngrok warning page)")
        return Response(content="Expected JSON", status_code=200)

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        first_name = data["message"]["chat"].get("first_name","")
        last_name = data["message"]["chat"].get("last_name","")
        tg_username = data["message"]["chat"].get("username","")
        full_name = f"{first_name} {last_name}".strip()
        text = data["message"].get("text", "").strip()
        user_repo = UserRepository(db)
        booking_repo = BookingRepository(db)

        # Handle /start command
        if text.startswith("/start"):
            # Check if user is already linked
            existing_user = user_repo.get_user_by_telegram_chat_id(chat_id)
            if existing_user:
                await telegram_client.send_message(
                    chat_id,
                    f"Welcome back, {existing_user.full_name or 'Friend'}! Your account is already linked. Type /mybookings to see your service history."
                )
                return {"status": "already_linked"}

            parts = text.split(" ")
            # Case 1: /start <prefix_id> (Deep Linking)
            if len(parts) > 1:
                magic_data = parts[1]
                try:
                    # Role-based linking: admin_UUID, tech_UUID, or just UUID (user)
                    if magic_data.startswith("admin_"):
                        admin_id = magic_data.replace("admin_", "")
                        from src.schemas.admin import adminModel
                        admin = db.query(adminModel).filter(adminModel.admin_id == admin_id).first()
                        if admin:
                            # We'll need to add telegram_chat_id to adminModel if it's missing
                            # For now, let's check if it exists or use a generic update
                            if hasattr(admin, "telegram_chat_id"):
                                admin.telegram_chat_id = chat_id
                                db.commit()
                                await telegram_client.send_message(chat_id, f"Welcome Admin {admin.username}! Your account is linked. You will receive alerts here.")
                                return {"status": "admin_linked"}
                        
                    elif magic_data.startswith("tech_"):
                        tech_id = magic_data.replace("tech_", "")
                        from src.schemas.techincal import TechnicalModel
                        tech = db.query(TechnicalModel).filter(TechnicalModel.technical_id == tech_id).first()
                        if tech:
                            # We'll need to add telegram_chat_id to TechnicalModel if it's missing
                            if hasattr(tech, "telegram_chat_id") or True: # Force check
                                # Check if column exists, if not we might need to add it
                                tech.telegram_chat_id = chat_id
                                db.commit()
                                await telegram_client.send_message(chat_id, f"Welcome Technician {tech.name}! Your account is linked. You will receive new job alerts here.")
                                return {"status": "tech_linked"}

                    else:
                        # Default User linking
                        user_id_str = magic_data
                        user = user_repo.get_user_by_id(user_id_str)
                        if user:
                            user.telegram_chat_id = chat_id
                            user.full_name = full_name
                            user.telegram_username = tg_username
                            db.commit()
                            print(f"✅ Linked Chat ID {chat_id} to User {user.full_name}")
                            await telegram_client.send_message(
                                chat_id, 
                                "Great! Your account is now linked. You will receive booking updates here. You can type /mybookings to see your history."
                            )
                            return {"status": "linked"}
                        
                    await telegram_client.send_message(chat_id, "Sorry, the magic link is invalid or expired.")
                except Exception as e:
                    print(f"❌ Error linking telegram: {e}")
                    await telegram_client.send_message(chat_id, "An error occurred while linking your account.")
            # Case 2: Just /start
            else:
                await telegram_client.send_message(
                    chat_id,
                    "Welcome to the Garage Service Bot! To receive notifications, link this chat to your user account by creating a booking on our website. You will receive a unique link to connect your account."
                )
                return {"status": "welcome_message_sent"}
        
        # Handle /mybookings command
        elif text == "/mybookings":
            user = user_repo.get_user_by_telegram_chat_id(chat_id)
            if not user:
                await telegram_client.send_message(
                    chat_id,
                    "Your Telegram account is not linked to any user. Please complete a booking on our website to link your account."
                )
                return {"status": "user_not_linked"}

            bookings = booking_repo.get_bookings_by_user_id(user.user_id)
            if not bookings:
                await telegram_client.send_message(chat_id, "You have no booking history.")
                return {"status": "no_bookings"}

            message = "Here is your booking history:\n\n"
            for booking in bookings:
                message += (
                    f"🚗 *Booking #{booking.booking_id}*\n"
                    f"   Car: {booking.car_make} {booking.car_model}\n"
                    f"   Date: {booking.appointment_date.strftime('%Y-%m-%d')} at {booking.start_time.strftime('%H:%M')}\n"
                    f"   Status: *{booking.status.value}*\n\n"
                )
            
            await telegram_client.send_message(chat_id, message)
            return {"status": "bookings_sent"}
                
    return {"status": "ignored"}