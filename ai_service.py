import json
from typing import Dict, List, Any, Optional
from config import Config
from models import PropertyOwner, FranchiseCompany, Entrepreneur, MatchResult, BusinessRecommendation

class AIService:
    def __init__(self):
        # Try to initialize Mistral client, but fall back to mock responses if it fails
        try:
            from mistralai.client import MistralClient
            from mistralai.models.chat_completion import ChatMessage
            self.client = MistralClient(api_key=Config.MISTRAL_API_KEY)
            self.model = "mistral-small-latest"
            # Store ChatMessage class for later use without re-imports
            self.ChatMessage = ChatMessage
            self.use_mistral = True
            print("✅ Mistral AI initialized successfully")
        except Exception as e:
            print(f"⚠️  Mistral AI not available: {e}")
            print("   Using mock AI responses for demonstration")
            self.use_mistral = False

    def _parse_json_safely(self, raw_text: str, expect: str = "object") -> Any:
        """Best-effort parsing of JSON-like LLM output."""
        import re, json

        if not raw_text:
            raise json.JSONDecodeError("empty", "", 0)

        text = raw_text.strip()
        text = text.replace('```json', '').replace('```', '').strip()
        text = text.replace("“", '"').replace("”", '"').replace("’", "'")

        if expect == "array":
            start = text.find('['); end = text.rfind(']')
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]
        else:
            start = text.find('{'); end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]

        # Quote unquoted keys
        text = re.sub(r'([\{,]\s*)([A-Za-z_][A-Za-z0-9_\s]*)\s*:',
                      lambda m: f'{m.group(1)}"{m.group(2).strip()}":', text)
        # Remove trailing commas
        text = re.sub(r',\s*([}\]])', r'\1', text)

        return json.loads(text)

    def _call_mistral(self, prompt: str) -> str:
        """Call Mistral AI with error handling"""
        if not self.use_mistral:
            raise Exception("Mistral AI is not available")
        
        try:
            # Use the current Mistral SDK client
            response = self.client.chat(
                model=self.model,
                messages=[self.ChatMessage(role="user", content=prompt)]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"⚠️  Mistral AI call failed: {e}")
            raise e  # Re-raise the exception instead of falling back to mock



    def analyze_property_market(self, property_owner: PropertyOwner, 
                              market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze property market and provide pricing recommendations"""
        
        # Extract specific property details for better analysis
        prop_type = property_owner.property_details.get("property_type", "commercial")
        prop_size = property_owner.property_details.get("area_sqft", 0)
        prop_location = property_owner.property_details.get("location", {})
        
        # Get rent and price information with specific details
        current_rent = property_owner.property_details.get("current_rent")
        asking_price = property_owner.property_details.get("asking_price")
        rent_info = f"Monthly Rent: ₹{current_rent:,}" if current_rent else "Not for rent"
        price_info = f"Sale Price: ₹{asking_price:,}" if asking_price else "Not for sale"
        
        # Extract market insights for specific analysis
        market_rent = market_data.get("average_rent", 0)
        competition_level = market_data.get("competition_level", "Unknown")
        foot_traffic = market_data.get("foot_traffic_score", 0)
        demand_categories = market_data.get("demand_categories", [])
        total_businesses = market_data.get("market_trends", {}).get("total_businesses", 0)
        
        prompt = f"""
        As a real estate market analyst, provide a detailed analysis of this specific property:

        PROPERTY DETAILS:
        - Type: {prop_type}
        - Size: {prop_size} sq ft
        - Location: {prop_location.get('city', 'Unknown')}, {prop_location.get('state', 'Unknown')}
        - {rent_info}
        - {price_info}

        MARKET DATA:
        - Average Market Rent: ₹{(market_rent or 0):,.0f}
        - Competition Level: {competition_level}
        - Foot Traffic Score: {(foot_traffic or 0.0):.2f}
        - Total Nearby Businesses: {total_businesses}
        - High-Demand Categories: {', '.join(demand_categories[:5])}

        Based on this specific data, provide detailed analysis in this exact JSON format:
        {{
            "pricing_strategy": "Specific pricing recommendations based on {prop_type} property in {prop_location.get('city', 'this location')} with {competition_level} competition. Include exact rent/sale price ranges based on market data.",
            "rent_analysis": {{
                "current_rent": "₹{(current_rent or 0):,.0f}",
                "market_average": "₹{(market_rent or 0):,.0f}",
                "recommendation": "Detailed rent analysis for {prop_size} sq ft {prop_type} property. Compare current rent with market average and provide specific recommendations for rent optimization."
            }},
            "price_analysis": {{
                "current_price": "₹{(asking_price or 0):,.0f} (Not for sale)" if not asking_price else "₹{(asking_price or 0):,.0f}",
                                                "market_value_estimate": "Based on market rent of ₹{(market_rent or 0):,.0f} for 20 years, estimated value: ₹{(market_rent or 0) * 12 * 20:,.0f}",
                "recommendation": "Sale price analysis considering {prop_size} sq ft {prop_type} property. Include market value assessment and pricing strategy."
            }},
            "target_franchises": ["List 3-5 specific franchise types that would work well in this {prop_type} property based on {demand_categories} demand"],
            "target_entrepreneurs": ["List 3-5 specific entrepreneur types who would find this {prop_type} property attractive based on size, location, and market conditions"],
            "positioning_advice": "Specific positioning strategy for {prop_type} property in {prop_location.get('city', 'this area')} with {competition_level} competition and {(foot_traffic or 0.0):.2f} foot traffic score",
                                            "investment_potential": "Detailed ROI analysis for {prop_size} sq ft {prop_type} property. Include specific investment potential based on market rent (₹{(market_rent or 0):,.0f}), competition ({competition_level}), and location factors"
        }}

        CRITICAL: Use the actual numbers and data provided above. Do not use generic values. Provide specific, actionable insights based on the real market data. Return ONLY valid JSON with proper quotes around all string values.
        """
        
        try:
            response_text = self._call_mistral(prompt)
            
            # Clean and extract JSON from the response
            import re
            
            # Remove any markdown formatting
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Try to extract JSON object
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
            
            # Try to parse the JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing error in analyze_property_market: {e}")
                print(f"⚠️  Raw response length: {len(response_text)} characters")
                print(f"⚠️  Raw response preview: {response_text[:300]}...")
                
                # If that fails, try to find and fix common JSON issues
                response_text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', response_text)
                response_text = re.sub(r':\s*([^",\d\[\]{}]+)([,}\]])', r': "\1"\2', response_text)
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as e2:
                    print(f"⚠️  Failed to parse JSON after fixes: {e2}")
                    print(f"⚠️  Fixed response preview: {response_text[:300]}...")
                    # Create data-driven fallback based on actual property and market data
                    market_rent = market_data.get("average_rent", 50000)
                    competition_level = market_data.get("competition_level", "Medium")
                    prop_size = property_owner.property_details.get("area_sqft", 1000)
                    prop_type = property_owner.property_details.get("property_type", "commercial")
                    
                    # Calculate estimated values based on actual data
                    estimated_rent = market_rent * (prop_size / 1000)  # Per 1000 sq ft
                    estimated_sale_price = estimated_rent * 12 * 20  # 20x annual rent
                    
                    return {
                        "pricing_strategy": f"Based on {prop_type} property ({prop_size} sq ft) in {competition_level} competition area. Recommended rent: ₹{estimated_rent:,.0f}/month, Sale price: ₹{estimated_sale_price:,.0f}",
                        "rent_analysis": {
                            "current_rent": f"₹{(current_rent or 0):,.0f}",
                            "market_average": f"₹{(market_rent or 0):,.0f}",
                            "recommendation": f"Market average rent: ₹{(market_rent or 0):,.0f}. For {prop_size} sq ft {prop_type} property, recommended rent range: ₹{estimated_rent * 0.8:,.0f} - ₹{estimated_rent * 1.2:,.0f}/month"
                        },
                        "price_analysis": {
                            "current_price": f"₹{(asking_price or 0):,.0f} (Not for sale)" if not asking_price else f"₹{asking_price:,.0f}",
                            "market_value_estimate": f"Based on market rent of ₹{(market_rent or 0):,.0f} for 20 years, estimated value: ₹{estimated_sale_price:,.0f}",
                            "recommendation": f"Estimated market value for {prop_size} sq ft {prop_type} property: ₹{estimated_sale_price:,.0f} based on {competition_level} competition and market rent data"
                        },
                        "target_franchises": ["Retail franchises", "Service businesses", "Food & beverage", "Healthcare services", "Educational centers"],
                        "target_entrepreneurs": ["Small business owners", "Service providers", "Retail entrepreneurs", "Healthcare professionals", "Educational institutions"],
                        "positioning_advice": f"Position as premium {prop_type} space in {competition_level} competition market. Highlight {prop_size} sq ft size and location advantages",
                        "investment_potential": f"ROI potential: 8-12% based on {(market_rent or 0):,.0f} market rent. {prop_size} sq ft {prop_type} property suitable for long-term investment"
                    }
            
            return result
        except Exception as e:
            print(f"⚠️  Error analyzing property market: {e}")
            # Create data-driven fallback based on actual property and market data
            market_rent = market_data.get("average_rent", 50000)
            competition_level = market_data.get("competition_level", "Medium")
            prop_size = property_owner.property_details.get("area_sqft", 1000)
            prop_type = property_owner.property_details.get("property_type", "commercial")
            
            # Calculate estimated values based on actual data
            estimated_rent = market_rent * (prop_size / 1000)  # Per 1000 sq ft
            estimated_sale_price = estimated_rent * 12 * 20  # 20x annual rent
            
            return {
                "pricing_strategy": f"Based on {prop_type} property ({prop_size} sq ft) in {competition_level} competition area. Recommended rent: ₹{estimated_rent:,.0f}/month, Sale price: ₹{estimated_sale_price:,.0f}",
                "rent_analysis": {
                    "current_rent": f"₹{(current_rent or 0):,.0f}",
                    "market_average": f"₹{(market_rent or 0):,.0f}",
                    "recommendation": f"Market average rent: ₹{(market_rent or 0):,.0f}. For {prop_size} sq ft {prop_type} property, recommended rent range: ₹{estimated_rent * 0.8:,.0f} - ₹{estimated_rent * 1.2:,.0f}/month"
                },
                "price_analysis": {
                    "current_price": f"₹{(asking_price or 0):,.0f} (Not for sale)" if not asking_price else f"₹{asking_price:,.0f}",
                    "market_value_estimate": f"Based on market rent of ₹{(market_rent or 0):,.0f} for 20 years, estimated value: ₹{estimated_sale_price:,.0f}",
                    "recommendation": f"Estimated market value for {prop_size} sq ft {prop_type} property: ₹{estimated_sale_price:,.0f} based on {competition_level} competition and market rent data"
                },
                "target_franchises": ["Retail franchises", "Service businesses", "Food & beverage", "Healthcare services", "Educational centers"],
                "target_entrepreneurs": ["Small business owners", "Service providers", "Retail entrepreneurs", "Healthcare professionals", "Educational institutions"],
                "positioning_advice": f"Position as premium {prop_type} space in {competition_level} competition market. Highlight {prop_size} sq ft size and location advantages",
                "investment_potential": f"ROI potential: 8-12% based on {(market_rent or 0):,.0f} market rent. {prop_size} sq ft {prop_type} property suitable for long-term investment"
            }

    def match_property_with_franchise(self, property_owner: PropertyOwner, 
                                    franchise_company: FranchiseCompany,
                                    market_insights: Dict[str, Any]) -> MatchResult:
        """Match property with franchise company using AI"""
        
        prompt = f"""
        Analyze the compatibility between this property and franchise opportunity:
        
        Property: {property_owner.property_details}
        Franchise Requirements: {franchise_company.franchise_requirements}
        Market Insights: {market_insights}
        
        Rate the match from 0-1 and provide reasoning.
        Format as JSON: {{"match_score": 0.85, "reasoning": "explanation", "recommendations": ["list", "of", "suggestions"]}}
        
        Important: Return ONLY valid JSON with proper quotes around all string values.
        """
        
        try:
            response_text = self._call_mistral(prompt)
            
            # Clean and extract JSON from the response
            import re
            
            # Remove any markdown formatting
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Try to extract JSON object
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
            
            # Try to parse the JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing error in match_property_with_franchise: {e}")
                
                # If that fails, try to find and fix common JSON issues
                response_text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', response_text)
                response_text = re.sub(r':\s*([^",\d\[\]{}]+)([,}\]])', r': "\1"\2', response_text)
                
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as e2:
                    print(f"⚠️  Failed to parse JSON after fixes: {e2}")
                    return MatchResult(
                        property_owner=property_owner,
                        franchise_company=franchise_company,
                        match_score=0.5,
                        reasoning="AI analysis could not be completed",
                        recommendations=[]
                    )
            
            return MatchResult(
                property_owner=property_owner,
                franchise_company=franchise_company,
                match_score=result.get("match_score", 0.5),
                reasoning=result.get("reasoning", "AI analysis pending"),
                recommendations=[]
            )
        except Exception as e:
            print(f"⚠️  Error in match_property_with_franchise: {e}")
            return MatchResult(
                property_owner=property_owner,
                franchise_company=franchise_company,
                match_score=0.5,
                reasoning="AI analysis could not be completed",
                recommendations=[]
            )

    def match_entrepreneur_with_opportunities(self, entrepreneur: Entrepreneur,
                                            properties: List[PropertyOwner],
                                            franchises: List[FranchiseCompany],
                                            business_opportunities: List[BusinessRecommendation]) -> List[MatchResult]:
        """Match entrepreneur with available opportunities"""
        
        prompt = f"""
        Match this entrepreneur with the best opportunities:
        
        Entrepreneur: {entrepreneur.model_dump()}
        Available Properties: {[p.property_details for p in properties]}
        Available Franchises: {[f.franchise_requirements for f in franchises]}
        Business Opportunities: {[b.model_dump() for b in business_opportunities]}
        
        Provide top 3 matches with scores and reasoning.
        Format as JSON array: [{{"type": "property/franchise/opportunity", "match_score": 0.9, "reasoning": "explanation"}}]
        """
        
        try:
            response_text = self._call_mistral(prompt)
            
            # Clean and extract JSON from the response
            import re
            
            # Remove any markdown formatting
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Try to extract JSON array
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group()
            
            # Try to parse the JSON
            try:
                matches = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing error in match_entrepreneur_with_opportunities: {e}")
                
                # If that fails, try to find and fix common JSON issues
                response_text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', response_text)
                response_text = re.sub(r':\s*([^",\d\[\]{}]+)([,}\]])', r': "\1"\2', response_text)
                
                try:
                    matches = json.loads(response_text)
                except json.JSONDecodeError as e2:
                    print(f"⚠️  Failed to parse JSON after fixes: {e2}")
                    return []
            
            results = []
            
            for match in matches:
                if match["type"] == "property":
                    for prop in properties:
                        results.append(MatchResult(
                            entrepreneur=entrepreneur,
                            property_owner=prop,
                            match_score=match["match_score"],
                            reasoning=match["reasoning"],
                            recommendations=[]
                        ))
                elif match["type"] == "franchise":
                    for franchise in franchises:
                        results.append(MatchResult(
                            entrepreneur=entrepreneur,
                            franchise_company=franchise,
                            match_score=match["match_score"],
                            reasoning=match["reasoning"],
                            recommendations=[]
                        ))
            
            return sorted(results, key=lambda x: x.match_score, reverse=True)[:5]
        except:
            return []

    def suggest_business_ideas(self, location: Dict[str, Any], 
                             budget: float, entrepreneur_type: str) -> List[Dict[str, Any]]:
        """Suggest business ideas based on location and budget - Now uses AI"""
        return self.generate_ai_business_ideas(location, budget, entrepreneur_type)

    def _analyze_competition(self, nearby_businesses: List[Any]) -> Dict[str, Any]:
        """Analyze competition from nearby businesses"""
        if not nearby_businesses:
            return {
                "total_businesses": 0, 
                "competition_level": "Unknown", 
                "categories": {},
                "direct_competitors": 0,
                "market_saturation": "Unknown"
            }
        
        categories = {}
        total_rating = 0
        rated_businesses = 0
        
        for business in nearby_businesses:
            # Handle both BusinessRecommendation objects and dict objects
            if hasattr(business, 'category'):
                category = business.category
            elif isinstance(business, dict):
                category = business.get('category', 'Unknown')
            else:
                category = 'Unknown'
                
            categories[category] = categories.get(category, 0) + 1
            
            # Handle rating from different object types
            rating = None
            if hasattr(business, 'rating'):
                rating = business.rating
            elif isinstance(business, dict):
                rating = business.get('rating')
                
            if rating:
                total_rating += rating
                rated_businesses += 1
            
            # Debug logging for first few businesses
            if len(categories) <= 3:
                print(f"🔍 Business: {getattr(business, 'name', 'Unknown')}")
                print(f"   Category: {category}")
                print(f"   Rating: {rating}")
                print(f"   Object type: {type(business)}")
                if hasattr(business, '__dict__'):
                    print(f"   Attributes: {list(business.__dict__.keys())}")
        
        # Determine competition level
        total_businesses = len(nearby_businesses)
        if total_businesses < 5:
            competition_level = "Very Low"
        elif total_businesses < 15:
            competition_level = "Low"
        elif total_businesses < 30:
            competition_level = "Moderate"
        else:
            competition_level = "High"
        
        # Calculate direct competitors (businesses in similar categories)
        competitive_categories = [
            'restaurant', 'cafe', 'food', 'retail', 'shop', 'store', 'market', 
            'grocery', 'supermarket', 'boutique', 'mall', 'plaza', 'center',
            'indian', 'vegan', 'vegetarian', 'seafood', 'bakery', 'donut'
        ]
        direct_competitors = sum(count for category, count in categories.items() 
                               if any(comp_cat in category.lower() for comp_cat in competitive_categories))
        
        # Determine market saturation based on total businesses and area
        if total_businesses == 0:
            market_saturation = "Unknown"
        elif total_businesses < 5:
            market_saturation = "Very Low"
        elif total_businesses < 15:
            market_saturation = "Low"
        elif total_businesses < 30:
            market_saturation = "Moderate"
        elif total_businesses < 50:
            market_saturation = "High"
        else:
            market_saturation = "Very High"
        
        avg_rating = total_rating / rated_businesses if rated_businesses > 0 else 0
        
        return {
            "total_businesses": total_businesses,
            "competition_level": competition_level,
            "average_rating": round(avg_rating, 2),
            "categories": categories,
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5],
            "direct_competitors": direct_competitors,
            "market_saturation": market_saturation
        }

    def generate_ai_business_ideas(self, location: Dict[str, Any], budget: float, 
                                 entrepreneur_type: str, nearby_businesses: List[Any] = None, 
                                 business_idea: str = None) -> List[Dict[str, Any]]:
        """Generate AI-powered business ideas with competition analysis"""
        
        # Analyze competition from nearby businesses
        competition_analysis = self._analyze_competition(nearby_businesses) if nearby_businesses else {}
        
        # Provide fallback competition analysis if no data available
        if not competition_analysis or competition_analysis.get('total_businesses', 0) == 0:
            print(f"⚠️  No nearby business data available, using fallback analysis")
            competition_analysis = {
                "total_businesses": 15,  # Reasonable default
                "competition_level": "Moderate",
                "direct_competitors": 5,
                "market_saturation": "Moderate",
                "average_rating": 4.0,
                "categories": {"Restaurant": 3, "Retail": 4, "Services": 3, "Healthcare": 2, "Education": 3},
                "top_categories": [("Retail", 4), ("Restaurant", 3), ("Services", 3)]
            }
        
        # Create AI prompt for business idea generation
        if isinstance(location, dict):
            location_info = f"Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}"
        else:
            location_info = f"Location: {location}"
        
        # Extract specific location details
        city = location.get('city', 'Unknown')
        state = location.get('state', 'Unknown')
        total_businesses = competition_analysis.get('total_businesses', 0)
        competition_level = competition_analysis.get('competition_level', 'Unknown')
        top_categories = competition_analysis.get('top_categories', [])
        
        # Include entrepreneur's business idea if provided
        idea_context = ""
        if business_idea and business_idea.strip():
            print(f"🎯 Entrepreneur provided business idea: {business_idea}")
            idea_context = f"""
        ENTREPRENEUR'S BUSINESS IDEA: {business_idea}
        
        CRITICAL INSTRUCTION: The entrepreneur has provided their own business idea. You MUST provide exactly 4 business ideas:
        1. IDEA #1: "{business_idea} for {city}, {state}" - enhanced version of their idea (set "is_entrepreneur_idea": true)
        2. IDEA #2: "{business_idea} specializing in [specific sector] for {city}, {state}" - different specialization of their SAME idea (set "is_entrepreneur_idea": true)
        3. IDEA #3: AI-generated complementary business idea for {city}, {state} (set "is_entrepreneur_idea": false)
        4. IDEA #4: AI-generated complementary business idea for {city}, {state} (set "is_entrepreneur_idea": false)
        
        EXAMPLES for ideas #1 and #2:
        - If entrepreneur says "mobile app development studio":
          * Idea #1: "Mobile App Development Studio for {city}" (enhanced version)
          * Idea #2: "Mobile App Development Studio specializing in [specific sector] for {city}" (different specialization)
        - If entrepreneur says "restaurant":
          * Idea #1: "Restaurant in {city}" (enhanced version)
          * Idea #2: "Restaurant specializing in [specific cuisine] in {city}" (different specialization)
        
        SPECIFIC EXAMPLE for this entrepreneur:
        - Entrepreneur idea: "{business_idea}"
        - Idea #1 should be: "{business_idea} for {city}" (enhanced)
        - Idea #2 should be: "{business_idea} specializing in [specific sector] for {city}" (different specialization)
        
        CRITICAL: For idea #2, you MUST use the EXACT SAME core business concept as the entrepreneur's idea, just with a different specialization or target market. DO NOT create a completely different business.
        
        IMPORTANT: If the entrepreneur says "mobile app development studio", both ideas #1 and #2 should be "mobile app development studio" with different specializations (e.g., "Mobile App Development Studio specializing in healthcare apps" or "Mobile App Development Studio specializing in e-commerce apps"), NOT specific app concepts.
        
        For ideas #1 and #2: BOTH must be DIRECTLY related to their original idea - different approaches, target markets, or specializations of the SAME core concept
        For ideas #3 and #4: Generate completely new business ideas that complement the entrepreneur's vision
        """
        else:
            idea_context = f"""
        NO ENTREPRENEUR IDEA PROVIDED
        
        CRITICAL INSTRUCTION: The entrepreneur has not provided a specific business idea. You MUST provide exactly 4 AI-generated business ideas:
        1. IDEA #1: AI-generated business idea for {city}, {state} (set "is_entrepreneur_idea": false)
        2. IDEA #2: AI-generated business idea for {city}, {state} (set "is_entrepreneur_idea": false)
        3. IDEA #3: AI-generated business idea for {city}, {state} (set "is_entrepreneur_idea": false)
        4. IDEA #4: AI-generated business idea for {city}, {state} (set "is_entrepreneur_idea": false)
        
        All ideas should be diverse and suitable for the location, budget, and market conditions.
        """
        
        prompt = f"""
        As a business consultant, analyze this entrepreneur's specific situation and suggest business ideas:

        LOCATION: {city}, {state}
        BUDGET: ₹{budget:,.0f}
        ENTREPRENEUR TYPE: {entrepreneur_type}{idea_context}
        MARKET ANALYSIS:
        - Total nearby businesses: {total_businesses}
        - Competition level: {competition_level}
        - Direct competitors: {competition_analysis.get('direct_competitors', 0)}
        - Market saturation: {competition_analysis.get('market_saturation', 'Unknown')}
        - Top business categories: {', '.join([cat[0] for cat in top_categories[:3]]) if top_categories else 'None found'}

        CONFIDENCE SCORE CALCULATION:
        Calculate confidence_score (70-95%) based on:
        - Market potential: High=+10%, Medium=+5%, Low=+0%
        - Risk level: Low=+10%, Medium=+5%, High=+0%
        - Competition: Low=+10%, Medium=+5%, High=+0%
        - Location fit: Excellent=+10%, Good=+5%, Poor=+0%
        - Base score: 70%
        - Maximum: 95%

        Based on this specific data, provide exactly 4 business ideas that would work well in {city}, {state}.
        Return ONLY a valid JSON array with this exact format:
        [
          {{
            "concept": "Specific business name for {city}",
            "startup_cost": 35000,
            "market_potential": "High/Medium/Low",
            "risk_level": "High/Medium/Low",
            "competition_level": "{competition_level}",
            "total_nearby_businesses": {total_businesses},
            "direct_competitors": {competition_analysis.get('direct_competitors', 0)},
            "market_saturation": "{competition_analysis.get('market_saturation', 'Unknown')}",
            "confidence_score": "Calculate based on market potential, risk level, competition, and location fit (70-95%)",
            "location_advantage": "Specific explanation of why this business would work well in {city}, {state} based on the market data",
            "competitive_advantages": "Specific competitive advantages for this business in {city}",
            "is_entrepreneur_idea": false
          }},
          {{
            "concept": "Second business idea for {city}",
            "startup_cost": 35000,
            "market_potential": "High/Medium/Low",
            "risk_level": "High/Medium/Low",
            "competition_level": "{competition_level}",
            "total_nearby_businesses": {total_businesses},
            "direct_competitors": {competition_analysis.get('direct_competitors', 0)},
            "market_saturation": "{competition_analysis.get('market_saturation', 'Unknown')}",
            "confidence_score": "Calculate based on market potential, risk level, competition, and location fit (70-95%)",
            "location_advantage": "Specific explanation of why this business would work well in {city}, {state} based on the market data",
            "competitive_advantages": "Specific competitive advantages for this business in {city}",
            "is_entrepreneur_idea": false
          }},
          {{
            "concept": "Third business idea for {city}",
            "startup_cost": 35000,
            "market_potential": "High/Medium/Low",
            "risk_level": "High/Medium/Low",
            "competition_level": "{competition_level}",
            "total_nearby_businesses": {total_businesses},
            "direct_competitors": {competition_analysis.get('direct_competitors', 0)},
            "market_saturation": "{competition_analysis.get('market_saturation', 'Unknown')}",
            "confidence_score": "Calculate based on market potential, risk level, competition, and location fit (70-95%)",
            "location_advantage": "Specific explanation of why this business would work well in {city}, {state} based on the market data",
            "competitive_advantages": "Specific competitive advantages for this business in {city}",
            "is_entrepreneur_idea": false
          }},
          {{
            "concept": "Fourth business idea for {city}",
            "startup_cost": 35000,
            "market_potential": "High/Medium/Low",
            "risk_level": "High/Medium/Low",
            "competition_level": "{competition_level}",
            "total_nearby_businesses": {total_businesses},
            "direct_competitors": {competition_analysis.get('direct_competitors', 0)},
            "market_saturation": "{competition_analysis.get('market_saturation', 'Unknown')}",
            "confidence_score": "Calculate based on market potential, risk level, competition, and location fit (70-95%)",
            "location_advantage": "Specific explanation of why this business would work well in {city}, {state} based on the market data",
            "competitive_advantages": "Specific competitive advantages for this business in {city}",
            "is_entrepreneur_idea": false
          }}
        ]

        CRITICAL REQUIREMENTS:
        1. Use the actual budget (₹{budget:,.0f}) and location ({city}, {state})
        2. Base recommendations on the real competition data ({total_businesses} businesses, {competition_level} competition)
        3. Provide specific, actionable business ideas for this exact location
        4. Return ONLY valid JSON with proper quotes around all string values
        5. Include exactly 4 business ideas with complete details
        6. If entrepreneur provided an idea, mark ideas #1 and #2 with "is_entrepreneur_idea": true
        7. If no entrepreneur idea, mark all ideas with "is_entrepreneur_idea": false
        8. ALWAYS provide exactly 4 ideas regardless of whether entrepreneur provided an idea or not
        9. DO NOT provide fewer than 4 ideas - always provide exactly 4
        10. For ideas #1 and #2: BOTH must be DIRECTLY related to the entrepreneur's original idea - different approaches, target markets, or specializations of the SAME core concept
        11. For idea #2: Use the EXACT SAME core business concept as the entrepreneur's idea, just with a different specialization or target market
        12. CONFIDENCE SCORE: Calculate different confidence scores (70-95%) for each idea based on:
            - Market potential: High=+10%, Medium=+5%, Low=+0%
            - Risk level: Low=+10%, Medium=+5%, High=+0%
            - Competition: Low=+10%, Medium=+5%, High=+0%
            - Location fit: Excellent=+10%, Good=+5%, Poor=+0%
            - Base score: 70%
            - Maximum: 95%
            - Each idea should have a DIFFERENT confidence score based on its unique characteristics
        """
        
        try:
            print(f"🎯 Sending prompt to AI for {city}, {state}")
            response_text = self._call_mistral(prompt)
            print(f"🎯 AI response received, length: {len(response_text)} characters")
            
            # Robust parse
            try:
                ideas = self._parse_json_safely(response_text, expect="array")
                print(f"🎯 Parsed {len(ideas)} ideas from AI response")
            except Exception as e:
                print(f"⚠️  JSON parsing error: {e}")
                print(f"⚠️  Raw response length: {len(response_text)} characters")
                print(f"⚠️  Raw response preview: {response_text[:300]}...")
                return []
            
            # Filter by budget and add AI insights
            affordable_ideas = []
            for idea in ideas:
                # Handle startup_cost as string or number
                startup_cost = idea.get("startup_cost", 0)
                if isinstance(startup_cost, str):
                    # Extract numeric value from string like "$35,000" or "35000"
                    import re
                    cost_match = re.search(r'[\d,]+', startup_cost.replace('$', '').replace(',', ''))
                    if cost_match:
                        startup_cost = float(cost_match.group().replace(',', ''))
                    else:
                        startup_cost = 0
                else:
                    startup_cost = float(startup_cost)
                
                if startup_cost <= budget * 1.2:
                    idea["startup_cost"] = startup_cost
                    idea["ai_generated"] = True
                    idea["competition_analysis"] = competition_analysis
                    affordable_ideas.append(idea)
            
            print(f"🎯 AI generated {len(ideas)} ideas, filtered to {len(affordable_ideas)} affordable ideas")
            return affordable_ideas[:4]
            
        except Exception as e:
            print(f"⚠️  Error generating business ideas: {e}")
            # Return empty list instead of fallback
            return []



    def generate_market_report(self, location: Dict[str, Any], 
                             business_category: str = None) -> Dict[str, Any]:
        """Generate comprehensive market report"""
        
        prompt = f"""
        Generate a market report for this location:
        
        Location: {location}
        Business Category: {business_category or "General"}
        
        Include:
        - Market trends
        - Competition analysis
        - Opportunities
        - Risks
        - Recommendations
        
        Format as JSON with sections.
        """
        
        try:
            response_text = self._call_mistral(prompt)
            return json.loads(response_text)
        except Exception as e:
            print(f"⚠️  Error generating market report: {e}")
            return {}

    def optimize_property_listing(self, property_details: Dict[str, Any],
                                market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize property listing for better visibility"""
        
        prompt = f"""
        Optimize this property listing for maximum appeal:
        
        Property: {property_details}
        Market Data: {market_data}
        
        Provide:
        - Optimized description
        - Key selling points
        - Target audience
        - Pricing strategy
        
        Format as JSON.
        """
        
        try:
            response_text = self._call_mistral(prompt)
            return json.loads(response_text)
        except Exception as e:
            print(f"⚠️  Error optimizing property listing: {e}")
            return {}
