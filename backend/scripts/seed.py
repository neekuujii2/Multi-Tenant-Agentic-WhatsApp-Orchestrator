"""
MongoDB Seeding Script.
Populates the tenants collection with two preconfigured test tenants:
1. Luxury Furniture (sofas, tables, interior design)
2. AutoCare (car servicing, cleaning, tire alignments)

Usage:
  python scripts/seed.py
"""
import os
import asyncio
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")


def seed_db():
    print("Connecting to MongoDB for seeding...")
    client = MongoClient(MONGODB_URI)
    db = client["orchestrator"]
    tenants_col = db["tenants"]

    # Clear existing tenants to ensure clean seed
    tenants_col.delete_many({})

    # 1. Tenant A: Luxury Furniture
    tenant_a = {
        "tenant_id": "luxury_furniture",
        "name": "Luxury Furniture Co.",
        "whatsapp": {
            "phone_number_id": os.getenv("TENANT_A_PHONE_NUMBER_ID", "123456789012345"),
            "access_token": os.getenv("TENANT_A_ACCESS_TOKEN", "EAAxxxxx_tenant_a_placeholder"),
            "business_account_id": "987654321098765"
        },
        "agent": {
            "system_prompt": (
                "You are 'Aura', the friendly customer assistant for Luxury Furniture Co.\n"
                "We design and sell high-end, premium solid wood furniture including designer sofas, "
                "elegant dining tables, ergonomic chairs, and bespoke cabinets.\n\n"
                "YOUR PERSONALITY:\n"
                "- Warm, professional, polite, and premium-tier hospitality.\n"
                "- Helpful but never pushy.\n\n"
                "YOUR RESPONSIBILITIES:\n"
                "- Recommend matching furniture products from our catalog.\n"
                "- Share image keys from the media library when customers request product pictures.\n"
                "- Promptly offer to book an appointment with our designer if the customer is interested in customizations.\n\n"
                "PRICING POLICY:\n"
                "- Premium Sofa Sets: Start from ₹85,000.\n"
                "- Royal Dining Tables (6-seater): Start from ₹1,20,000.\n"
                "- Ergonomic Accent Chairs: Start from ₹22,000."
            ),
            "llm_model": "claude-sonnet-4-6",
            "max_history_messages": 10,
            "temperature": 0.5,
            "supported_languages": ["en", "hi", "hinglish"]
        },
        "media_library": {
            "catalog": "https://images.unsplash.com/photo-1540518614846-7eded433c457?q=80&w=800&auto=format&fit=crop",
            "sofa": "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=800&auto=format&fit=crop",
            "dining": "https://images.unsplash.com/photo-1615066390971-03e4e1c36ddf?q=80&w=800&auto=format&fit=crop",
            "chair": "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?q=80&w=800&auto=format&fit=crop"
        },
        "campaign_templates": [
            {
                "template_id": "monsoon_sale",
                "name": "Monsoon Makeover Sale",
                "body": "Hi there! Build your dream home this monsoon. Get flat 15% off on all solid-wood dining sets and sofa sets. Use code: MONSOON15 at checkout 🌧️🛋️",
                "media_url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?q=80&w=800",
                "media_type": "image"
            }
        ],
        "settings": {
            "auto_reply_enabled": True,
            "sentiment_threshold": -0.4,
            "typing_indicator_enabled": True,
            "business_hours": {
                "enabled": False,
                "timezone": "Asia/Kolkata",
                "open": "09:00",
                "close": "20:00"
            }
        }
    }

    # 2. Tenant B: AutoCare Services
    tenant_b = {
        "tenant_id": "autocare",
        "name": "AutoCare Services",
        "whatsapp": {
            "phone_number_id": os.getenv("TENANT_B_PHONE_NUMBER_ID", "543210987654321"),
            "access_token": os.getenv("TENANT_B_ACCESS_TOKEN", "EAAxxxxx_tenant_b_placeholder"),
            "business_account_id": "567890123456789"
        },
        "agent": {
            "system_prompt": (
                "You are 'Gearbox', the service coordinator for AutoCare Services.\n"
                "We provide premium multi-brand automobile servicing, oil change, denting/painting, "
                "interior detailing, tire alignment, and general mechanical repair.\n\n"
                "YOUR PERSONALITY:\n"
                "- Knowledgeable, clear, efficient, and direct.\n"
                "- Focus on vehicle reliability and customer safety.\n\n"
                "YOUR RESPONSIBILITIES:\n"
                "- Assist customers with estimating service costs.\n"
                "- Share services catalog from the media library.\n"
                "- Help book servicing slots at our workshop.\n\n"
                "PRICING & SERVICES:\n"
                "- General Servicing (Hatchback/Sedan): ₹3,999 (includes oil change, filters check, wash).\n"
                "- Deep Interior Detailing: ₹2,499.\n"
                "- Wheel Alignment & Balancing: ₹999."
            ),
            "llm_model": "claude-sonnet-4-6",
            "max_history_messages": 8,
            "temperature": 0.3,
            "supported_languages": ["en", "hi", "hinglish"]
        },
        "media_library": {
            "catalog": "https://images.unsplash.com/photo-1486006920555-c77dce18193b?q=80&w=800&auto=format&fit=crop",
            "workshop": "https://images.unsplash.com/photo-1616788494707-ec28f08d05a1?q=80&w=800&auto=format&fit=crop",
            "service_bay": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?q=80&w=800&auto=format&fit=crop"
        },
        "campaign_templates": [
            {
                "template_id": "road_trip_check",
                "name": "Summer Road Trip Checklist",
                "body": "Planning a weekend road trip? Get our 25-Point Safety Inspection for just ₹499. Ensure your brakes, AC, and tires are road-trip ready! Reply slot to book. 🚗☀️",
                "media_url": "https://images.unsplash.com/photo-1506015391300-4802dc74de2e?q=80&w=800",
                "media_type": "image"
            }
        ],
        "settings": {
            "auto_reply_enabled": True,
            "sentiment_threshold": -0.5,
            "typing_indicator_enabled": True,
            "business_hours": {
                "enabled": True,
                "timezone": "Asia/Kolkata",
                "open": "08:00",
                "close": "19:00"
            }
        }
    }

    tenants_col.insert_many([tenant_a, tenant_b])
    print("Database seeded successfully with 2 tenants:")
    print("  1. luxury_furniture (Luxury Furniture Co.)")
    print("  2. autocare (AutoCare Services)")


if __name__ == "__main__":
    seed_db()
