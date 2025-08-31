from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class UserType(str, Enum):
    PROPERTY_OWNER = "property_owner"
    FRANCHISE_COMPANY = "franchise_company"
    ENTREPRENEUR = "entrepreneur"

class EntrepreneurType(str, Enum):
    INVESTOR = "investor"  # Has money, wants to invest
    IDEA_OWNER = "idea_owner"  # Has business idea
    BOTH = "both"  # Has both money and idea

class LocationData(BaseModel):
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    country: str
    pincode: Optional[str] = None

class PincodeLocation(BaseModel):
    pincode: str
    latitude: float
    longitude: float
    address: str
    city: str
    state: str
    country: str

class PropertyOwner(BaseModel):
    user_id: Optional[str] = None
    name: str
    email: str
    phone: str
    property_details: Dict[str, Any] = Field(description="Property information including location, size, price")
    rent_amount: Optional[float] = Field(None, description="Monthly rent amount in INR")
    sale_price: Optional[float] = Field(None, description="Sale price in INR")
    access_token: Optional[str] = None

class FranchiseCompany(BaseModel):
    user_id: Optional[str] = None
    company_name: str
    email: str
    phone: str
    franchise_requirements: Dict[str, Any] = Field(description="Franchise requirements including category, location, area size")
    access_token: Optional[str] = None

class Entrepreneur(BaseModel):
    user_id: Optional[str] = None
    name: str
    email: str
    phone: str
    entrepreneur_type: EntrepreneurType
    budget: float = Field(description="Budget in currency units")
    pincode: str = Field(description="Pincode/Postal code for location-based recommendations")
    business_idea: Optional[str] = None
    investment_preferences: Optional[Dict[str, Any]] = None
    location_data: Optional[LocationData] = None  # Will be populated from pincode
    access_token: Optional[str] = None

class BusinessRecommendation(BaseModel):
    place_id: str
    name: str
    category: str
    location: LocationData
    rating: Optional[float] = None
    price_tier: Optional[int] = None
    popularity_score: Optional[float] = None
    match_score: float = Field(description="How well this matches user requirements (0-1)")

class MarketInsight(BaseModel):
    location: LocationData
    average_rent: Optional[float] = None
    foot_traffic_score: Optional[float] = None
    competition_level: Optional[str] = None
    demand_categories: List[str] = []
    market_trends: Dict[str, Any] = {}

class MatchResult(BaseModel):
    property_owner: Optional[PropertyOwner] = None
    franchise_company: Optional[FranchiseCompany] = None
    entrepreneur: Optional[Entrepreneur] = None
    match_score: float
    reasoning: str
    recommendations: List[BusinessRecommendation] = []
    market_insights: Optional[MarketInsight] = None
