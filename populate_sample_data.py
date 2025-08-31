import requests
import json
import time
from typing import List, Dict, Any

# Base URL for the API
BASE_URL = "http://localhost:8000"

def add_property_owners():
    """Add sample property owners"""
    print("🏢 Adding Property Owners...")
    
    property_owners = [
        {
            "name": "Rajesh Kumar",
            "email": "rajesh.kumar@email.com",
            "phone": "9876543210",
            "property_details": {
                "type": "Commercial Space",
                "size": 1500,
                "price": 25000,
                "location": {
                    "address": "Connaught Place, New Delhi",
                    "latitude": 28.6328,
                    "longitude": 77.2198,
                    "city": "New Delhi",
                    "state": "Delhi",
                    "country": "India"
                }
            }
        },
        {
            "name": "Priya Sharma",
            "email": "priya.sharma@email.com",
            "phone": "9876543211",
            "property_details": {
                "type": "Retail Shop",
                "size": 800,
                "price": 18000,
                "location": {
                    "address": "Bandra West, Mumbai",
                    "latitude": 19.0596,
                    "longitude": 72.8295,
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India"
                }
            }
        },
        {
            "name": "Amit Patel",
            "email": "amit.patel@email.com",
            "phone": "9876543212",
            "property_details": {
                "type": "Office Space",
                "size": 2000,
                "price": 35000,
                "location": {
                    "address": "Koramangala, Bangalore",
                    "latitude": 12.9349,
                    "longitude": 77.6050,
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "country": "India"
                }
            }
        },
        {
            "name": "Sneha Reddy",
            "email": "sneha.reddy@email.com",
            "phone": "9876543213",
            "property_details": {
                "type": "Restaurant Space",
                "size": 1200,
                "price": 22000,
                "location": {
                    "address": "T Nagar, Chennai",
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                    "city": "Chennai",
                    "state": "Tamil Nadu",
                    "country": "India"
                }
            }
        },
        {
            "name": "Vikram Singh",
            "email": "vikram.singh@email.com",
            "phone": "9876543214",
            "property_details": {
                "type": "Warehouse",
                "size": 5000,
                "price": 45000,
                "location": {
                    "address": "Gurgaon, Haryana",
                    "latitude": 28.4595,
                    "longitude": 77.0266,
                    "city": "Gurgaon",
                    "state": "Haryana",
                    "country": "India"
                }
            }
        },
        {
            "name": "Anjali Desai",
            "email": "anjali.desai@email.com",
            "phone": "9876543215",
            "property_details": {
                "type": "Boutique Space",
                "size": 600,
                "price": 15000,
                "location": {
                    "address": "Jubilee Hills, Hyderabad",
                    "latitude": 17.4065,
                    "longitude": 78.4772,
                    "city": "Hyderabad",
                    "state": "Telangana",
                    "country": "India"
                }
            }
        },
        {
            "name": "Rahul Verma",
            "email": "rahul.verma@email.com",
            "phone": "9876543216",
            "property_details": {
                "type": "Gym Space",
                "size": 1000,
                "price": 20000,
                "location": {
                    "address": "Salt Lake, Kolkata",
                    "latitude": 22.5726,
                    "longitude": 88.3639,
                    "city": "Kolkata",
                    "state": "West Bengal",
                    "country": "India"
                }
            }
        },
        {
            "name": "Meera Iyer",
            "email": "meera.iyer@email.com",
            "phone": "9876543217",
            "property_details": {
                "type": "Spa Center",
                "size": 900,
                "price": 18000,
                "location": {
                    "address": "Vasant Vihar, Delhi",
                    "latitude": 28.5562,
                    "longitude": 77.1000,
                    "city": "Delhi",
                    "state": "Delhi",
                    "country": "India"
                }
            }
        },
        {
            "name": "Karan Malhotra",
            "email": "karan.malhotra@email.com",
            "phone": "9876543218",
            "property_details": {
                "type": "Tech Startup Space",
                "size": 1500,
                "price": 28000,
                "location": {
                    "address": "Hinjewadi, Pune",
                    "latitude": 18.5204,
                    "longitude": 73.8567,
                    "city": "Pune",
                    "state": "Maharashtra",
                    "country": "India"
                }
            }
        },
        {
            "name": "Divya Gupta",
            "email": "divya.gupta@email.com",
            "phone": "9876543219",
            "property_details": {
                "type": "Café Space",
                "size": 700,
                "price": 16000,
                "location": {
                    "address": "Indiranagar, Bangalore",
                    "latitude": 12.9716,
                    "longitude": 77.5946,
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "country": "India"
                }
            }
        }
    ]
    
    for i, owner in enumerate(property_owners, 1):
        try:
            response = requests.post(f"{BASE_URL}/api/users/property-owner", json=owner)
            if response.status_code == 200:
                print(f"✅ Property Owner {i}: {owner['name']} - {owner['property_details']['type']}")
            else:
                print(f"❌ Failed to add Property Owner {i}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error adding Property Owner {i}: {e}")
        time.sleep(0.5)

def add_franchise_companies():
    """Add sample franchise companies"""
    print("\n🏪 Adding Franchise Companies...")
    
    franchise_companies = [
        {
            "company_name": "Coffee Corner Express",
            "email": "info@coffeecorner.com",
            "phone": "9876543220",
            "franchise_requirements": {
                "category": "Food & Beverage",
                "investment_required": 500000,
                "area_size": 800,
                "description": "Premium coffee shop franchise with modern ambiance"
            }
        },
        {
            "company_name": "FitLife Gym",
            "email": "franchise@fitlife.com",
            "phone": "9876543221",
            "franchise_requirements": {
                "category": "Health & Fitness",
                "investment_required": 800000,
                "area_size": 1500,
                "description": "Modern fitness center with latest equipment"
            }
        },
        {
            "company_name": "TechTutors Academy",
            "email": "franchise@techtutors.com",
            "phone": "9876543222",
            "franchise_requirements": {
                "category": "Education",
                "investment_required": 300000,
                "area_size": 1000,
                "description": "Coding and technology education for kids and adults"
            }
        },
        {
            "company_name": "BeautyBliss Salon",
            "email": "franchise@beautybliss.com",
            "phone": "9876543223",
            "franchise_requirements": {
                "category": "Beauty & Wellness",
                "investment_required": 400000,
                "area_size": 600,
                "description": "Premium beauty salon and spa services"
            }
        },
        {
            "company_name": "QuickBite Restaurant",
            "email": "franchise@quickbite.com",
            "phone": "9876543224",
            "franchise_requirements": {
                "category": "Food & Beverage",
                "investment_required": 600000,
                "area_size": 1200,
                "description": "Fast-casual restaurant serving healthy meals"
            }
        },
        {
            "company_name": "EduSmart Learning",
            "email": "franchise@edusmart.com",
            "phone": "9876543225",
            "franchise_requirements": {
                "category": "Education",
                "investment_required": 250000,
                "area_size": 800,
                "description": "After-school tutoring and skill development"
            }
        },
        {
            "company_name": "GreenMart Grocery",
            "email": "franchise@greenmart.com",
            "phone": "9876543226",
            "franchise_requirements": {
                "category": "Retail",
                "investment_required": 700000,
                "area_size": 2000,
                "description": "Organic and healthy grocery store"
            }
        },
        {
            "company_name": "PetCare Plus",
            "email": "franchise@petcare.com",
            "phone": "9876543227",
            "franchise_requirements": {
                "category": "Pet Services",
                "investment_required": 350000,
                "area_size": 900,
                "description": "Pet grooming, daycare, and veterinary services"
            }
        },
        {
            "company_name": "CleanPro Services",
            "email": "franchise@cleanpro.com",
            "phone": "9876543228",
            "franchise_requirements": {
                "category": "Services",
                "investment_required": 200000,
                "area_size": 500,
                "description": "Professional cleaning and maintenance services"
            }
        },
        {
            "company_name": "FashionForward",
            "email": "franchise@fashionforward.com",
            "phone": "9876543229",
            "franchise_requirements": {
                "category": "Retail",
                "investment_required": 450000,
                "area_size": 1000,
                "description": "Trendy fashion boutique for young adults"
            }
        }
    ]
    
    for i, franchise in enumerate(franchise_companies, 1):
        try:
            response = requests.post(f"{BASE_URL}/api/users/franchise-company", json=franchise)
            if response.status_code == 200:
                print(f"✅ Franchise Company {i}: {franchise['company_name']} - {franchise['franchise_requirements']['category']}")
            else:
                print(f"❌ Failed to add Franchise Company {i}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error adding Franchise Company {i}: {e}")
        time.sleep(0.5)

def add_entrepreneurs():
    """Add sample entrepreneurs"""
    print("\n👨‍💼 Adding Entrepreneurs...")
    
    entrepreneurs = [
        {
            "name": "Arjun Mehta",
            "email": "arjun.mehta@email.com",
            "phone": "9876543230",
            "entrepreneur_type": "investor",
            "budget": 1000000,
            "pincode": "400001",
            "business_idea": "Tech startup in fintech space"
        },
        {
            "name": "Priya Reddy",
            "email": "priya.reddy@email.com",
            "phone": "9876543231",
            "entrepreneur_type": "idea_owner",
            "budget": 500000,
            "pincode": "110001",
            "business_idea": "Organic food delivery service"
        },
        {
            "name": "Rahul Sharma",
            "email": "rahul.sharma@email.com",
            "phone": "9876543232",
            "entrepreneur_type": "both",
            "budget": 800000,
            "pincode": "600001",
            "business_idea": "AI-powered education platform"
        },
        {
            "name": "Anjali Patel",
            "email": "anjali.patel@email.com",
            "phone": "9876543233",
            "entrepreneur_type": "investor",
            "budget": 1200000,
            "pincode": "302015",
            "business_idea": "Luxury hospitality business"
        },
        {
            "name": "Vikram Singh",
            "email": "vikram.singh@email.com",
            "phone": "9876543234",
            "entrepreneur_type": "idea_owner",
            "budget": 300000,
            "pincode": "302031",
            "business_idea": "Traditional handicraft marketplace"
        },
        {
            "name": "Meera Iyer",
            "email": "meera.iyer@email.com",
            "phone": "9876543235",
            "entrepreneur_type": "both",
            "budget": 600000,
            "pincode": "500001",
            "business_idea": "Health and wellness center"
        },
        {
            "name": "Karan Malhotra",
            "email": "karan.malhotra@email.com",
            "phone": "9876543236",
            "entrepreneur_type": "investor",
            "budget": 900000,
            "pincode": "700001",
            "business_idea": "Real estate investment"
        },
        {
            "name": "Divya Gupta",
            "email": "divya.gupta@email.com",
            "phone": "9876543237",
            "entrepreneur_type": "idea_owner",
            "budget": 400000,
            "pincode": "560001",
            "business_idea": "Sustainable fashion brand"
        },
        {
            "name": "Amit Kumar",
            "email": "amit.kumar@email.com",
            "phone": "9876543238",
            "entrepreneur_type": "both",
            "budget": 750000,
            "pincode": "400001",
            "business_idea": "E-commerce platform for local artisans"
        },
        {
            "name": "Sneha Verma",
            "email": "sneha.verma@email.com",
            "phone": "9876543239",
            "entrepreneur_type": "investor",
            "budget": 1500000,
            "pincode": "110001",
            "business_idea": "Renewable energy solutions"
        }
    ]
    
    for i, entrepreneur in enumerate(entrepreneurs, 1):
        try:
            response = requests.post(f"{BASE_URL}/api/users/entrepreneur", json=entrepreneur)
            if response.status_code == 200:
                print(f"✅ Entrepreneur {i}: {entrepreneur['name']} - {entrepreneur['entrepreneur_type']} (Pincode: {entrepreneur['pincode']})")
            else:
                print(f"❌ Failed to add Entrepreneur {i}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error adding Entrepreneur {i}: {e}")
        time.sleep(0.5)

def main():
    """Main function to populate all sample data"""
    print("🚀 Populating Sample Data for Business Matchmaking Platform")
    print("=" * 60)
    
    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print("❌ Server is not running. Please start the application first.")
            return
        
        print("✅ Server is running. Starting data population...\n")
        
        # Add all sample data
        add_property_owners()
        add_franchise_companies()
        add_entrepreneurs()
        
        print("\n🎉 Sample data population completed!")
        print("=" * 60)
        print("📊 Summary:")
        print("   • 10 Property Owners added")
        print("   • 10 Franchise Companies added")
        print("   • 10 Entrepreneurs added")
        print("\n🌐 Visit http://localhost:8000/recommendations to see AI-powered matches!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please make sure the application is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
