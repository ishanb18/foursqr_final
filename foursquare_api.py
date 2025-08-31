import requests
import json
from typing import Dict, List, Optional, Any
from config import Config
from models import LocationData, BusinessRecommendation, MarketInsight, PincodeLocation

class FoursquareAPI:
    def __init__(self, service_key: str = None):
        self.service_key = service_key or Config.FOURSQUARE_SERVICE_KEY
        self.places_base_url = Config.PLACES_API_BASE
        self.users_base_url = Config.USERS_API_BASE
        
        # Headers for API requests
        self.places_headers = {
            "Authorization": f"Bearer {self.service_key}",
            "X-Places-Api-Version": Config.FOURSQUARE_PLACES_API_VERSION,
            "Accept": "application/json"
        }
        
        self.users_headers = {
            "Authorization": f"Bearer {self.service_key}",
            "X-Users-Api-Version": Config.FOURSQUARE_USERS_API_VERSION,
            "Accept": "application/json"
        }

    def get_location_from_pincode(self, pincode: str) -> Optional[PincodeLocation]:
        """Convert pincode to location coordinates using Foursquare API geocoding"""
        try:
            # Try using Foursquare autocomplete for geocoding with different query formats
            url = f"{self.places_base_url}/autocomplete"
            
            # Try different query formats for better postal code recognition
            query_formats = [
                pincode,
                f"{pincode} India",
                f"postal code {pincode}",
                f"pincode {pincode}"
            ]
            
            for query in query_formats:
                params = {
                    "query": query,
                    "types": "geo",  # Only return geographic locations
                    "limit": 1
                }
                
                response = requests.get(url, headers=self.places_headers, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get("results") and len(data["results"]) > 0:
                    result = data["results"][0]
                    geo_data = result.get("geo", {})
                    
                    # Check if the result is actually relevant to the pincode
                    if geo_data.get("center"):
                        return PincodeLocation(
                            pincode=pincode,
                            latitude=geo_data["center"].get("latitude", 0),
                            longitude=geo_data["center"].get("longitude", 0),
                            address=geo_data.get("name", ""),
                            city=geo_data.get("name", "").split(",")[0] if geo_data.get("name") else "",
                            state=geo_data.get("name", "").split(",")[1].strip() if geo_data.get("name") and "," in geo_data.get("name") else "",
                            country=geo_data.get("cc", "")
                        )
            
            # If autocomplete doesn't work, try places search
            search_url = f"{self.places_base_url}/places/search"
            search_params = {
                "query": f"postal code {pincode} India",
                "limit": 1
            }
            
            search_response = requests.get(search_url, headers=self.places_headers, params=search_params, timeout=15)
            search_response.raise_for_status()
            search_data = search_response.json()
            
            if search_data.get("results") and len(search_data["results"]) > 0:
                place = search_data["results"][0]
                location = place.get("location", {})
                geocodes = place.get("geocodes", {})
                main_geo = geocodes.get("main", {}) or geocodes.get("roof", {})
                lat = main_geo.get("latitude", 0)
                lon = main_geo.get("longitude", 0)

                return PincodeLocation(
                    pincode=pincode,
                    latitude=lat,
                    longitude=lon,
                    address=location.get("address", ""),
                    city=location.get("locality", ""),
                    state=location.get("region", ""),
                    country=location.get("country", "")
                )
            else:
                print(f"⚠️  Could not find location for pincode: {pincode}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Network error getting location from pincode {pincode}: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Error getting location from pincode {pincode}: {e}")
            return None





    def create_managed_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a managed user for property owners, franchise companies, or entrepreneurs"""
        url = f"{self.users_base_url}/users/managed-user/create"
        
        payload = {
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "phone": user_data.get("phone", "")
        }
        
        response = requests.post(url, headers=self.users_headers, json=payload)
        response.raise_for_status()
        return response.json()

    def search_places(self, query: str, location: Optional[Dict] = None, 
                     categories: Optional[List[str]] = None, 
                     radius: int = 5000) -> List[BusinessRecommendation]:
        """Search for places using Foursquare Places API with retry logic"""
        url = f"{self.places_base_url}/places/search"
        
        params = {}
        
        # Only add query parameter if it's not empty
        if query and query.strip():
            params["query"] = query
        
        if location:
            # Try using city name for better location-based search
            city = location.get('city', '')
            if city:
                params.update({
                    "near": city
                })
                # Don't use radius with 'near' parameter (API restriction)
            else:
                # Fallback to coordinates if city not available
                lat = location.get('latitude')
                lon = location.get('longitude')
                if lat and lon:
                    # Use coordinates in the format expected by Foursquare API
                    params.update({
                        "ll": f"{lat},{lon}",
                        "radius": radius  # Only use radius with coordinates
                    })
        else:
            # If no location provided, use radius for IP-based search
            params["radius"] = radius
        
        if categories:
            params["categories"] = ",".join(categories)
        
        # Add retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.places_headers, params=params, timeout=10)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"⚠️  Foursquare API call failed after {max_retries} attempts: {e}")
                    return []
                else:
                    print(f"⚠️  Foursquare API call failed (attempt {attempt + 1}/{max_retries}): {e}")
                    import time
                    time.sleep(1)  # Wait before retry
        
        data = response.json()
        recommendations = []
        
        for place in data.get("results", []):
            geocodes = place.get("geocodes", {})
            main_geo = geocodes.get("main", {}) or geocodes.get("roof", {})
            latitude = main_geo.get("latitude", 0)
            longitude = main_geo.get("longitude", 0)

            location_data = LocationData(
                latitude=latitude,
                longitude=longitude,
                address=place.get("location", {}).get("address", ""),
                city=place.get("location", {}).get("locality", ""),
                state=place.get("location", {}).get("region", ""),
                country=place.get("location", {}).get("country", "")
            )
            
            recommendation = BusinessRecommendation(
                place_id=place.get("fsq_place_id") or place.get("fsq_id", ""),
                name=place.get("name", ""),
                category=place.get("categories", [{}])[0].get("name", "") if place.get("categories") else "",
                location=location_data,
                rating=place.get("rating"),
                price_tier=place.get("price"),
                popularity_score=place.get("popularity", 0),
                match_score=0.8  # Default match score, will be calculated by AI
            )
            recommendations.append(recommendation)
        
        return recommendations

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific place"""
        url = f"{self.places_base_url}/places/{place_id}"
        
        response = requests.get(url, headers=self.places_headers)
        response.raise_for_status()
        
        return response.json()

    def get_place_tips(self, place_id: str) -> List[Dict[str, Any]]:
        """Get tips/reviews for a specific place"""
        url = f"{self.places_base_url}/places/{place_id}/tips"
        
        response = requests.get(url, headers=self.places_headers)
        response.raise_for_status()
        
        return response.json().get("results", [])

    def get_place_photos(self, place_id: str) -> List[Dict[str, Any]]:
        """Get photos for a specific place"""
        url = f"{self.places_base_url}/places/{place_id}/photos"
        
        response = requests.get(url, headers=self.places_headers)
        response.raise_for_status()
        
        return response.json().get("results", [])

    def autocomplete_location(self, query: str) -> List[Dict[str, Any]]:
        """Get location autocomplete suggestions"""
        url = f"{self.places_base_url}/autocomplete"
        
        params = {
            "query": query,
            "types": "geo"  # Only return geographic locations
        }
        
        response = requests.get(url, headers=self.places_headers, params=params)
        response.raise_for_status()
        
        return response.json().get("results", [])

    def analyze_market_insights(self, location: LocationData, 
                              business_category: str = None) -> MarketInsight:
        """Analyze market insights for a location"""
        # Search for businesses in the area
        nearby_businesses = self.search_places(
            query=business_category or "business",
            location={"latitude": location.latitude, "longitude": location.longitude},
            radius=1000
        )
        
        # Calculate market insights
        total_businesses = len(nearby_businesses)
        categories = {}
        total_rating = 0
        rated_businesses = 0
        total_popularity = 0
        businesses_with_popularity = 0
        
        for business in nearby_businesses:
            if business.category:
                categories[business.category] = categories.get(business.category, 0) + 1
            
            # Handle rating (might be None)
            if business.rating is not None:
                total_rating += business.rating
                rated_businesses += 1
            
            # Handle popularity score (might be None)
            if business.popularity_score is not None:
                total_popularity += business.popularity_score
                businesses_with_popularity += 1
        
        # Determine demand categories (categories with most businesses)
        demand_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        demand_categories = [cat[0] for cat in demand_categories]
        
        # Calculate average rating
        avg_rating = total_rating / rated_businesses if rated_businesses > 0 else 0.0
        
        # Calculate average popularity
        avg_popularity = total_popularity / businesses_with_popularity if businesses_with_popularity > 0 else 0.0
        
        # Determine competition level
        if total_businesses < 10:
            competition_level = "Low"
        elif total_businesses < 30:
            competition_level = "Medium"
        else:
            competition_level = "High"
        
        # Calculate foot traffic score using multiple factors
        foot_traffic_score = 0.0
        
        # Factor 1: Average rating (if available)
        if avg_rating > 0:
            foot_traffic_score += (avg_rating / 5.0) * 0.4  # 40% weight
        
        # Factor 2: Average popularity (if available)
        if avg_popularity > 0:
            # Normalize popularity (assuming max popularity is around 100)
            normalized_popularity = min(avg_popularity / 100.0, 1.0)
            foot_traffic_score += normalized_popularity * 0.3  # 30% weight
        
        # Factor 3: Business density (more businesses = more foot traffic)
        if total_businesses > 0:
            # Normalize business count (assuming 50+ businesses is high density)
            density_score = min(total_businesses / 50.0, 1.0)
            foot_traffic_score += density_score * 0.3  # 30% weight
        
        # Ensure foot traffic score is between 0 and 1
        foot_traffic_score = min(foot_traffic_score, 1.0)
        
        # Estimate average rent based on market competition and foot traffic
        base_rent = 25000  # Base rent in INR (more realistic for smaller cities)
        if competition_level == "High":
            avg_rent = base_rent * 1.5  # Higher rent in competitive areas
        elif competition_level == "Medium":
            avg_rent = base_rent * 1.2  # Moderate rent in balanced markets
        else:
            avg_rent = base_rent * 0.8  # Lower rent in less competitive areas
        
        # Adjust based on foot traffic (higher foot traffic = higher rent potential)
        foot_traffic_adjustment = 1 + (foot_traffic_score * 0.5)  # Up to 50% increase
        avg_rent = avg_rent * foot_traffic_adjustment
        
        return MarketInsight(
            location=location,
            average_rent=avg_rent,
            foot_traffic_score=foot_traffic_score,
            competition_level=competition_level,
            demand_categories=demand_categories,
            market_trends={
                "total_businesses": total_businesses,
                "average_rating": float(avg_rating) if avg_rating is not None else 0.0,
                "average_popularity": float(avg_popularity) if avg_popularity is not None else 0.0,
                "top_categories": demand_categories
            }
        )

    def suggest_property_price(self, location: LocationData, 
                             property_type: str, size: float) -> Dict[str, Any]:
        """Suggest property pricing based on market analysis"""
        market_insight = self.analyze_market_insights(location, property_type)
        
        # Calculate suggested price based on market insights and location data
        base_price_per_sqft = 10000  # Base price per square foot in INR
        
        # Adjust based on competition and demand
        if market_insight.competition_level == "Low":
            price_multiplier = 0.8  # Lower prices in less competitive areas
        elif market_insight.competition_level == "Medium":
            price_multiplier = 1.0  # Standard pricing in balanced markets
        else:
            price_multiplier = 1.3  # Higher prices in competitive areas
        
        # Adjust based on foot traffic (higher foot traffic = higher property value)
        foot_traffic_score = market_insight.foot_traffic_score or 0.0
        foot_traffic_multiplier = 1 + (foot_traffic_score * 0.5)
        
        # Adjust based on property type
        property_type_multiplier = 1.0
        if property_type == "retail":
            property_type_multiplier = 1.2  # Retail properties typically command higher prices
        elif property_type == "office":
            property_type_multiplier = 1.1  # Office spaces have moderate premium
        elif property_type == "warehouse":
            property_type_multiplier = 0.8  # Warehouses typically have lower per-sqft prices
        
        suggested_price = base_price_per_sqft * size * price_multiplier * foot_traffic_multiplier * property_type_multiplier
        
        return {
            "suggested_price": suggested_price,
            "price_range": {
                "min": suggested_price * 0.8,
                "max": suggested_price * 1.2
            },
            "market_insights": market_insight.model_dump(),
            "reasoning": f"Based on {(market_insight.competition_level or 'Unknown')} competition and {(market_insight.foot_traffic_score or 0.0):.2f} foot traffic score"
        }

    def find_business_opportunities(self, location: LocationData, 
                                  budget: float, business_idea: str = None) -> List[BusinessRecommendation]:
        """Find business opportunities based on location and budget"""
        # Search for existing businesses to understand the market
        existing_businesses = self.search_places(
            query="business",
            location={"latitude": location.latitude, "longitude": location.longitude},
            radius=2000
        )
        
        # Analyze market gaps
        categories = {}
        for business in existing_businesses:
            if business.category:
                categories[business.category] = categories.get(business.category, 0) + 1
        
        # Find underrepresented categories (opportunities)
        opportunities = []
        for category, count in categories.items():
            if count < 3:  # Less than 3 businesses in this category
                opportunities.append(category)
        
        # If business idea is provided, search for similar businesses
        if business_idea:
            similar_businesses = self.search_places(
                query=business_idea,
                location={"latitude": location.latitude, "longitude": location.longitude},
                radius=5000
            )
            
            # Filter by budget
            affordable_options = [
                business for business in similar_businesses
                if business.price_tier and business.price_tier <= (budget / 10000)  # Rough conversion
            ]
            
            return affordable_options[:5]  # Return top 5 matches
        
        return existing_businesses[:5]  # Return top 5 existing businesses as examples
