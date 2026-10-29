from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from rooms.models import RoomType, Room, RoomAmenity
from bookings.models import Booking, Payment
from services.models import DiningVenue, SpaService, HousekeepingTask

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds Elara Grand Hotel & Resort with ultra-luxury 5-star inventory, venues, spa, and sample bookings."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))
        self.stdout.write(self.style.MIGRATE_HEADING("   SEEDING ELARA GRAND HOTEL & RESORT DATA        "))
        self.stdout.write(self.style.MIGRATE_HEADING("=================================================="))

        # 1. Superuser & Guest Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@elara.com',
            defaults={
                'username': 'admin@elara.com',
                'first_name': 'Alexander',
                'last_name': 'Vance',
                'role': 'SUPER_ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.role = 'SUPER_ADMIN'
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.set_password('SecureAdmin123!')
        admin_user.save()

        guest_user, _ = User.objects.get_or_create(
            email='guest@elara.com',
            defaults={
                'username': 'guest@elara.com',
                'first_name': 'Arjun',
                'last_name': 'Sharma',
                'phone': '+91 98201 54321',
                'role': 'CUSTOMER',
            }
        )
        guest_user.set_password('LuxuryGuest123!')
        guest_user.save()
        self.stdout.write(self.style.SUCCESS("[OK] Admin and Guest users verified."))

        # 2. Luxury Amenities
        amenities_data = [
            ("High-Speed Wi-Fi 6", "fa-wifi"),
            ("65\" 4K OLED Smart TV", "fa-tv"),
            ("Italian Marble Bathtub", "fa-bath"),
            ("Nespresso Coffee System", "fa-mug-hot"),
            ("24/7 Royal Butler Service", "fa-bell-concierge"),
            ("Private Panoramic Balcony", "fa-mountain-sun"),
            ("Herman Miller Workspace", "fa-chair"),
            ("Molton Brown Toiletries", "fa-pump-soap"),
            ("Private Temperature-Controlled Jacuzzi", "fa-hot-tub-person"),
            ("In-Room Cocktail Bar", "fa-wine-glass"),
        ]
        amenities = {}
        for name, icon in amenities_data:
            amenity, _ = RoomAmenity.objects.get_or_create(name=name, defaults={'icon': icon})
            amenities[name] = amenity
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(amenities)} Luxury Room Amenities populated."))

        # 3. Room Types
        room_types_data = [
            {
                "name": "Deluxe King Room",
                "slug": "deluxe-king-room",
                "description": "Sophisticated contemporary room with floor-to-ceiling windows overlooking Pune's verdant hilltops. Features a plush pillow-top king bed, marble vanity, and smart lighting controls.",
                "base_price": Decimal("14500.00"),
                "max_adults": 2,
                "max_children": 1,
                "bed_type": "1 King Bed",
                "size_sqm": 48,
                "amenities": ["High-Speed Wi-Fi 6", "65\" 4K OLED Smart TV", "Italian Marble Bathtub", "Nespresso Coffee System", "Molton Brown Toiletries"]
            },
            {
                "name": "Executive Club Suite",
                "slug": "executive-club-suite",
                "description": "Expansive luxury suite with a private lounge area and exclusive access to The Elara Club Lounge with complimentary afternoon high tea and evening craft cocktails.",
                "base_price": Decimal("24000.00"),
                "max_adults": 3,
                "max_children": 1,
                "bed_type": "1 California King Bed",
                "size_sqm": 68,
                "amenities": ["High-Speed Wi-Fi 6", "65\" 4K OLED Smart TV", "Italian Marble Bathtub", "Nespresso Coffee System", "Herman Miller Workspace", "In-Room Cocktail Bar"]
            },
            {
                "name": "Royal Pune Luxury Suite",
                "slug": "royal-pune-luxury-suite",
                "description": "Inspired by Maratha royal heritage with handcrafted brass motifs, bespoke teak furnishings, a dedicated walk-in wardrobe, and separate dining salon.",
                "base_price": Decimal("48000.00"),
                "max_adults": 3,
                "max_children": 2,
                "bed_type": "1 Emperor King Bed",
                "size_sqm": 95,
                "amenities": ["High-Speed Wi-Fi 6", "65\" 4K OLED Smart TV", "Italian Marble Bathtub", "24/7 Royal Butler Service", "Private Panoramic Balcony", "In-Room Cocktail Bar"]
            },
            {
                "name": "The Elara Presidential Suite",
                "slug": "elara-presidential-suite",
                "description": "The pinnacle of hospitality. 180 square meters of pure opulence spanning a master wing, private dining room for 8, baby grand piano, private spa treatment room, and dedicated 24-hour butler.",
                "base_price": Decimal("125000.00"),
                "max_adults": 4,
                "max_children": 2,
                "bed_type": "Custom Royal King Bed",
                "size_sqm": 180,
                "amenities": ["High-Speed Wi-Fi 6", "65\" 4K OLED Smart TV", "Italian Marble Bathtub", "24/7 Royal Butler Service", "Private Temperature-Controlled Jacuzzi", "In-Room Cocktail Bar", "Private Panoramic Balcony"]
            },
            {
                "name": "Serenity Garden Pool Villa",
                "slug": "serenity-garden-pool-villa",
                "description": "Private standalone villa nestled within aromatic botanical gardens featuring an open-air plunge pool, secluded sun deck, outdoor stone shower, and in-villa spa pavilion.",
                "base_price": Decimal("38000.00"),
                "max_adults": 2,
                "max_children": 2,
                "bed_type": "1 King Bed & Daybed",
                "size_sqm": 110,
                "amenities": ["High-Speed Wi-Fi 6", "65\" 4K OLED Smart TV", "Private Temperature-Controlled Jacuzzi", "Private Panoramic Balcony", "Nespresso Coffee System"]
            }
        ]

        created_room_types = {}
        for rdata in room_types_data:
            rtype, _ = RoomType.objects.get_or_create(
                slug=rdata["slug"],
                defaults={
                    "name": rdata["name"],
                    "description": rdata["description"],
                    "base_price_per_night": rdata["base_price"],
                    "max_adults": rdata["max_adults"],
                    "max_children": rdata["max_children"],
                    "bed_type": rdata["bed_type"],
                    "room_size_sqm": rdata["size_sqm"],
                }
            )
            for aname in rdata["amenities"]:
                if aname in amenities:
                    rtype.amenities.add(amenities[aname])
            created_room_types[rdata["slug"]] = rtype
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_room_types)} Signature Room Types configured."))

        # 4. Rooms Inventory
        rooms_inventory = [
            ("101", "deluxe-king-room", "1st Floor", "AVAILABLE"),
            ("102", "deluxe-king-room", "1st Floor", "AVAILABLE"),
            ("103", "deluxe-king-room", "1st Floor", "OCCUPIED"),
            ("201", "deluxe-king-room", "2nd Floor", "AVAILABLE"),
            ("202", "deluxe-king-room", "2nd Floor", "CLEANING"),
            ("301", "executive-club-suite", "3rd Floor", "AVAILABLE"),
            ("302", "executive-club-suite", "3rd Floor", "AVAILABLE"),
            ("401", "executive-club-suite", "4th Floor", "OCCUPIED"),
            ("501", "royal-pune-luxury-suite", "5th Floor", "AVAILABLE"),
            ("502", "royal-pune-luxury-suite", "5th Floor", "RESERVED"),
            ("801", "elara-presidential-suite", "Penthouse Floor", "AVAILABLE"),
            ("V-01", "serenity-garden-pool-villa", "Resort Gardens", "AVAILABLE"),
            ("V-02", "serenity-garden-pool-villa", "Resort Gardens", "OCCUPIED"),
        ]

        created_rooms = []
        for rnum, slug, floor, rstatus in rooms_inventory:
            rm, _ = Room.objects.get_or_create(
                room_number=rnum,
                defaults={
                    "room_type": created_room_types[slug],
                    "floor": floor,
                    "status": rstatus,
                    "is_active": True
                }
            )
            created_rooms.append(rm)
        self.stdout.write(self.style.SUCCESS(f"[OK] {len(created_rooms)} Rooms cataloged into live inventory."))

        # 5. Fine Dining Venues
        dining_venues_data = [
            {
                "name": "The Saffron Lounge",
                "slug": "the-saffron-lounge",
                "cuisine": "Royal Awadhi & Peshwa Heritage",
                "description": "Celebrated fine-dining sanctuary presenting authentic royal recipes slow-cooked in hand-beaten copper vessels with silver leaf garnishes.",
                "opening_hours": "12:30 PM - 03:30 PM, 07:00 PM - 11:30 PM",
                "dress_code": "Formal / Traditional Luxury",
                "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "name": "Aura Rooftop Bar & Lounge",
                "slug": "aura-rooftop-lounge",
                "cuisine": "Mediterranean Tapas & Craft Mixology",
                "description": "Perched on the 18th floor offering 360-degree panoramic sunset vistas of Pune's skyline, bespoke botanical infusions, and live jazz.",
                "opening_hours": "05:00 PM - 01:30 AM",
                "dress_code": "Smart Casual",
                "image_url": "https://images.unsplash.com/photo-1578474846511-04ba529f0b88?q=80&w=1200&auto=format&fit=crop"
            },
            {
                "name": "Silk & Spice",
                "slug": "silk-and-spice",
                "cuisine": "Pan-Asian & Live Teppanyaki",
                "description": "Dramatic live culinary theater featuring authentic Japanese robata grills, Dim Sum masterclasses, and handcrafted sushi bars.",
                "opening_hours": "06:30 PM - 11:30 PM",
                "dress_code": "Smart Casual",
                "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1200&auto=format&fit=crop"
            }
        ]
        for vdata in dining_venues_data:
            DiningVenue.objects.get_or_create(slug=vdata["slug"], defaults=vdata)
        self.stdout.write(self.style.SUCCESS("[OK] 3 Signature Dining Venues configured."))

        # 6. Luxury Spa Services
        spa_services_data = [
            ("Royal Shirodhara & Abhyanga", "AYURVEDA", 90, Decimal("7500.00"), "Warm medicated herbal oils poured in a rhythmic flow over the third eye, accompanied by traditional synchronized full-body massage."),
            ("Deep Tissue Himalayan Salt Stone Therapy", "MASSAGE", 60, Decimal("5500.00"), "Heated organic Himalayan salt stones deliver deep thermal relaxation to release chronic muscular tension."),
            ("24K Gold Cellular Radiance Facial", "FACIAL", 75, Decimal("8500.00"), "Pure 24-karat gold leaf infused with marine collagen and peptide serums for extraordinary luminous rejuvenation."),
            ("Detoxifying Hydrotherapy & Mineral Cocoon", "HYDROTHERAPY", 60, Decimal("4800.00"), "Aromatherapy thermal hydro-bath followed by volcanic sea clay body wrap to draw out deep toxins.")
        ]
        for name, cat, dur, pr, desc in spa_services_data:
            SpaService.objects.get_or_create(
                name=name,
                defaults={
                    "category": cat,
                    "duration_minutes": dur,
                    "price": pr,
                    "description": desc,
                    "is_active": True
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] 4 Luxury Spa & Wellness Treatments registered."))

        # 7. Housekeeping Tasks
        room_202 = Room.objects.filter(room_number="202").first()
        if room_202:
            HousekeepingTask.objects.get_or_create(
                room=room_202,
                task_type="CHECKOUT_CLEANING",
                defaults={
                    "status": "PENDING",
                    "priority": "HIGH",
                    "notes": "VIP Guest checkout completed. High-priority turnaround needed for incoming arrival."
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Housekeeping operations active."))

        # 8. Sample Confirmed Booking for Guest
        room_101 = Room.objects.filter(room_number="101").first()
        if room_101 and not Booking.objects.filter(user=guest_user).exists():
            today = date.today()
            check_in = today + timedelta(days=5)
            check_out = today + timedelta(days=8)
            nights = 3
            base_amt = room_101.room_type.base_price_per_night * nights
            tax_amt = (base_amt * Decimal("0.18")).quantize(Decimal("0.01"))
            final_amt = base_amt + tax_amt

            sample_booking = Booking.objects.create(
                user=guest_user,
                room=room_101,
                check_in_date=check_in,
                check_out_date=check_out,
                num_adults=2,
                num_children=0,
                room_price_total=base_amt,
                tax_total=tax_amt,
                final_amount=final_amt,
                status=Booking.Status.CONFIRMED,
                special_requests="High floor preferred, extra goose-down pillows, honeymoon welcome champagne."
            )
            Payment.objects.create(
                booking=sample_booking,
                amount=final_amt,
                transaction_id="TXN-ELARA-98421",
                payment_method="CREDIT_CARD",
                card_last4="8821",
                status=Payment.Status.SUCCESS
            )
            self.stdout.write(self.style.SUCCESS(f"[OK] Sample Confirmed Reservation created for {guest_user.email} (ID: #{str(sample_booking.id)[:8]})."))

        self.stdout.write(self.style.MIGRATE_HEADING("--------------------------------------------------"))
        self.stdout.write(self.style.SUCCESS("ELARA GRAND HOTEL & RESORT SEEDING COMPLETE!"))
