# 🏢 Business Matchmaking Platform

A comprehensive platform that connects property owners, franchise companies, and entrepreneurs using Foursquare's location intelligence and AI-powered matchmaking.

## 🎯 Project Overview

This platform serves three main user types:

### 1. Property Owners
- List commercial properties for franchise and entrepreneur opportunities
- Get AI-powered pricing recommendations based on market analysis
- Receive suggestions for target franchise companies and entrepreneurs
- Access market insights and location intelligence

### 2. Franchise Companies
- List franchise opportunities with specific requirements
- Find matching properties in target locations
- Connect with interested entrepreneurs
- Get market analysis for expansion decisions

### 3. Entrepreneurs
- **Investors**: Find properties and franchises to invest in
- **Idea Owners**: Get location recommendations for business ideas
- **Both**: Combine investment opportunities with business ideas
- Receive AI-powered business suggestions and market analysis

## 🚀 Features

- **Location Intelligence**: Powered by Foursquare Places API
- **AI Matchmaking**: Using Mistral AI for intelligent recommendations
- **Market Analysis**: Real-time market insights and pricing suggestions
- **User Management**: Foursquare managed users for authentication
- **Modern UI**: Responsive web interface with Bootstrap
- **RESTful API**: FastAPI backend with comprehensive endpoints

## 🛠️ Technology Stack

- **Backend**: Python FastAPI
- **AI**: Mistral AI (small model)
- **Location Data**: Foursquare Places API
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Database**: SQLite (in-memory for demo)
- **Authentication**: Foursquare Service Keys

## 📋 Prerequisites

- Python 3.8+
- Foursquare Developer Account
- Mistral AI API Key

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd foursqare
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\Activate.ps1
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**
   ```bash
   # Copy the example file
   cp env_example.txt .env
   
   # Edit .env with your API keys
   ```

6. **Get API Keys**

   **Foursquare Service Key:**
   - Visit [Foursquare Developer Console](https://developer.foursquare.com/console)
   - Create a new app
   - Get your Service Key
   - Add it to `.env` as `FOURSQUARE_SERVICE_KEY`

   **Mistral AI Key:**
   - Visit [Mistral AI Console](https://console.mistral.ai/)
   - Create an account and get your API key
   - Add it to `.env` as `MISTRAL_API_KEY`

## 🚀 Running the Application

1. **Start the server**
   ```bash
   python main.py
   ```

2. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📚 API Endpoints

### User Registration
- `POST /api/users/property-owner` - Register property owner
- `POST /api/users/franchise-company` - Register franchise company
- `POST /api/users/entrepreneur` - Register entrepreneur

### Recommendations & Matches
- `GET /api/property-owners/{user_id}/recommendations` - Get property recommendations
- `GET /api/franchise-companies/{user_id}/matches` - Get franchise matches
- `GET /api/entrepreneurs/{user_id}/opportunities` - Get entrepreneur opportunities

### Location & Market Analysis
- `GET /api/location/autocomplete` - Location autocomplete
- `GET /api/market-analysis/{location}` - Market analysis for location

### Platform Stats
- `GET /api/stats` - Platform statistics

## 🔄 Workflow

### For Property Owners:
1. Register with property details and location
2. Receive market analysis and pricing suggestions
3. Get matched with interested franchise companies
4. View market insights and demand categories

### For Franchise Companies:
1. Register with franchise requirements
2. Find matching properties in target areas
3. Connect with interested entrepreneurs
4. Access location intelligence for expansion

### For Entrepreneurs:
1. Register with budget and preferences
2. Receive business idea suggestions
3. Find matching properties and franchises
4. Get location recommendations for business ideas

## 🏗️ Project Structure

```
foursqare/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── models.py              # Pydantic data models
├── foursquare_api.py      # Foursquare API integration
├── ai_service.py          # Mistral AI service
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web interface
├── env_example.txt        # Environment variables example
└── README.md             # This file
```

## 🔑 Foursquare API Integration

This project uses the latest Foursquare API migration (2025-06-17):

- **Places API**: `places-api.foursquare.com`
- **Users API**: `users-api.foursquare.com`
- **Authentication**: Service Keys with Bearer tokens
- **Versioning**: Date-based versioning in headers

### Key API Features Used:
- Place search and details
- Location autocomplete
- Market analysis
- User management
- Geotagging capabilities

## 🤖 AI Integration

Uses Mistral AI (small model) for:
- Property market analysis
- Franchise-property matching
- Entrepreneur opportunity matching
- Business idea suggestions
- Market report generation
- Property listing optimization

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile
- **Modern Interface**: Bootstrap 5 with custom styling
- **Interactive Forms**: Dynamic form switching
- **Real-time Stats**: Live platform statistics
- **User-friendly**: Intuitive navigation and feedback

## 🔒 Security Features

- **API Key Management**: Secure environment variable handling
- **Input Validation**: Pydantic models for data validation
- **Error Handling**: Comprehensive error responses
- **CORS Support**: Cross-origin resource sharing enabled

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment
1. Set up a production server
2. Install dependencies
3. Configure environment variables
4. Use a production WSGI server (Gunicorn)
5. Set up reverse proxy (Nginx)

## 📊 Future Enhancements

- Database integration (PostgreSQL/MySQL)
- User authentication and sessions
- Real-time notifications
- Advanced analytics dashboard
- Mobile app development
- Payment integration
- Document management
- Advanced AI features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is created for the Foursquare Hackathon.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the Foursquare API documentation
3. Check the Mistral AI documentation

## 🎯 Hackathon Goals

This project demonstrates:
- ✅ Foursquare API integration
- ✅ AI-powered business intelligence
- ✅ Location-based matchmaking
- ✅ Modern web development
- ✅ Real-world business application
- ✅ Scalable architecture

---

**Built with ❤️ for the Foursquare Hackathon**
