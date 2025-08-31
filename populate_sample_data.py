#!/usr/bin/env python3
"""
Sample Data Population Script for Match Square
This script populates the application with sample data for testing matching functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def register_property_owner(name, email, phone, property_type, area_sqft, current_rent, pincode, address, asking_price=None):
    """Register a property owner"""
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "property_details": {
            "property_type": property_type,
            "area_sqft": area_sqft,
            "current_rent": current_rent,
            "pincode": pincode,
            "address": address,
            "asking_price": asking_price,
            "location": {
                "latitude": 12.9716,  # Bangalore coordinates
                "longitude": 77.5946,
                "address": address,
                "city": "Bangalore",
                "state": "Karnataka",
                "country": "India",
                "pincode": pincode
            }
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/users/property-owner", json=data)
    if response.status_code == 200:
        print(f"✅ Property Owner '{name}' registered successfully")
        return response.json()
    else:
        print(f"❌ Failed to register Property Owner '{name}': {response.text}")
        return None

def register_franchise_company(company_name, email, phone, category, investment_required, area_size, pincode):
    """Register a franchise company"""
    data = {
        "company_name": company_name,
        "email": email,
        "phone": phone,
        "franchise_requirements": {
            "category": category,
            "investment_required": investment_required,
            "area_size": area_size,
            "pincode": pincode,
            "description": f"Great {category} franchise opportunity",
            "location_description": f"Prime location in {pincode}"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/users/franchise-company", json=data)
    if response.status_code == 200:
        print(f"✅ Franchise Company '{company_name}' registered successfully")
        return response.json()
    else:
        print(f"❌ Failed to register Franchise Company '{company_name}': {response.text}")
        return None

def register_entrepreneur(name, email, phone, entrepreneur_type, budget, pincode, business_idea=None):
    """Register an entrepreneur"""
    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "entrepreneur_type": entrepreneur_type,
        "budget": budget,
        "pincode": pincode,
        "business_idea": business_idea or f"Looking for {entrepreneur_type} opportunities"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/entrepreneur", json=data)
    if response.status_code == 200:
        print(f"✅ Entrepreneur '{name}' registered successfully")
        return response.json()
    else:
        print(f"❌ Failed to register Entrepreneur '{name}': {response.text}")
        return None

def main():
    print("🚀 Populating Match Square with comprehensive sample data...")
    print("=" * 60)
    
    # Property Owners (with diverse properties for better matching)
    print("\n🏢 Registering Property Owners...")
    property_owners = [
        {
            "name": "Rajesh Kumar",
            "email": "rajesh@example.com",
            "phone": "9876543210",
            "property_type": "retail",
            "area_sqft": 800,
            "current_rent": 25000,
            "pincode": "560001",
            "address": "MG Road, Bangalore",
            "asking_price": 8000000
        },
        {
            "name": "Priya Sharma",
            "email": "priya@example.com",
            "phone": "9876543211",
            "property_type": "commercial",
            "area_sqft": 1200,
            "current_rent": 35000,
            "pincode": "560002",
            "address": "Commercial Street, Bangalore",
            "asking_price": 12000000
        },
        {
            "name": "Amit Patel",
            "email": "amit@example.com",
            "phone": "9876543212",
            "property_type": "office",
            "area_sqft": 1500,
            "current_rent": 40000,
            "pincode": "560003",
            "address": "Koramangala, Bangalore",
            "asking_price": 15000000
        },
        {
            "name": "Deepak Verma",
            "email": "deepak@example.com",
            "phone": "9876543213",
            "property_type": "restaurant",
            "area_sqft": 1000,
            "current_rent": 30000,
            "pincode": "560004",
            "address": "Indiranagar, Bangalore",
            "asking_price": 10000000
        },
        {
            "name": "Meera Iyer",
            "email": "meera@example.com",
            "phone": "9876543214",
            "property_type": "retail",
            "area_sqft": 600,
            "current_rent": 20000,
            "pincode": "560005",
            "address": "JP Nagar, Bangalore",
            "asking_price": 6000000
        },
        {
            "name": "Vikram Singh",
            "email": "vikram@example.com",
            "phone": "9876543215",
            "property_type": "commercial",
            "area_sqft": 2000,
            "current_rent": 50000,
            "pincode": "560006",
            "address": "Whitefield, Bangalore",
            "asking_price": 20000000
        },
        {
            "name": "Anjali Desai",
            "email": "anjali@example.com",
            "phone": "9876543216",
            "property_type": "office",
            "area_sqft": 800,
            "current_rent": 25000,
            "pincode": "560007",
            "address": "Electronic City, Bangalore",
            "asking_price": 8000000
        },
        {
            "name": "Rahul Gupta",
            "email": "rahul@example.com",
            "phone": "9876543217",
            "property_type": "retail",
            "area_sqft": 1200,
            "current_rent": 35000,
            "pincode": "560008",
            "address": "Marathahalli, Bangalore",
            "asking_price": 12000000
        }
    ]
    
    for owner in property_owners:
        register_property_owner(**owner)
        time.sleep(0.5)  # Small delay between requests
    
    # Franchise Companies (with diverse investment requirements)
    print("\n🏪 Registering Franchise Companies...")
    franchise_companies = [
        {
            "company_name": "Quick Bites",
            "email": "info@quickbites.com",
            "phone": "9876543220",
            "category": "food_beverage",
            "investment_required": 500000,
            "area_size": 800,
            "pincode": "560001"
        },
        {
            "company_name": "Tech Solutions",
            "email": "info@techsolutions.com",
            "phone": "9876543221",
            "category": "services",
            "investment_required": 300000,
            "area_size": 600,
            "pincode": "560002"
        },
        {
            "company_name": "Fashion Hub",
            "email": "info@fashionhub.com",
            "phone": "9876543222",
            "category": "retail",
            "investment_required": 800000,
            "area_size": 1000,
            "pincode": "560003"
        },
        {
            "company_name": "Coffee Corner",
            "email": "info@coffeecorner.com",
            "phone": "9876543223",
            "category": "food_beverage",
            "investment_required": 400000,
            "area_size": 500,
            "pincode": "560004"
        },
        {
            "company_name": "Beauty Salon",
            "email": "info@beautysalon.com",
            "phone": "9876543224",
            "category": "services",
            "investment_required": 250000,
            "area_size": 400,
            "pincode": "560005"
        },
        {
            "company_name": "Gym Fitness",
            "email": "info@gymfitness.com",
            "phone": "9876543225",
            "category": "healthcare",
            "investment_required": 1000000,
            "area_size": 1500,
            "pincode": "560006"
        },
        {
            "company_name": "Mobile Store",
            "email": "info@mobilestore.com",
            "phone": "9876543226",
            "category": "retail",
            "investment_required": 600000,
            "area_size": 800,
            "pincode": "560007"
        },
        {
            "company_name": "Tutoring Center",
            "email": "info@tutoringcenter.com",
            "phone": "9876543227",
            "category": "education",
            "investment_required": 200000,
            "area_size": 600,
            "pincode": "560008"
        },
        {
            "company_name": "Pharmacy Plus",
            "email": "info@pharmacyplus.com",
            "phone": "9876543228",
            "category": "healthcare",
            "investment_required": 700000,
            "area_size": 700,
            "pincode": "560001"
        },
        {
            "company_name": "Bakery Delight",
            "email": "info@bakerydelight.com",
            "phone": "9876543229",
            "category": "food_beverage",
            "investment_required": 350000,
            "area_size": 600,
            "pincode": "560002"
        }
    ]
    
    for franchise in franchise_companies:
        register_franchise_company(**franchise)
        time.sleep(0.5)
    
    # Entrepreneurs (with diverse budgets and types)
    print("\n👤 Registering Entrepreneurs...")
    entrepreneurs = [
        {
            "name": "Naveen Kumar",
            "email": "naveen@example.com",
            "phone": "9876543230",
            "entrepreneur_type": "investor",
            "budget": 1200000,
            "pincode": "560001",
            "business_idea": "Looking for food franchise opportunities"
        },
        {
            "name": "Sneha Reddy",
            "email": "sneha@example.com",
            "phone": "9876543231",
            "entrepreneur_type": "idea_owner",
            "budget": 600000,
            "pincode": "560002",
            "business_idea": "Want to start a tech service business"
        },
        {
            "name": "Arjun Singh",
            "email": "arjun@example.com",
            "phone": "9876543232",
            "entrepreneur_type": "investor",
            "budget": 900000,
            "pincode": "560003",
            "business_idea": "Interested in retail franchise"
        },
        {
            "name": "Kavya Sharma",
            "email": "kavya@example.com",
            "phone": "9876543233",
            "entrepreneur_type": "idea_owner",
            "budget": 400000,
            "pincode": "560004",
            "business_idea": "Planning to open a coffee shop"
        },
        {
            "name": "Rohan Mehta",
            "email": "rohan@example.com",
            "phone": "9876543234",
            "entrepreneur_type": "investor",
            "budget": 800000,
            "pincode": "560005",
            "business_idea": "Looking for beauty and wellness franchise"
        },
        {
            "name": "Priya Patel",
            "email": "priya.patel@example.com",
            "phone": "9876543235",
            "entrepreneur_type": "idea_owner",
            "budget": 1500000,
            "pincode": "560006",
            "business_idea": "Want to start a fitness center"
        },
        {
            "name": "Aditya Verma",
            "email": "aditya@example.com",
            "phone": "9876543236",
            "entrepreneur_type": "investor",
            "budget": 500000,
            "pincode": "560007",
            "business_idea": "Interested in mobile retail business"
        },
        {
            "name": "Neha Kapoor",
            "email": "neha@example.com",
            "phone": "9876543237",
            "entrepreneur_type": "idea_owner",
            "budget": 300000,
            "pincode": "560008",
            "business_idea": "Planning to start an educational center"
        },
        {
            "name": "Vikrant Singh",
            "email": "vikrant@example.com",
            "phone": "9876543238",
            "entrepreneur_type": "investor",
            "budget": 1000000,
            "pincode": "560001",
            "business_idea": "Looking for healthcare franchise opportunities"
        },
        {
            "name": "Ananya Das",
            "email": "ananya@example.com",
            "phone": "9876543239",
            "entrepreneur_type": "idea_owner",
            "budget": 450000,
            "pincode": "560002",
            "business_idea": "Want to start a bakery business"
        }
    ]
    
    for entrepreneur in entrepreneurs:
        register_entrepreneur(**entrepreneur)
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("✅ Comprehensive sample data population completed!")
    print("\n📊 Current Statistics:")
    
    # Check final stats
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Property Owners: {stats['total_property_owners']}")
            print(f"   Franchise Companies: {stats['total_franchise_companies']}")
            print(f"   Entrepreneurs: {stats['total_entrepreneurs']}")
            print(f"   Total Users: {stats['total_users']}")
        else:
            print("❌ Could not fetch statistics")
    except Exception as e:
        print(f"❌ Error fetching statistics: {e}")
    
    print("\n🌐 Visit http://localhost:8000/recommendations to see the matches!")
    print("💡 The matching should now work with proper budget compatibility.")
    print("🎯 AI insights will be generated for all property owners.")

if __name__ == "__main__":
    main()
