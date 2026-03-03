from enum import Enum

# Enums (keep as is)
class VehicleType(str, Enum):
    SEDAN = "Sedan"
    SUV = "SUV"
    TRUCK = "Truck"
    VAN = "Van"
    COUPE = "Coupe"
    CONVERTIBLE = "Convertible"
    WAGON = "Wagon"
    HATCHBACK = "Hatchback"
    MINIVAN = "Minivan"
    PICKUP = "Pickup"
    CROSSOVER = "Crossover"
    MOTORCYCLE = "Motorcycle"
    COMMERCIAL = "Commercial"

class FuelType(str, Enum):
    GASOLINE = "Gasoline"
    DIESEL = "Diesel"
    HYBRID = "Hybrid"
    ELECTRIC = "Electric"
    PLUG_IN_HYBRID = "Plug-in Hybrid"
    FLEX_FUEL = "Flex Fuel"

class DriveType(str, Enum):
    FWD = "FWD"
    RWD = "RWD"
    AWD = "AWD"
    FOUR_WD = "4WD"

class TransmissionType(str, Enum):
    MANUAL = "Manual"
    AUTOMATIC = "Automatic"
    CVT = "CVT"
    SEMI_AUTOMATIC = "Semi-Automatic"
    DUAL_CLUTCH = "Dual Clutch"

class ServiceType(str, Enum):
    GARAGE = "Garage"
    HOME = "Home"

class BookingStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    COMPLETED = "Completed"

class BookingSource(str, Enum):
    WEB = "Web"
    PHONE = "Phone"

class UserStatus(str, Enum):
    GUEST = "Guest"
    ACTIVE = "Active"