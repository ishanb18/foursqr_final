from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
import uvicorn
from typing import List, Dict, Any, Optional
import uuid
from contextlib import asynccontextmanager

from config import Config
from models import (
    PropertyOwner, FranchiseCompany, Entrepreneur, 
    UserType, EntrepreneurType, LocationData, MatchResult
)
from foursquare_api import FoursquareAPI
from ai_service import AIService

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI application"""
    # Startup
    global property_owners, franchise_companies, entrepreneurs
    property_owners.clear()
    franchise_companies.clear()
    entrepreneurs.clear()
    print("🔄 Application startup: All previous data cleared for fresh start")
    yield
    # Shutdown
    print("🔄 Application shutdown: Cleaning up resources")

app = FastAPI(title=Config.APP_NAME, debug=Config.DEBUG, lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
foursquare_api = FoursquareAPI()
ai_service = AIService()

# In-memory storage (replace with database in production)
# Initialize empty storage - ensures fresh start each time server restarts
property_owners = {}
franchise_companies = {}
entrepreneurs = {}

# Clear any existing data on startup to ensure fresh state
print("🔄 Starting fresh - clearing any existing data...")
property_owners.clear()
franchise_companies.clear()
entrepreneurs.clear()
print("✅ All previous data cleared. Starting with empty database.")

# Templates for web interface
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with user registration options"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations(request: Request):
    return templates.TemplateResponse("recommendations.html", {"request": request})

@app.post("/api/users/property-owner", response_model=Dict[str, Any])
async def register_property_owner(property_owner: PropertyOwner):
    """Register a new property owner with dynamic location and AI analysis"""
    try:
        # Create managed user in Foursquare
        user_data = {
            "name": property_owner.name,
            "email": property_owner.email,
            "phone": property_owner.phone
        }
        
        foursquare_user = foursquare_api.create_managed_user(user_data)
        property_owner.user_id = foursquare_user.get("id", str(uuid.uuid4()))
        property_owner.access_token = foursquare_user.get("access_token")
        
        # Get location data from pincode if available
        location = property_owner.property_details.get("location", {})
        pincode = location.get("pincode")
        
        if pincode:
            # Convert pincode to location coordinates using Foursquare API
            location_data = foursquare_api.get_location_from_pincode(pincode)
            
            if location_data is not None:
                # Update property details with accurate location data
                property_owner.property_details["location"].update({
                    "latitude": location_data.latitude,
                    "longitude": location_data.longitude,
                    "address": location_data.address,
                    "city": location_data.city,
                    "state": location_data.state,
                    "country": location_data.country,
                    "pincode": pincode
                })
                print(f"✅ Location found for property owner {property_owner.name}: {location_data.city}, {location_data.state}")
            else:
                print(f"⚠️  Could not find location for pincode: {pincode}")
        
        # Store in memory
        property_owners[property_owner.user_id] = property_owner
        
        # Get dynamic market insights and AI analysis
        market_insights = None
        ai_analysis = None
        
        # Get the updated location data after pincode conversion
        updated_location = property_owner.property_details.get("location", {})
        
        if updated_location and updated_location.get("latitude") and updated_location.get("longitude"):
            try:
                # Ensure all required fields are present for LocationData
                location_data_dict = {
                    "latitude": updated_location.get("latitude"),
                    "longitude": updated_location.get("longitude"),
                    "address": updated_location.get("address", ""),
                    "city": updated_location.get("city", ""),
                    "state": updated_location.get("state", ""),
                    "country": updated_location.get("country", ""),
                    "pincode": updated_location.get("pincode")
                }
                
                # Get real market data from Foursquare API using converted coordinates
                market_insights = foursquare_api.analyze_market_insights(
                    LocationData(**location_data_dict)
                )
                
                # Get AI-powered property analysis
                ai_analysis = ai_service.analyze_property_market(
                    property_owner, market_insights.model_dump()
                )
                
                print(f"✅ Market analysis completed for {property_owner.name} in {updated_location.get('city', 'Unknown')}")
                print(f"   Using coordinates: {updated_location.get('latitude')}, {updated_location.get('longitude')}")
                
            except Exception as e:
                print(f"⚠️  Error getting market insights for {property_owner.name}: {e}")
                # Set default values when market insights fail
                market_insights = None
                ai_analysis = None
        else:
            print(f"⚠️  No valid coordinates available for {property_owner.name} after pincode conversion")
        
        return {
            "user_id": property_owner.user_id,
            "message": "Property owner registered successfully",
            "location_found": location_data is not None if pincode else None,
            "pincode_converted": pincode is not None,
            "coordinates_available": updated_location.get("latitude") is not None and updated_location.get("longitude") is not None,
            "location_data": {
                "pincode": pincode,
                "city": updated_location.get("city", "Unknown"),
                "state": updated_location.get("state", "Unknown"),
                "coordinates": f"{updated_location.get('latitude', 0)}, {updated_location.get('longitude', 0)}" if updated_location.get("latitude") else None
            },
            "market_analysis": ai_analysis,
            "market_insights": market_insights.model_dump() if market_insights else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/users/franchise-company", response_model=Dict[str, Any])
async def register_franchise_company(franchise_company: FranchiseCompany):
    """Register a new franchise company"""
    try:
        # Convert pincode to location coordinates if provided
        location_data = None
        pincode = franchise_company.franchise_requirements.get("pincode")
        if pincode:
            location_data = foursquare_api.get_location_from_pincode(pincode)
            
            if location_data is not None:
                # Add location data to franchise requirements
                franchise_company.franchise_requirements["location_data"] = {
                    "latitude": location_data.latitude,
                    "longitude": location_data.longitude,
                    "address": location_data.address,
                    "city": location_data.city,
                    "state": location_data.state,
                    "country": location_data.country,
                    "pincode": pincode
                }
                print(f"✅ Location found for franchise {franchise_company.company_name} pincode {pincode}: {location_data.city}, {location_data.state}")
            else:
                print(f"⚠️  Could not find location for franchise {franchise_company.company_name} pincode: {pincode}")
        
        # Create managed user in Foursquare
        user_data = {
            "name": franchise_company.company_name,
            "email": franchise_company.email,
            "phone": franchise_company.phone
        }
        
        foursquare_user = foursquare_api.create_managed_user(user_data)
        franchise_company.user_id = foursquare_user.get("id", str(uuid.uuid4()))
        franchise_company.access_token = foursquare_user.get("access_token")
        
        # Store in memory
        franchise_companies[franchise_company.user_id] = franchise_company
        
        return {
            "user_id": franchise_company.user_id,
            "message": "Franchise company registered successfully",
            "location_found": location_data is not None,
            "location_data": franchise_company.franchise_requirements.get("location_data") if location_data else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/users/entrepreneur", response_model=Dict[str, Any])
async def register_entrepreneur(entrepreneur: Entrepreneur):
    """Register a new entrepreneur"""
    try:
        # Convert pincode to location coordinates
        location_data = foursquare_api.get_location_from_pincode(entrepreneur.pincode)
        
        if location_data is not None:
            entrepreneur.location_data = LocationData(
                latitude=location_data.latitude,
                longitude=location_data.longitude,
                address=location_data.address,
                city=location_data.city,
                state=location_data.state,
                country=location_data.country,
                pincode=entrepreneur.pincode
            )
            print(f"✅ Location found for pincode {entrepreneur.pincode}: {location_data.city}, {location_data.state}")
        else:
            print(f"⚠️  Could not find location for pincode: {entrepreneur.pincode}")
        
        # Create managed user in Foursquare
        user_data = {
            "name": entrepreneur.name,
            "email": entrepreneur.email,
            "phone": entrepreneur.phone
        }
        
        foursquare_user = foursquare_api.create_managed_user(user_data)
        entrepreneur.user_id = foursquare_user.get("id", str(uuid.uuid4()))
        entrepreneur.access_token = foursquare_user.get("access_token")
        
        # Store in memory
        entrepreneurs[entrepreneur.user_id] = entrepreneur
        
        return {
            "user_id": entrepreneur.user_id,
            "message": "Entrepreneur registered successfully",
            "location_found": entrepreneur.location_data is not None,
            "location_data": entrepreneur.location_data.model_dump() if entrepreneur.location_data and hasattr(entrepreneur.location_data, 'model_dump') else entrepreneur.location_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/property-owners/{user_id}/recommendations")
async def get_property_recommendations(user_id: str):
    """Get dynamic recommendations for a property owner using real market data"""
    if user_id not in property_owners:
        raise HTTPException(status_code=404, detail="Property owner not found")
    
    property_owner = property_owners[user_id]
    
    try:
        # Get location data
        location = property_owner.property_details.get("location", {})
        if not location or not location.get("latitude") or not location.get("longitude"):
            raise HTTPException(status_code=400, detail="Valid location data not available")
        
        # Get real-time market insights from Foursquare API
        market_insights = foursquare_api.analyze_market_insights(
            LocationData(**location)
        )
        
        # Get AI-powered property analysis
        ai_analysis = ai_service.analyze_property_market(
            property_owner, market_insights.model_dump()
        )
        
        # Find matching franchise companies using AI
        matching_franchises = []
        for franchise in franchise_companies.values():
            match_result = ai_service.match_property_with_franchise(
                property_owner, franchise, market_insights.model_dump()
            )
            if match_result.match_score > 0.6:  # Only show good matches
                matching_franchises.append({
                    "franchise": franchise.model_dump(),
                    "match_score": match_result.match_score,
                    "reasoning": match_result.reasoning
                })
        
        # Find matching entrepreneurs for this property
        matching_entrepreneurs = []
        for entrepreneur in entrepreneurs.values():
            # Check if entrepreneur can afford this property
            prop_size = property_owner.property_details.get("area_sqft", 0)
            estimated_value = prop_size * 10000  # Base calculation
            
            # Use rent/price data if available for better estimation
            current_rent = property_owner.property_details.get("current_rent")
            asking_price = property_owner.property_details.get("asking_price")
            
            if current_rent:
                estimated_value = current_rent * 12 * 20  # 20x annual rent
            elif asking_price:
                estimated_value = asking_price
            
            # Safely get entrepreneur budget
            try:
                entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
            except (ValueError, TypeError):
                entrepreneur_budget = 0
            
            # Check if entrepreneur has enough budget (30% down payment)
            if entrepreneur_budget >= estimated_value * 0.3:
                # Calculate match score based on entrepreneur type and property type
                match_score = 0.5  # Base score
                
                # Property type preference
                prop_type = property_owner.property_details.get("property_type", "")
                if entrepreneur.entrepreneur_type in ["investor", EntrepreneurType.INVESTOR]:
                    if prop_type in ["commercial", "retail"]:
                        match_score += 0.2  # Investors prefer commercial properties
                elif entrepreneur.entrepreneur_type in ["idea_owner", EntrepreneurType.IDEA_OWNER]:
                    if prop_type in ["office", "commercial"]:
                        match_score += 0.2  # Idea owners prefer office spaces
                
                # Budget compatibility
                if entrepreneur_budget >= estimated_value * 0.5:
                    match_score += 0.2  # Higher budget = better match
                
                # Location proximity (if entrepreneur has pincode)
                if entrepreneur.pincode:
                    import math
                    # Convert entrepreneur pincode to coordinates
                    ent_location = foursquare_api.get_location_from_pincode(entrepreneur.pincode)
                    if ent_location:
                        ent_lat, ent_lon = ent_location.latitude, ent_location.longitude
                        prop_lat, prop_lon = location.get("latitude"), location.get("longitude")
                        
                        # Only calculate distance if both locations have valid coordinates
                        if prop_lat is not None and prop_lon is not None and ent_lat is not None and ent_lon is not None:
                            try:
                                prop_lat = float(prop_lat)
                                prop_lon = float(prop_lon)
                                ent_lat = float(ent_lat)
                                ent_lon = float(ent_lon)
                                
                                # Calculate distance
                                distance = math.sqrt((prop_lat-ent_lat)**2 + (prop_lon-ent_lon)**2) * 111  # Rough km
                                if distance < 50:  # Within 50km
                                    match_score += 0.1
                            except (ValueError, TypeError):
                                # Skip distance bonus if coordinates are invalid
                                pass
                
                if match_score >= 0.4:  # Show matches with reasonable compatibility
                    matching_entrepreneurs.append({
                        "entrepreneur": entrepreneur.model_dump(),
                        "match_score": min(match_score, 1.0),
                        "reasoning": f"Budget compatible (₹{(entrepreneur_budget or 0):,.0f}), {entrepreneur.entrepreneur_type} type, estimated property value ₹{(estimated_value or 0):,.0f}"
                    })
        
        # Sort by match score
        matching_franchises.sort(key=lambda x: x["match_score"], reverse=True)
        matching_entrepreneurs.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Get dynamic property pricing suggestions
        suggested_price = foursquare_api.suggest_property_price(
            LocationData(**location),
            property_owner.property_details.get("property_type", "commercial"),
            property_owner.property_details.get("area_sqft", 1000)
        )
        
        return {
            "property_owner": property_owner.model_dump(),
            "market_insights": market_insights.model_dump(),
            "ai_analysis": ai_analysis,
            "matching_franchises": matching_franchises[:5],
            "matching_entrepreneurs": matching_entrepreneurs[:5],
            "suggested_price": suggested_price,
            "location_data": {
                "city": location.get("city", "Unknown"),
                "state": location.get("state", "Unknown"),
                "pincode": location.get("pincode", "Unknown")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/franchise-companies/{user_id}/matches")
async def get_franchise_matches(user_id: str):
    """Get matching properties and entrepreneurs for a franchise company"""
    if user_id not in franchise_companies:
        raise HTTPException(status_code=404, detail="Franchise company not found")
    
    franchise_company = franchise_companies[user_id]
    
    try:
        # Find matching properties
        matching_properties = []
        for property_owner in property_owners.values():
            location = property_owner.property_details.get("location", {})
            if location:
                market_insights = foursquare_api.analyze_market_insights(
                    LocationData(**location)
                )
                match_result = ai_service.match_property_with_franchise(
                    property_owner, franchise_company, market_insights.model_dump()
                )
                if match_result.match_score > 0.4:
                    matching_properties.append({
                        "property": property_owner.model_dump(),
                        "match_score": match_result.match_score,
                        "reasoning": match_result.reasoning
                    })
        
        # Find matching entrepreneurs
        matching_entrepreneurs = []
        for entrepreneur in entrepreneurs.values():
            # Check if entrepreneur can afford this franchise
            franchise_investment = franchise_company.franchise_requirements.get("investment_required", 0)
            franchise_category = franchise_company.franchise_requirements.get("category", "")
            
            # Safely get entrepreneur budget
            try:
                entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
            except (ValueError, TypeError):
                entrepreneur_budget = 0
            
            if entrepreneur_budget >= franchise_investment:
                match_score = 0.6  # Base score
                
                # Category preference based on entrepreneur type
                if entrepreneur.entrepreneur_type in ["investor", EntrepreneurType.INVESTOR]:
                    if franchise_category in ["food_beverage", "retail"]:
                        match_score += 0.2  # Investors prefer proven categories
                elif entrepreneur.entrepreneur_type in ["idea_owner", EntrepreneurType.IDEA_OWNER]:
                    if franchise_category in ["services", "healthcare", "education"]:
                        match_score += 0.2  # Idea owners prefer service-based businesses
                
                # Budget compatibility
                if entrepreneur_budget >= franchise_investment * 1.5:
                    match_score += 0.2  # Extra budget for operations
                
                # Location preference (if entrepreneur has pincode)
                if entrepreneur.pincode:
                    # Add location-based scoring if franchise has location requirements
                    match_score += 0.1
                
                if match_score >= 0.4:  # Show matches with reasonable compatibility
                    matching_entrepreneurs.append({
                        "entrepreneur": entrepreneur.model_dump(),
                        "match_score": min(match_score, 1.0),
                        "reasoning": f"Budget compatible (₹{(entrepreneur_budget or 0):,.0f}), {entrepreneur.entrepreneur_type} type, franchise investment ₹{(franchise_investment or 0):,.0f}"
                    })
        
        # Sort by match score
        matching_properties.sort(key=lambda x: x["match_score"], reverse=True)
        matching_entrepreneurs.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "franchise_company": franchise_company.model_dump(),
            "matching_properties": matching_properties[:5],
            "matching_entrepreneurs": matching_entrepreneurs[:5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entrepreneurs/{user_id}/opportunities")
async def get_entrepreneur_opportunities(user_id: str):
    """Get business opportunities for an entrepreneur"""
    if user_id not in entrepreneurs:
        raise HTTPException(status_code=404, detail="Entrepreneur not found")
    
    entrepreneur = entrepreneurs[user_id]
    
    try:
        # Get business ideas if entrepreneur has a business idea
        business_ideas = []
        if entrepreneur.business_idea:
            # Get location from preferences or use default
            location = entrepreneur.investment_preferences.get("location", {}) if entrepreneur.investment_preferences else {}
            if location:
                business_ideas = ai_service.suggest_business_ideas(
                    location, entrepreneur.budget, entrepreneur.entrepreneur_type
                )
        
        # Find matching properties
        matching_properties = []
        for property_owner in property_owners.values():
            # Check if entrepreneur type is investor or both (using string comparison for flexibility)
            if entrepreneur.entrepreneur_type in ["investor", "both", EntrepreneurType.INVESTOR, EntrepreneurType.BOTH]:
                location = property_owner.property_details.get("location", {})
                if location:
                    market_insights = foursquare_api.analyze_market_insights(
                        LocationData(**location)
                    )
                    match_result = ai_service.match_entrepreneur_with_opportunities(
                        entrepreneur, [property_owner], [], []
                    )
                    if match_result and match_result[0].match_score > 0.4:
                        matching_properties.append({
                            "property": property_owner.model_dump(),
                            "match_score": match_result[0].match_score,
                            "reasoning": match_result[0].reasoning
                        })
        
        # Find matching franchises
        matching_franchises = []
        for franchise_company in franchise_companies.values():
            # Check if entrepreneur type is investor or both (using string comparison for flexibility)
            if entrepreneur.entrepreneur_type in ["investor", "both", EntrepreneurType.INVESTOR, EntrepreneurType.BOTH]:
                match_result = ai_service.match_entrepreneur_with_opportunities(
                    entrepreneur, [], [franchise_company], []
                )
                if match_result and match_result[0].match_score > 0.4:
                    matching_franchises.append({
                        "franchise": franchise_company.model_dump(),
                        "match_score": match_result[0].match_score,
                        "reasoning": match_result[0].reasoning
                    })
        
        # Sort by match score
        matching_properties.sort(key=lambda x: x["match_score"], reverse=True)
        matching_franchises.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "entrepreneur": entrepreneur.model_dump(),
            "business_ideas": business_ideas,
            "matching_properties": matching_properties[:5],
            "matching_franchises": matching_franchises[:5]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/location/autocomplete")
async def autocomplete_location(query: str):
    """Get location autocomplete suggestions"""
    try:
        suggestions = foursquare_api.autocomplete_location(query)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/property-owners/{user_id}/contact")
async def update_property_owner_contact(user_id: str, contact_data: dict):
    """Update property owner contact information"""
    if user_id not in property_owners:
        raise HTTPException(status_code=404, detail="Property owner not found")
    
    property_owner = property_owners[user_id]
    if "email" in contact_data:
        property_owner.email = contact_data["email"]
    if "phone" in contact_data:
        property_owner.phone = contact_data["phone"]
    
    return {"message": "Contact information updated successfully"}

@app.put("/api/entrepreneurs/{user_id}/contact")
async def update_entrepreneur_contact(user_id: str, contact_data: dict):
    """Update entrepreneur contact information"""
    if user_id not in entrepreneurs:
        raise HTTPException(status_code=404, detail="Entrepreneur not found")
    
    entrepreneur = entrepreneurs[user_id]
    if "email" in contact_data:
        entrepreneur.email = contact_data["email"]
    if "phone" in contact_data:
        entrepreneur.phone = contact_data["phone"]
    
    return {"message": "Contact information updated successfully"}

@app.put("/api/franchise-companies/{user_id}/contact")
async def update_franchise_contact(user_id: str, contact_data: dict):
    """Update franchise company contact information"""
    if user_id not in franchise_companies:
        raise HTTPException(status_code=404, detail="Franchise company not found")
    
    franchise_company = franchise_companies[user_id]
    if "email" in contact_data:
        franchise_company.email = contact_data["email"]
    if "phone" in contact_data:
        franchise_company.phone = contact_data["phone"]
    
    return {"message": "Contact information updated successfully"}

@app.get("/api/location/from-pincode/{pincode}")
async def get_location_from_pincode_endpoint(pincode: str):
    """Geocode a pincode to coordinates and metadata"""
    try:
        loc = foursquare_api.get_location_from_pincode(pincode)
        if loc is None:
            raise HTTPException(status_code=404, detail="Location not found for pincode")
        # Support both Pydantic v1 and v2
        return loc.model_dump() if hasattr(loc, 'model_dump') else loc.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/location/from-text")
async def get_location_from_text(query: str):
    """Geocode from free-text (address/city)."""
    try:
        results = foursquare_api.autocomplete_location(query)
        if results:
            first = results[0]
            geo = first.get("geo", {})
            center = geo.get("center", {})
            return {
                "latitude": center.get("latitude", 0),
                "longitude": center.get("longitude", 0),
                "address": first.get("name", ""),
                "city": first.get("name", "").split(",")[0] if first.get("name") else "",
                "state": "",
                "country": geo.get("cc", ""),
            }
        # Fallback empty
        raise HTTPException(status_code=404, detail="Location not found for text query")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/overview/property-owner/{user_id}")
async def overview_property_owner(user_id: str):
    """Return a single property owner's overview with dynamic market analysis."""
    if user_id not in property_owners:
        raise HTTPException(status_code=404, detail="Property owner not found")
    owner = property_owners[user_id]
    try:
        location = owner.property_details.get("location", {})
        insights = None
        ai_analysis = None
        
        # Only analyze if we have valid location data
        if location and location.get("latitude") and location.get("longitude"):
            try:
                print(f"🔍 Getting market insights for {owner.name} at {location.get('city', 'Unknown')}")
                
                # Get nearby businesses using enhanced search strategies (same as entrepreneurs)
                nearby_businesses = []
                
                # Strategy 1: Search for restaurants
                try:
                    restaurants = foursquare_api.search_places(
                        query="restaurant",
                        location={"latitude": location.get("latitude", 0), "longitude": location.get("longitude", 0)},
                        radius=5000
                    )
                    nearby_businesses.extend(restaurants)
                    print(f"🍽️  Found {len(restaurants)} restaurants")
                except Exception as e:
                    print(f"⚠️  Restaurant search failed: {e}")
                
                # Strategy 2: Search for general businesses if restaurant search failed
                if len(nearby_businesses) < 5:
                    try:
                        businesses = foursquare_api.search_places(
                            query="",
                            location={"latitude": location.get("latitude", 0), "longitude": location.get("longitude", 0)},
                            radius=10000
                        )
                        nearby_businesses.extend(businesses)
                        print(f"🏢 Found {len(businesses)} general businesses")
                    except Exception as e:
                        print(f"⚠️  General business search failed: {e}")
                
                # Strategy 3: Search by city name if coordinate search failed
                if len(nearby_businesses) < 5 and location.get('city'):
                    try:
                        city_businesses = foursquare_api.search_places(
                            query="",
                            location={"city": location.get('city')},
                            radius=15000
                        )
                        nearby_businesses.extend(city_businesses)
                        print(f"🏙️  Found {len(city_businesses)} city businesses")
                    except Exception as e:
                        print(f"⚠️  City search failed: {e}")
                
                # Remove duplicates based on place_id
                unique_businesses = []
                seen_ids = set()
                for business in nearby_businesses:
                    business_id = getattr(business, 'place_id', None) or getattr(business, 'fsq_id', None)
                    if business_id and business_id not in seen_ids:
                        unique_businesses.append(business)
                        seen_ids.add(business_id)
                    elif not business_id:
                        unique_businesses.append(business)
                
                nearby_businesses = unique_businesses
                print(f"✅ Total unique nearby businesses: {len(nearby_businesses)}")
                
                # Create enhanced market insights using the nearby businesses
                if nearby_businesses:
                    # Calculate market insights manually using the enhanced data
                    total_businesses = len(nearby_businesses)
                    categories = {}
                    total_rating = 0
                    rated_businesses = 0
                    total_popularity = 0
                    businesses_with_popularity = 0
                    
                    for business in nearby_businesses:
                        if business.category:
                            categories[business.category] = categories.get(business.category, 0) + 1
                        
                        if business.rating is not None:
                            total_rating += business.rating
                            rated_businesses += 1
                        
                        if business.popularity_score is not None:
                            total_popularity += business.popularity_score
                            businesses_with_popularity += 1
                    
                    # Determine demand categories
                    demand_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
                    demand_categories = [cat[0] for cat in demand_categories]
                    
                    # Calculate averages
                    avg_rating = total_rating / rated_businesses if rated_businesses > 0 else 0
                    avg_popularity = total_popularity / businesses_with_popularity if businesses_with_popularity > 0 else 0
                    
                    # Determine competition level
                    if total_businesses < 10:
                        competition_level = "Low"
                    elif total_businesses < 30:
                        competition_level = "Medium"
                    else:
                        competition_level = "High"
                    
                    # Calculate foot traffic score
                    foot_traffic_score = 0.0
                    if avg_rating > 0:
                        foot_traffic_score += (avg_rating / 5.0) * 0.4
                    if avg_popularity > 0:
                        normalized_popularity = min(avg_popularity / 100.0, 1.0)
                        foot_traffic_score += normalized_popularity * 0.3
                    if total_businesses > 0:
                        density_score = min(total_businesses / 50.0, 1.0)
                        foot_traffic_score += density_score * 0.3
                    foot_traffic_score = min(foot_traffic_score, 1.0)
                    
                    # Estimate average rent
                    base_rent = 50000
                    if competition_level == "High":
                        avg_rent = base_rent * 1.5
                    elif competition_level == "Medium":
                        avg_rent = base_rent * 1.2
                    else:
                        avg_rent = base_rent * 0.8
                    
                    foot_traffic_adjustment = 1 + (foot_traffic_score * 0.5)
                    avg_rent = avg_rent * foot_traffic_adjustment
                    
                    # Create enhanced market insights
                    enhanced_insights = {
                        "location": location,
                        "average_rent": avg_rent,
                        "foot_traffic_score": foot_traffic_score,
                        "competition_level": competition_level,
                        "demand_categories": demand_categories,
                        "market_trends": {
                            "total_businesses": total_businesses,
                            "average_rating": avg_rating,
                            "average_popularity": avg_popularity,
                            "top_categories": demand_categories
                        }
                    }
                    
                    insights = enhanced_insights
                else:
                    # Fallback to original method if no businesses found
                    market_insights = foursquare_api.analyze_market_insights(
                        LocationData(**location)
                    )
                    insights = market_insights.model_dump()
                
                # Get AI-powered property analysis
                ai_analysis = ai_service.analyze_property_market(owner, insights)
                
                print(f"✅ Enhanced overview analysis completed for {owner.name} in {location.get('city', 'Unknown')}")
                
            except Exception as e:
                print(f"⚠️  Error getting overview for {owner.name}: {e}")
        
        return {
            "user_id": user_id,
            "name": owner.name,
            "property_details": owner.property_details,
            "ai_analysis": ai_analysis,
            "market_insights": insights,
            "location_valid": bool(location and location.get("latitude") and location.get("longitude"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/overview/entrepreneur/{user_id}")
async def overview_entrepreneur(user_id: str):
    """Return a single entrepreneur overview item with targeted computations."""
    if user_id not in entrepreneurs:
        raise HTTPException(status_code=404, detail="Entrepreneur not found")
    ent = entrepreneurs[user_id]
    try:
        # Prepare AI business ideas
        business_ideas = []
        location_dict = ent.location_data.model_dump() if ent.location_data and hasattr(ent.location_data, 'model_dump') else (ent.location_data.model_dump() if ent.location_data else None)
        if ent.budget and location_dict:
            try:
                # Get nearby businesses using enhanced search strategies
                print(f"🔍 Searching for nearby businesses for {ent.name} at {location_dict.get('city', 'Unknown')}")
                
                # Try multiple search strategies to get nearby businesses
                nearby_businesses = []
                
                # Strategy 1: Search for restaurants
                try:
                    restaurants = foursquare_api.search_places(
                    query="restaurant",
                    location={"latitude": location_dict.get("latitude", 0), "longitude": location_dict.get("longitude", 0)},
                    radius=5000
                )
                    nearby_businesses.extend(restaurants)
                    print(f"🍽️  Found {len(restaurants)} restaurants")
                except Exception as e:
                    print(f"⚠️  Restaurant search failed: {e}")
                
                # Strategy 2: Search for general businesses if restaurant search failed
                if len(nearby_businesses) < 5:
                    try:
                        businesses = foursquare_api.search_places(
                            query="",
                            location={"latitude": location_dict.get("latitude", 0), "longitude": location_dict.get("longitude", 0)},
                            radius=10000
                        )
                        nearby_businesses.extend(businesses)
                        print(f"🏢 Found {len(businesses)} general businesses")
                    except Exception as e:
                        print(f"⚠️  General business search failed: {e}")
                
                # Strategy 3: Search by city name if coordinate search failed
                if len(nearby_businesses) < 5 and location_dict.get('city'):
                    try:
                        city_businesses = foursquare_api.search_places(
                            query="",
                            location={"city": location_dict.get('city')},
                            radius=15000
                        )
                        nearby_businesses.extend(city_businesses)
                        print(f"🏙️  Found {len(city_businesses)} city businesses")
                    except Exception as e:
                        print(f"⚠️  City search failed: {e}")
                
                # Remove duplicates based on place_id
                unique_businesses = []
                seen_ids = set()
                for business in nearby_businesses:
                    business_id = getattr(business, 'place_id', None) or getattr(business, 'fsq_id', None)
                    if business_id and business_id not in seen_ids:
                        unique_businesses.append(business)
                        seen_ids.add(business_id)
                    elif not business_id:
                        unique_businesses.append(business)
                
                nearby_businesses = unique_businesses
                print(f"✅ Total unique nearby businesses: {len(nearby_businesses)}")
                
            except Exception as e:
                print(f"⚠️  Error getting nearby businesses: {e}")
                nearby_businesses = []
            business_ideas = ai_service.generate_ai_business_ideas(
                location=location_dict,
                budget=ent.budget,
                entrepreneur_type=ent.entrepreneur_type,
                nearby_businesses=nearby_businesses,
                business_idea=ent.business_idea
            )

        # Simple matches (reusing logic lightly)
        matching_properties = []
        for prop_owner in property_owners.values():
            prop_location = prop_owner.property_details.get("location", {})
            prop_size = prop_owner.property_details.get("area_sqft", 0)
            # Calculate estimated value using market insights
            try:
                prop_location = prop_owner.property_details.get("location", {})
                if prop_location and prop_location.get("latitude") and prop_location.get("longitude"):
                    # Ensure all required fields are present for LocationData
                    location_data_dict = {
                        "latitude": prop_location.get("latitude"),
                        "longitude": prop_location.get("longitude"),
                        "address": prop_location.get("address", ""),
                        "city": prop_location.get("city", ""),
                        "state": prop_location.get("state", ""),
                        "country": prop_location.get("country", ""),
                        "pincode": prop_location.get("pincode")
                    }
                    
                    market_insights = foursquare_api.analyze_market_insights(
                        LocationData(**location_data_dict)
                    )
                    
                    # Use market data for valuation
                    base_value = prop_size * 10000  # Base ₹10,000 per sq ft
                    
                    # Adjust based on market competition
                    if market_insights.competition_level == "Low":
                        competition_multiplier = 0.8
                    elif market_insights.competition_level == "Medium":
                        competition_multiplier = 1.0
                    else:  # High competition
                        competition_multiplier = 1.3
                    
                    # Adjust based on foot traffic
                    foot_traffic_score = market_insights.foot_traffic_score or 0.0
                    foot_traffic_multiplier = 1 + (foot_traffic_score * 0.5)
                    
                    # Use rent/price data if available
                    current_rent = prop_owner.property_details.get("current_rent")
                    asking_price = prop_owner.property_details.get("asking_price")
                    
                    if current_rent:
                        rent_based_value = current_rent * 12 * 20  # 20x annual rent
                        estimated_value = max(base_value * competition_multiplier * foot_traffic_multiplier, rent_based_value)
                    elif asking_price:
                        estimated_value = asking_price
                    else:
                        estimated_value = base_value * competition_multiplier * foot_traffic_multiplier
                else:
                    estimated_value = prop_size * 10000
            except Exception as e:
                print(f"Error calculating property value for {prop_owner.name}: {e}")
                estimated_value = prop_size * 10000
            if ent.budget and ent.budget >= estimated_value * 0.3:
                matching_properties.append({
                    "property_owner": {
                        "name": prop_owner.name,
                        "property_details": prop_owner.property_details
                    },
                    "match_score": 0.6,
                    "nearby_businesses": 0,
                    "estimated_value": estimated_value
                })

        return {
            "user_id": user_id,
            "name": ent.name,
            "entrepreneur_type": ent.entrepreneur_type,
            "budget": ent.budget,
            "pincode": ent.pincode,
            "location_data": ent.location_data.model_dump() if ent.location_data and hasattr(ent.location_data, 'model_dump') else ent.location_data,
            "ai_business_ideas": business_ideas[:4],
            "matching_properties": matching_properties[:3],
            "matching_franchises": [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/overview/property-owner")
async def overview_property_owner_post(owner: PropertyOwner):
    """Compute overview payload for a provided property owner object with dynamic analysis.
    Also stores it in memory (upsert) to improve subsequent GETs.
    """
    # upsert into memory if user_id present
    if owner.user_id:
        property_owners[owner.user_id] = owner
    try:
        insights = None
        ai_analysis = None
        location = owner.property_details.get("location", {}) if isinstance(owner.property_details, dict) else {}
        
        # Only analyze if we have valid location data
        if location and location.get("latitude") and location.get("longitude"):
            try:
                # Ensure all required fields are present for LocationData
                location_data_dict = {
                    "latitude": location.get("latitude"),
                    "longitude": location.get("longitude"),
                    "address": location.get("address", ""),
                    "city": location.get("city", ""),
                    "state": location.get("state", ""),
                    "country": location.get("country", ""),
                    "pincode": location.get("pincode")
                }
                
                # Get real-time market insights from Foursquare API
                market_insights = foursquare_api.analyze_market_insights(
                    LocationData(**location_data_dict)
                )
                insights = market_insights.model_dump()
                
                # Get AI-powered property analysis
                ai_analysis = ai_service.analyze_property_market(owner, insights)
                
                print(f"✅ POST overview analysis completed for {owner.name} in {location.get('city', 'Unknown')}")
                
            except Exception as e:
                print(f"⚠️  Error getting POST overview for {owner.name}: {e}")
                # Set default values when analysis fails
                insights = None
                ai_analysis = None
        
        # Find matching entrepreneurs and franchises
        matching_entrepreneurs = []
        matching_franchises = []
        
        try:
            # Find matching entrepreneurs
            for entrepreneur in entrepreneurs.values():
                # Check if entrepreneur can afford this property
                prop_size = owner.property_details.get("area_sqft", 0)
                estimated_value = prop_size * 10000  # Base calculation
                
                # Use rent/price data if available for better estimation
                current_rent = owner.property_details.get("current_rent")
                asking_price = owner.property_details.get("asking_price")
                
                if current_rent:
                    estimated_value = current_rent * 12 * 20  # 20x annual rent
                elif asking_price:
                    estimated_value = asking_price
                
                # Safely get entrepreneur budget
                try:
                    entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
                except (ValueError, TypeError):
                    entrepreneur_budget = 0
                
                # Check if entrepreneur has enough budget (30% down payment)
                if entrepreneur_budget >= estimated_value * 0.3:
                    # Calculate match score based on entrepreneur type and property type
                    match_score = 0.5  # Base score
                    
                    # Property type preference
                    prop_type = owner.property_details.get("property_type", "")
                    if entrepreneur.entrepreneur_type in ["investor", EntrepreneurType.INVESTOR]:
                        if prop_type in ["commercial", "retail"]:
                            match_score += 0.2  # Investors prefer commercial properties
                    elif entrepreneur.entrepreneur_type in ["idea_owner", EntrepreneurType.IDEA_OWNER]:
                        if prop_type in ["office", "commercial"]:
                            match_score += 0.2  # Idea owners prefer office spaces
                    
                    # Location match (same pincode gets bonus)
                    if entrepreneur.pincode == owner.property_details.get("location", {}).get("pincode"):
                        match_score += 0.1
                    
                    if match_score > 0.6:
                        matching_entrepreneurs.append({
                            "entrepreneur": entrepreneur.model_dump(),
                            "match_score": match_score,
                            "reasoning": f"Budget compatible (₹{entrepreneur_budget:,.0f}), {entrepreneur.entrepreneur_type} type, estimated property value ₹{estimated_value:,.0f}"
                        })
            
            # Find matching franchises
            for franchise_company in franchise_companies.values():
                franchise_location = franchise_company.franchise_requirements.get("location_data", {})
                if franchise_location:
                    # Check if franchise location matches property location
                    franchise_pincode = franchise_location.get("pincode")
                    property_pincode = owner.property_details.get("location", {}).get("pincode")
                    
                    if franchise_pincode == property_pincode:
                        # Calculate match score based on property size and franchise requirements
                        prop_size = owner.property_details.get("area_sqft", 0)
                        franchise_area = franchise_company.franchise_requirements.get("area_size", 0)
                        
                        if prop_size >= franchise_area * 0.8:  # Property is suitable for franchise
                            match_score = 0.7  # Base score for location match
                            
                            # Size compatibility bonus
                            if prop_size >= franchise_area:
                                match_score += 0.1
                            
                            matching_franchises.append({
                                "franchise": franchise_company.model_dump(),
                                "match_score": match_score,
                                "reasoning": f"Location match (pincode: {franchise_pincode}), property size {prop_size} sq ft suitable for franchise requirement {franchise_area} sq ft"
                            })
            
            # Sort by match score
            matching_entrepreneurs.sort(key=lambda x: x["match_score"], reverse=True)
            matching_franchises.sort(key=lambda x: x["match_score"], reverse=True)
            
        except Exception as e:
            print(f"⚠️  Error finding matches for property: {e}")
        
        payload = {
            "user_id": owner.user_id,
            "name": owner.name,
            "property_details": owner.property_details,
            "ai_analysis": ai_analysis,
            "market_insights": insights,
            "location_valid": bool(location and location.get("latitude") and location.get("longitude")),
            "matching_entrepreneurs": matching_entrepreneurs[:5],
            "matching_franchises": matching_franchises[:5]
        }
        
        try:
            if owner.user_id:
                property_owners[owner.user_id] = owner
        except Exception:
            pass
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/overview/entrepreneur")
async def overview_entrepreneur_post(ent: Entrepreneur):
    """Compute overview for a provided entrepreneur object.
    Also stores it in memory (upsert) to improve subsequent GETs.
    """
    if ent.user_id:
        entrepreneurs[ent.user_id] = ent
    try:
        business_ideas = []
        location_dict = ent.location_data.model_dump() if ent.location_data and hasattr(ent.location_data, 'model_dump') else (ent.location_data.model_dump() if ent.location_data else None)
        if ent.budget and location_dict:
            try:
                print(f"🔍 Searching for nearby businesses in {location_dict.get('city', 'Unknown')}, {location_dict.get('state', 'Unknown')}")
                
                # Try multiple search strategies to get nearby businesses
                nearby_businesses = []
                
                # Strategy 1: Search for restaurants
                try:
                    restaurants = foursquare_api.search_places(
                    query="restaurant",
                    location={"latitude": location_dict.get("latitude", 0), "longitude": location_dict.get("longitude", 0)},
                    radius=5000
                )
                    nearby_businesses.extend(restaurants)
                    print(f"🍽️  Found {len(restaurants)} restaurants")
                except Exception as e:
                    print(f"⚠️  Restaurant search failed: {e}")
                
                # Strategy 2: Search for general businesses if restaurant search failed
                if len(nearby_businesses) < 5:
                    try:
                        businesses = foursquare_api.search_places(
                            query="",
                            location={"latitude": location_dict.get("latitude", 0), "longitude": location_dict.get("longitude", 0)},
                            radius=10000
                        )
                        nearby_businesses.extend(businesses)
                        print(f"🏢 Found {len(businesses)} general businesses")
                    except Exception as e:
                        print(f"⚠️  General business search failed: {e}")
                
                # Strategy 3: Search by city name if coordinate search failed
                if len(nearby_businesses) < 5 and location_dict.get('city'):
                    try:
                        city_businesses = foursquare_api.search_places(
                            query="",
                            location={"city": location_dict.get('city')},
                            radius=15000
                        )
                        nearby_businesses.extend(city_businesses)
                        print(f"🏙️  Found {len(city_businesses)} city businesses")
                    except Exception as e:
                        print(f"⚠️  City search failed: {e}")
                
                # Remove duplicates based on place_id
                unique_businesses = []
                seen_ids = set()
                for business in nearby_businesses:
                    business_id = getattr(business, 'place_id', None) or getattr(business, 'fsq_id', None)
                    if business_id and business_id not in seen_ids:
                        unique_businesses.append(business)
                        seen_ids.add(business_id)
                    elif not business_id:
                        unique_businesses.append(business)
                
                nearby_businesses = unique_businesses
                print(f"✅ Total unique nearby businesses: {len(nearby_businesses)}")
                
            except Exception as e:
                print(f"⚠️  Error getting nearby businesses: {e}")
                nearby_businesses = []
            business_ideas = ai_service.generate_ai_business_ideas(
                location=location_dict,
                budget=ent.budget,
                entrepreneur_type=ent.entrepreneur_type,
                nearby_businesses=nearby_businesses,
                business_idea=ent.business_idea
            )

        # Find matching properties and franchises
        matching_properties = []
        matching_franchises = []
        
        try:
            # Find matching properties
            for property_owner in property_owners.values():
                # Check if entrepreneur type is investor or both
                if ent.entrepreneur_type in ["investor", "both", EntrepreneurType.INVESTOR, EntrepreneurType.BOTH]:
                    location = property_owner.property_details.get("location", {})
                    if location:
                        market_insights = foursquare_api.analyze_market_insights(
                            LocationData(**location)
                        )
                        match_result = ai_service.match_entrepreneur_with_opportunities(
                            ent, [property_owner], [], []
                        )
                        if match_result and match_result[0].match_score > 0.4:
                            matching_properties.append({
                                "property": property_owner.model_dump(),
                                "match_score": match_result[0].match_score,
                                "reasoning": match_result[0].reasoning
                            })
            
            # Find matching franchises
            for franchise_company in franchise_companies.values():
                # Check if entrepreneur type is investor or both
                if ent.entrepreneur_type in ["investor", "both", EntrepreneurType.INVESTOR, EntrepreneurType.BOTH]:
                    match_result = ai_service.match_entrepreneur_with_opportunities(
                        ent, [], [franchise_company], []
                    )
                    if match_result and match_result[0].match_score > 0.4:
                        matching_franchises.append({
                            "franchise": franchise_company.model_dump(),
                            "match_score": match_result[0].match_score,
                            "reasoning": match_result[0].reasoning
                        })
            
            # Sort by match score
            matching_properties.sort(key=lambda x: x["match_score"], reverse=True)
            matching_franchises.sort(key=lambda x: x["match_score"], reverse=True)
            
        except Exception as e:
            print(f"⚠️  Error finding matches: {e}")
        
        payload = {
            "user_id": ent.user_id,
            "name": ent.name,
            "entrepreneur_type": ent.entrepreneur_type,
            "budget": ent.budget,
            "pincode": ent.pincode,
            "location_data": ent.location_data.model_dump() if ent.location_data and hasattr(ent.location_data, 'model_dump') else ent.location_data,
            "ai_business_ideas": business_ideas[:4],
            "matching_properties": matching_properties[:5],
            "matching_franchises": matching_franchises[:5],
        }
        # Persist into in-memory store for future GETs
        try:
            if ent.user_id:
                entrepreneurs[ent.user_id] = ent
        except Exception:
            pass
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-analysis/{location}")
async def get_market_analysis(location: str):
    """Get market analysis for a location"""
    try:
        # Parse location (assuming format: "lat,lng" or address)
        if "," in location:
            lat, lng = map(float, location.split(","))
            location_data = LocationData(
                latitude=lat,
                longitude=lng,
                address="",
                city="",
                state="",
                country=""
            )
        else:
            # For address, you'd need geocoding
            raise HTTPException(status_code=400, detail="Please provide coordinates in lat,lng format")
        
        market_insights = foursquare_api.analyze_market_insights(location_data)
        market_report = ai_service.generate_market_report(location_data.model_dump())
        
        return {
            "location": location_data.model_dump(),
            "market_insights": market_insights.model_dump(),
            "market_report": market_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_platform_stats():
    """Get platform statistics"""
    return {
        "total_property_owners": len(property_owners),
        "total_franchise_companies": len(franchise_companies),
        "total_entrepreneurs": len(entrepreneurs),
        "total_users": len(property_owners) + len(franchise_companies) + len(entrepreneurs)
    }

@app.post("/api/clear-all-data")
async def clear_all_data():
    """Clear all data from memory - for testing purposes"""
    global property_owners, franchise_companies, entrepreneurs
    property_owners.clear()
    franchise_companies.clear()
    entrepreneurs.clear()
    print("🗑️ All data cleared manually via API")
    return {
        "message": "All data cleared successfully",
        "stats": {
            "total_property_owners": 0,
            "total_franchise_companies": 0,
            "total_entrepreneurs": 0,
            "total_users": 0
        }
    }

@app.post("/api/clear-browser-cache")
async def clear_browser_cache():
    """Clear browser localStorage cache - for testing purposes"""
    return {
        "message": "Browser cache cleared successfully",
        "instructions": "Please refresh the page to see the changes",
        "cache_keys_cleared": [
            "bm_overview_recommendations_v1",
            "bm_overview_recommendations_time_v1",
            "bm_overview_pending_v1"
        ]
    }

@app.get("/api/property-owners", response_model=List[Dict[str, Any]])
async def get_all_property_owners():
    """Get all registered property owners"""
    return [
        {
            "user_id": user_id,
            "name": owner.name,
            "email": owner.email,
            "phone": owner.phone,
            "property_details": owner.property_details
        }
        for user_id, owner in property_owners.items()
    ]

@app.get("/api/franchise-companies", response_model=List[Dict[str, Any]])
async def get_all_franchise_companies():
    """Get all registered franchise companies"""
    return [
        {
            "user_id": user_id,
            "company_name": company.company_name,
            "email": company.email,
            "phone": company.phone,
            "franchise_requirements": company.franchise_requirements
        }
        for user_id, company in franchise_companies.items()
    ]

@app.get("/api/entrepreneurs", response_model=List[Dict[str, Any]])
async def get_all_entrepreneurs():
    """Get all registered entrepreneurs"""
    return [
        {
            "user_id": user_id,
            "name": entrepreneur.name,
            "email": entrepreneur.email,
            "phone": entrepreneur.phone,
            "entrepreneur_type": entrepreneur.entrepreneur_type,
            "budget": entrepreneur.budget,
            "pincode": entrepreneur.pincode,
            "location_data": entrepreneur.location_data.model_dump() if entrepreneur.location_data else None,
            "business_idea": entrepreneur.business_idea
        }
        for user_id, entrepreneur in entrepreneurs.items()
    ]

@app.get("/api/recommendations/overview")
async def get_recommendations_overview(t: Optional[int] = None):
    """Get overview of all recommendations and matches with cache-busting support"""
    """Get overview of all recommendations and matches"""
    try:
        recommendations = {
            "property_owners": [],
            "franchise_companies": [],
            "entrepreneurs": [],
            "matches": []
        }
        
        # Get dynamic recommendations for each property owner using real market data
        for user_id, property_owner in property_owners.items():
            try:
                location = property_owner.property_details.get("location", {})
                
                # Only analyze if we have valid location data
                if location and location.get("latitude") and location.get("longitude"):
                    try:
                        # Ensure all required fields are present for LocationData
                        location_data_dict = {
                            "latitude": location.get("latitude"),
                            "longitude": location.get("longitude"),
                            "address": location.get("address", ""),
                            "city": location.get("city", ""),
                            "state": location.get("state", ""),
                            "country": location.get("country", ""),
                            "pincode": location.get("pincode")
                        }
                        
                        # Get real-time market insights from Foursquare API
                        market_insights = foursquare_api.analyze_market_insights(
                            LocationData(**location_data_dict)
                        )
                        
                        # Get AI-powered property analysis
                        ai_analysis = ai_service.analyze_property_market(
                            property_owner, market_insights.model_dump()
                        )
                        
                        print(f"✅ Overview analysis for {property_owner.name} in {location.get('city', 'Unknown')}")
                        
                        # Find matching entrepreneurs for this property owner
                        matching_entrepreneurs = []
                        for entrepreneur in entrepreneurs.values():
                            prop_size = property_owner.property_details.get("area_sqft", 0)
                            estimated_value = prop_size * 10000
                            
                            current_rent = property_owner.property_details.get("current_rent")
                            asking_price = property_owner.property_details.get("asking_price")
                            
                            if current_rent:
                                estimated_value = current_rent * 12 * 10  # 10 years instead of 20
                            elif asking_price:
                                estimated_value = asking_price
                            
                            # Safely get entrepreneur budget
                            try:
                                entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
                            except (ValueError, TypeError):
                                entrepreneur_budget = 0
                            
                            if entrepreneur_budget >= estimated_value * 0.15:  # Lower threshold from 30% to 15%
                                match_score = 0.5
                                prop_type = property_owner.property_details.get("property_type", "")
                                
                                if entrepreneur.entrepreneur_type == "investor" and prop_type in ["commercial", "retail"]:
                                    match_score += 0.2
                                elif entrepreneur.entrepreneur_type == "idea_owner" and prop_type in ["office", "commercial"]:
                                    match_score += 0.2
                                
                                if entrepreneur_budget >= estimated_value * 0.25:  # Lower threshold from 50% to 25%
                                    match_score += 0.2
                                
                                if match_score >= 0.4:
                                    matching_entrepreneurs.append({
                                        "entrepreneur": entrepreneur.model_dump(),
                                        "match_score": min(match_score, 1.0),
                                        "reasoning": f"Budget compatible, {entrepreneur.entrepreneur_type} type"
                                    })
                        
                        matching_entrepreneurs.sort(key=lambda x: x["match_score"], reverse=True)
                        
                        # Find matching franchise companies for this property owner
                        matching_franchises = []
                        for franchise in franchise_companies.values():
                            prop_size = property_owner.property_details.get("area_sqft", 0)
                            prop_type = property_owner.property_details.get("property_type", "")
                            franchise_area = franchise.franchise_requirements.get("area_size", 0)
                            franchise_category = franchise.franchise_requirements.get("category", "")
                            
                            # Calculate match score based on area compatibility
                            area_match = 0.0
                            if franchise_area > 0 and prop_size > 0:
                                area_ratio = min(prop_size, franchise_area) / max(prop_size, franchise_area)
                                area_match = area_ratio * 0.4
                            
                            # Calculate match score based on property type compatibility
                            type_match = 0.0
                            if prop_type in ["commercial", "retail"] and franchise_category in ["food_beverage", "retail", "services"]:
                                type_match = 0.3
                            elif prop_type == "office" and franchise_category in ["services", "education", "healthcare"]:
                                type_match = 0.3
                            elif prop_type == "industrial" and franchise_category in ["services", "healthcare"]:
                                type_match = 0.2
                            
                            # Calculate location compatibility (if both have location data)
                            location_match = 0.0
                            if location and location.get("latitude") and location.get("longitude"):
                                franchise_location = franchise.franchise_requirements.get("location", {})
                                if franchise_location and franchise_location.get("latitude") and franchise_location.get("longitude"):
                                    try:
                                        # Calculate distance between property and franchise location
                                        lat1, lon1 = float(location.get("latitude")), float(location.get("longitude"))
                                        lat2, lon2 = float(franchise_location.get("latitude")), float(franchise_location.get("longitude"))
                                        
                                        # Simple distance calculation (Haversine formula)
                                        import math
                                        R = 6371  # Earth's radius in km
                                        dlat = math.radians(lat2 - lat1)
                                        dlon = math.radians(lon2 - lon1)
                                        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
                                        c = 2 * math.asin(math.sqrt(a))
                                        distance_km = R * c
                                        
                                        # Distance bonus (closer is better)
                                        if distance_km <= 10:
                                            location_match = 0.3
                                        elif distance_km <= 25:
                                            location_match = 0.2
                                        elif distance_km <= 50:
                                            location_match = 0.1
                                    except (ValueError, TypeError):
                                        pass
                            
                            total_match_score = area_match + type_match + location_match
                            
                            if total_match_score >= 0.3:  # Minimum threshold for a match
                                matching_franchises.append({
                                    "franchise": {
                                        "company_name": franchise.company_name,
                                        "email": franchise.email,
                                        "phone": franchise.phone,
                                        "franchise_requirements": franchise.franchise_requirements
                                    },
                                    "match_score": min(total_match_score, 1.0),
                                    "reasoning": f"Area: {area_match:.1f}, Type: {type_match:.1f}, Location: {location_match:.1f}"
                                })
                        
                        matching_franchises.sort(key=lambda x: x["match_score"], reverse=True)
                        
                        recommendations["property_owners"].append({
                            "user_id": user_id,
                            "name": property_owner.name,
                            "email": property_owner.email,
                            "phone": property_owner.phone,
                            "property_details": property_owner.property_details,
                            "ai_analysis": ai_analysis,
                            "market_insights": market_insights.model_dump(),
                            "location_valid": True,
                            "matching_entrepreneurs": matching_entrepreneurs[:3],
                            "matching_franchises": matching_franchises[:3]
                        })
                    except Exception as e:
                        print(f"⚠️  Error getting market insights for {property_owner.name}: {e}")
                        # Add property owner without analysis if market insights fail
                        recommendations["property_owners"].append({
                            "user_id": user_id,
                            "name": property_owner.name,
                            "email": property_owner.email,
                            "phone": property_owner.phone,
                            "property_details": property_owner.property_details,
                            "ai_analysis": None,
                            "market_insights": None,
                            "location_valid": False,
                            "matching_entrepreneurs": [],
                            "matching_franchises": []
                        })
                else:
                    print(f"⚠️  No valid location data for {property_owner.name}")
                    # Add property owner without analysis if no location data
                    recommendations["property_owners"].append({
                        "user_id": user_id,
                        "name": property_owner.name,
                        "email": property_owner.email,
                        "phone": property_owner.phone,
                        "property_details": property_owner.property_details,
                        "ai_analysis": None,
                        "market_insights": None,
                        "location_valid": False,
                        "matching_entrepreneurs": [],
                        "matching_franchises": []
                    })
            except Exception as e:
                print(f"Error getting recommendations for property owner {user_id}: {e}")
        
        # Get enhanced recommendations for each entrepreneur using Foursquare data
        for user_id, entrepreneur in entrepreneurs.items():
            try:
                # Get business ideas based on budget and location (using Foursquare)
                business_ideas = []
                location_based_recommendations = []
                
                # Use entrepreneur's location data from pincode for better recommendations
                if entrepreneur.location_data:
                    print(f"📍 Using location data for {entrepreneur.name}: {entrepreneur.location_data.city}, {entrepreneur.location_data.state}")
                    
                    # Get nearby businesses in entrepreneur's area first
                    try:
                        # Try restaurant search first
                        nearby_businesses = foursquare_api.search_places(
                            query="restaurant",
                            location={"latitude": entrepreneur.location_data.latitude, "longitude": entrepreneur.location_data.longitude},
                            radius=5000
                        )
                        
                        # If no restaurants found, try broader business search
                        if len(nearby_businesses) == 0:
                            print(f"🍽️  No restaurants found, searching for general businesses...")
                            nearby_businesses = foursquare_api.search_places(
                                query="business",
                                location={"latitude": entrepreneur.location_data.latitude, "longitude": entrepreneur.location_data.longitude},
                                radius=10000
                            )
                        
                        # If still no results, try without query parameter
                        if len(nearby_businesses) == 0:
                            print(f"🏢 No businesses found, searching for all places...")
                            nearby_businesses = foursquare_api.search_places(
                                query="",
                                location={"latitude": entrepreneur.location_data.latitude, "longitude": entrepreneur.location_data.longitude},
                                radius=25000
                            )
                        
                        print(f"🏢 Found {len(nearby_businesses)} nearby businesses in {entrepreneur.location_data.city}")
                    except Exception as e:
                        print(f"⚠️  Error getting nearby businesses for {entrepreneur.name}: {e}")
                        nearby_businesses = []
                    
                    # Get location-specific business ideas using Foursquare data and AI analysis
                    if entrepreneur.budget > 0:
                        # Convert location_data to dict if it's a Pydantic model
                        location_dict = entrepreneur.location_data.model_dump() if hasattr(entrepreneur.location_data, 'model_dump') else entrepreneur.location_data
                        business_ideas = ai_service.generate_ai_business_ideas(
                            location=location_dict,
                            budget=entrepreneur.budget,
                            entrepreneur_type=entrepreneur.entrepreneur_type,
                            nearby_businesses=nearby_businesses,
                            business_idea=entrepreneur.business_idea
                        )
                else:
                    print(f"⚠️  No location data for {entrepreneur.name}, using budget-based recommendations only")
                    # Fallback to budget-based recommendations
                    if entrepreneur.budget > 0:
                        business_ideas = ai_service.generate_ai_business_ideas(
                            location={"budget": entrepreneur.budget},
                            budget=entrepreneur.budget,
                            entrepreneur_type=entrepreneur.entrepreneur_type,
                            nearby_businesses=[],
                            business_idea=entrepreneur.business_idea
                        )
                    nearby_businesses = []
                
                # Find matching properties with location intelligence
                matching_properties = []
                for prop_owner in property_owners.values():
                    prop_location = prop_owner.property_details.get("location", {})
                    prop_size = prop_owner.property_details.get("area_sqft", 0)
                    
                    # Calculate property value estimate using market insights and AI analysis
                    try:
                        # Get market insights for this property location
                        prop_location = prop_owner.property_details.get("location", {})
                        if prop_location and prop_location.get("latitude") and prop_location.get("longitude"):
                            # Ensure all required fields are present for LocationData
                            location_data_dict = {
                                "latitude": prop_location.get("latitude"),
                                "longitude": prop_location.get("longitude"),
                                "address": prop_location.get("address", ""),
                                "city": prop_location.get("city", ""),
                                "state": prop_location.get("state", ""),
                                "country": prop_location.get("country", ""),
                                "pincode": prop_location.get("pincode")
                            }
                            
                            market_insights = foursquare_api.analyze_market_insights(
                                LocationData(**location_data_dict)
                            )
                            
                            # Use AI analysis for property valuation
                            ai_analysis = ai_service.analyze_property_market(
                                prop_owner, market_insights.model_dump()
                            )
                            
                            # Calculate estimated value based on AI insights and market data
                            base_value = prop_size * 10000  # Base ₹10,000 per sq ft
                            
                            # Adjust based on market competition
                            if market_insights.competition_level == "Low":
                                competition_multiplier = 0.8
                            elif market_insights.competition_level == "Medium":
                                competition_multiplier = 1.0
                            else:  # High competition
                                competition_multiplier = 1.3
                            
                            # Adjust based on foot traffic
                            foot_traffic_score = market_insights.foot_traffic_score or 0.0
                            foot_traffic_multiplier = 1 + (foot_traffic_score * 0.5)
                            
                            # Use rent/price data if available
                            current_rent = prop_owner.property_details.get("current_rent")
                            asking_price = prop_owner.property_details.get("asking_price")
                            
                            if current_rent:
                                rent_based_value = current_rent * 12 * 20  # 20x annual rent
                                estimated_property_value = max(base_value * competition_multiplier * foot_traffic_multiplier, rent_based_value)
                            elif asking_price:
                                estimated_property_value = asking_price
                            else:
                                estimated_property_value = base_value * competition_multiplier * foot_traffic_multiplier
                        else:
                            # Fallback to basic calculation if no location data
                            estimated_property_value = prop_size * 10000
                    except Exception as e:
                        print(f"Error calculating property value for {prop_owner.name}: {e}")
                        # Fallback to basic calculation
                        estimated_property_value = prop_size * 10000
                    
                    # Check if entrepreneur can afford this property
                    # Safely get entrepreneur budget
                    try:
                        entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
                    except (ValueError, TypeError):
                        entrepreneur_budget = 0
                    
                    if entrepreneur_budget >= estimated_property_value * 0.15:  # 15% down payment (same as property owner matching)
                        # Get nearby businesses using Foursquare API
                        try:
                            # Only search if we have valid coordinates
                            if prop_location and prop_location.get("latitude") and prop_location.get("longitude"):
                                # Try restaurant search first
                                nearby_businesses = foursquare_api.search_places(
                                    query="restaurant",
                                    location={"latitude": prop_location.get("latitude"), "longitude": prop_location.get("longitude")},
                                    radius=5000
                                )
                                
                                # If no restaurants found, try broader business search
                                if len(nearby_businesses) == 0:
                                    nearby_businesses = foursquare_api.search_places(
                                        query="business",
                                        location={"latitude": prop_location.get("latitude"), "longitude": prop_location.get("longitude")},
                                        radius=10000
                                    )
                                
                                # If still no results, try without query parameter
                                if len(nearby_businesses) == 0:
                                    nearby_businesses = foursquare_api.search_places(
                                        query="",
                                        location={"latitude": prop_location.get("latitude"), "longitude": prop_location.get("longitude")},
                                        radius=25000
                                    )
                            else:
                                nearby_businesses = []
                            
                            # Calculate match score based on nearby businesses and entrepreneur type
                            match_score = 0.5  # Base score
                            
                            if entrepreneur.entrepreneur_type == "investor":
                                # Investors prefer areas with existing successful businesses
                                if nearby_businesses and len(nearby_businesses) > 5:
                                    match_score += 0.3
                            elif entrepreneur.entrepreneur_type == "idea_owner":
                                # Idea owners prefer areas with less competition
                                if nearby_businesses and len(nearby_businesses) < 10:
                                    match_score += 0.3
                            
                            # Budget compatibility
                            if entrepreneur_budget >= estimated_property_value * 0.5:
                                match_score += 0.2
                            
                            # Location proximity bonus (if entrepreneur has location data)
                            if entrepreneur.location_data:
                                # Calculate distance between entrepreneur and property
                                import math
                                lat1, lon1 = entrepreneur.location_data.latitude, entrepreneur.location_data.longitude
                                lat2, lon2 = prop_location.get("latitude"), prop_location.get("longitude")
                                
                                # Only calculate distance if both locations have valid coordinates
                                if lat2 is not None and lon2 is not None and lat1 is not None and lon1 is not None:
                                    try:
                                        lat2 = float(lat2)
                                        lon2 = float(lon2)
                                        lat1 = float(lat1)
                                        lon1 = float(lon1)
                                        
                                        # Simple distance calculation (Haversine formula simplified)
                                        distance = math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111  # Rough km conversion
                                        if distance < 50:  # Within 50km
                                            match_score += 0.1
                                    except (ValueError, TypeError):
                                        # Skip distance bonus if coordinates are invalid
                                        pass
                            
                            # Calculate distance for display if coordinates are valid
                            display_distance = None
                            if entrepreneur.location_data:
                                lat1, lon1 = entrepreneur.location_data.latitude, entrepreneur.location_data.longitude
                                lat2, lon2 = prop_location.get("latitude"), prop_location.get("longitude")
                                if lat2 is not None and lon2 is not None and lat1 is not None and lon1 is not None:
                                    try:
                                        lat2 = float(lat2)
                                        lon2 = float(lon2)
                                        lat1 = float(lat1)
                                        lon1 = float(lon1)
                                        display_distance = math.sqrt((lat2-lat1)**2 + (lon2-lon1)**2) * 111
                                    except (ValueError, TypeError):
                                        pass
                            
                            matching_properties.append({
                                "property_owner": {
                                    "name": prop_owner.name,
                                    "email": prop_owner.email,
                                    "phone": prop_owner.phone,
                                    "property_details": prop_owner.property_details
                                },
                                "match_score": min(match_score, 1.0),
                                "nearby_businesses": len(nearby_businesses) if nearby_businesses else 0,
                                "estimated_value": estimated_property_value,
                                "distance_km": display_distance
                            })
                        except Exception as e:
                            print(f"Error getting nearby businesses: {e}")
                            # Fallback without Foursquare data
                            matching_properties.append({
                                "property_owner": {
                                    "name": prop_owner.name,
                                    "email": prop_owner.email,
                                    "phone": prop_owner.phone,
                                    "property_details": prop_owner.property_details
                                },
                                "match_score": 0.6,
                                "nearby_businesses": 0,
                                "estimated_value": estimated_property_value
                            })
                
                # Find matching franchises with location analysis
                matching_franchises = []
                for franchise in franchise_companies.values():
                    franchise_investment = franchise.franchise_requirements.get("investment_required", 0)
                    franchise_category = franchise.franchise_requirements.get("category", "")
                    
                    # Check if entrepreneur can afford this franchise
                    # Safely get entrepreneur budget
                    try:
                        entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
                    except (ValueError, TypeError):
                        entrepreneur_budget = 0
                    
                    if entrepreneur_budget >= franchise_investment:
                        match_score = 0.6  # Base score
                        
                        # Category preference based on entrepreneur type
                        if entrepreneur.entrepreneur_type == "investor":
                            if franchise_category in ["food_beverage", "retail"]:
                                match_score += 0.2  # Investors prefer proven categories
                        elif entrepreneur.entrepreneur_type == "idea_owner":
                            if franchise_category in ["services", "healthcare", "education"]:
                                match_score += 0.2  # Idea owners prefer service-based businesses
                        
                        # Budget compatibility
                        if entrepreneur_budget >= franchise_investment * 1.5:
                            match_score += 0.2  # Extra budget for operations
                        
                        matching_franchises.append({
                            "franchise": {
                                "company_name": franchise.company_name,
                                "email": franchise.email,
                                "phone": franchise.phone,
                                "franchise_requirements": franchise.franchise_requirements
                            },
                            "match_score": min(match_score, 1.0),
                            "investment_required": franchise_investment
                        })
                
                # Sort by match score
                matching_properties.sort(key=lambda x: x["match_score"], reverse=True)
                matching_franchises.sort(key=lambda x: x["match_score"], reverse=True)
                
                recommendations["entrepreneurs"].append({
                    "user_id": user_id,
                    "name": entrepreneur.name,
                    "email": entrepreneur.email,
                    "phone": entrepreneur.phone,
                    "entrepreneur_type": entrepreneur.entrepreneur_type,
                    "budget": entrepreneur.budget,
                    "pincode": entrepreneur.pincode,
                    "location_data": entrepreneur.location_data.model_dump() if entrepreneur.location_data and hasattr(entrepreneur.location_data, 'model_dump') else entrepreneur.location_data,
                    "business_idea": entrepreneur.business_idea,
                    "ai_business_ideas": business_ideas,
                    "matching_properties": matching_properties[:3],  # Top 3 matches
                    "matching_franchises": matching_franchises[:3]   # Top 3 matches
                })
            except Exception as e:
                print(f"Error getting recommendations for entrepreneur {user_id}: {e}")
        
                # Get franchise company recommendations with location analysis
        for user_id, franchise in franchise_companies.items():
            try:
                matching_properties = []
                for prop_owner in property_owners.values():
                    prop_type = prop_owner.property_details.get("type", "")
                    franchise_category = franchise.franchise_requirements.get("category", "")
                    prop_location = prop_owner.property_details.get("location", {})
                    
                    # Simple matching logic
                    category_match = False
                    if (franchise_category == "food_beverage" and prop_type in ["commercial", "retail"]) or \
                       (franchise_category == "retail" and prop_type == "retail") or \
                       (franchise_category == "services" and prop_type in ["office", "commercial"]):
                        category_match = True
                    
                    if category_match:
                        # Get nearby businesses using Foursquare API
                        try:
                            nearby_businesses = foursquare_api.search_places(
                                query=franchise_category.replace("_", " "),
                                location={"latitude": prop_location.get("latitude", 0), "longitude": prop_location.get("longitude", 0)},
                                radius=2000
                            )
                            
                            # Calculate match score
                            match_score = 0.7  # Base score for category match
                            
                            # Competition analysis
                            if nearby_businesses:
                                competition_level = len(nearby_businesses)
                                if competition_level < 5:
                                    match_score += 0.2  # Low competition
                                elif competition_level < 15:
                                    match_score += 0.1  # Moderate competition
                                else:
                                    match_score -= 0.1  # High competition
                            
                            matching_properties.append({
                                "property_owner": {
                                    "name": prop_owner.name,
                                    "property_details": prop_owner.property_details
                                },
                                "match_score": min(match_score, 1.0),
                                "nearby_competition": len(nearby_businesses) if nearby_businesses else 0
                            })
                        except Exception as e:
                            print(f"Error getting nearby businesses for franchise: {e}")
                            # Fallback without Foursquare data
                            matching_properties.append({
                                "property_owner": {
                                    "name": prop_owner.name,
                                    "property_details": prop_owner.property_details
                                },
                                "match_score": 0.7,
                                "nearby_competition": 0
                            })
                
                # Sort by match score
                matching_properties.sort(key=lambda x: x["match_score"], reverse=True)
                
                # Find matching entrepreneurs for this franchise
                matching_entrepreneurs = []
                for entrepreneur in entrepreneurs.values():
                    franchise_investment = franchise.franchise_requirements.get("investment_required", 0)
                    franchise_category = franchise.franchise_requirements.get("category", "")
                    
                    # Safely get entrepreneur budget
                    try:
                        entrepreneur_budget = float(entrepreneur.budget) if entrepreneur.budget is not None else 0
                    except (ValueError, TypeError):
                        entrepreneur_budget = 0
                    
                    if entrepreneur_budget >= franchise_investment:
                        match_score = 0.6  # Base score
                        
                        # Category preference based on entrepreneur type
                        if entrepreneur.entrepreneur_type == "investor":
                            if franchise_category in ["food_beverage", "retail"]:
                                match_score += 0.2  # Investors prefer proven categories
                        elif entrepreneur.entrepreneur_type == "idea_owner":
                            if franchise_category in ["services", "healthcare", "education"]:
                                match_score += 0.2  # Idea owners prefer service-based businesses
                        
                        # Budget compatibility
                        if entrepreneur_budget >= franchise_investment * 1.5:
                            match_score += 0.2  # Extra budget for operations
                        
                        if match_score >= 0.6:  # Only show good matches
                            matching_entrepreneurs.append({
                                "entrepreneur": entrepreneur.model_dump(),
                                "match_score": min(match_score, 1.0),
                                "reasoning": f"Budget compatible (₹{(entrepreneur_budget or 0):,.0f}), {entrepreneur.entrepreneur_type} type"
                            })
                
                matching_entrepreneurs.sort(key=lambda x: x["match_score"], reverse=True)
                
                recommendations["franchise_companies"].append({
                    "user_id": user_id,
                    "company_name": franchise.company_name,
                    "email": franchise.email,
                    "phone": franchise.phone,
                    "franchise_requirements": franchise.franchise_requirements,
                    "matching_properties": matching_properties[:3],
                    "matching_entrepreneurs": matching_entrepreneurs[:3]
                })
            except Exception as e:
                print(f"Error getting recommendations for franchise {user_id}: {e}")
        
        # Add cache-busting headers
        import time
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=recommendations)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-Fresh-Data"] = str(int(time.time()))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
