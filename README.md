# YouTube Scrapping Application v2.1

A professional, modular Flask application for scraping and analyzing YouTube and Reddit comments with AI-powered query generation.

## 🚀 New Modular Architecture

This version features a completely modernized architecture following Flask best practices:

### 📁 Project Structure

```
youtube-scrapping-2.1/
├── 📄 main.py                 # Main application entry point
├── 📄 run.py                  # Convenient runner script with CLI options
├── 📄 application.py          # Flask application factory
├── 📄 config.py              # Configuration management
├── 📄 requirements.txt       # Python dependencies
├── 📁 routes/                # Route blueprints
│   ├── database_routes.py    # MongoDB operations
│   ├── search_routes.py      # AI-powered search functionality
│   └── testing_routes.py     # Testing utilities and home page
├── 📁 services/              # Business logic services
│   ├── ai_service.py         # Gemini AI integration
│   ├── database.py           # MongoDB service
│   ├── youtube_service.py    # YouTube API integration
│   ├── reddit_service.py     # Reddit API integration
│   └── comment_fetcher.py    # Unified comment fetching
├── 📁 utils/                 # Utility functions
│   ├── helpers.py            # Common utilities
│   └── file_utils.py         # File operations
├── 📁 templates/             # HTML templates
├── 📁 static/                # Static assets (CSS, JS)
├── 📁 data/                  # Output data files
├── 📁 history/               # Historical data
└── 📁 logs/                  # Application logs
```

## 🔧 Quick Start

### Option 1: Simple Start (Recommended)
```bash
# Start in development mode (default)
python main.py

# Or use the convenience runner
python run.py
```

### Option 2: Advanced Start with Options
```bash
# Development mode with custom port
python run.py --port 8080

# Production mode
python run.py --prod --host 0.0.0.0 --port 80

# Testing mode with debug enabled
python run.py --test --debug

# See all options
python run.py --help
```

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Environment Variables** configured (see Configuration section)
3. **Dependencies** installed: `pip install -r requirements.txt`

## ⚙️ Configuration

Create a `.env` file in the project root with your API keys:

```env
# Required - YouTube API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Optional - AI Features (Gemini)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - Database Features (MongoDB)
MONGODB_URI=your_mongodb_connection_string
MONGODB_DATABASE=youtube_scraper

# Optional - Reddit Integration
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name

# Optional - Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

## 🌟 Key Features

### 🤖 AI-Powered Query Generation
- Uses Google Gemini AI to generate multiple query variations
- Increases comment collection efficiency
- Smart query optimization

### 🔄 Multi-Source Data Collection
- **YouTube**: Video comments via YouTube API
- **Reddit**: Post and comment data via Reddit API
- **Unified Processing**: Combines data from multiple sources

### 🗄️ Database Integration
- MongoDB support for data persistence
- Batch tracking and management
- Historical data storage

### 🏗️ Modern Architecture
- **Application Factory Pattern**: Clean, testable Flask app creation
- **Blueprint Organization**: Modular route management
- **Service Layer**: Separated business logic
- **Configuration Management**: Environment-based configuration
- **Error Handling**: Comprehensive error management
- **Logging**: Structured application logging

## 🌐 API Endpoints

### Main Application
- `GET /` - Home page with web interface
- `GET /health` - Application health check

### Search & Data Collection
- `POST /api/search` - AI-powered multi-query search
- `POST /api/test_filename` - Test filename generation

### Database Operations
- `GET /api/database/test_mongodb` - Test MongoDB connection
- `GET /api/database/mongodb_stats` - Get database statistics
- `GET /api/database/batch/<batch_id>` - Get specific batch data
- `GET /api/database/batches` - List all batches

## 🏃‍♂️ Running the Application

### Development Mode
```bash
# Simple start
python main.py

# With custom settings
python run.py --dev --port 3000 --debug
```

### Production Mode
```bash
# Production with environment file
python run.py --prod --host 0.0.0.0 --port 8080

# Or set environment variables directly
FLASK_ENV=production FLASK_HOST=0.0.0.0 FLASK_PORT=8080 python main.py
```

### Testing Mode
```bash
python run.py --test
```

## 📊 Health Check

Check application status at: `http://localhost:5000/health`

Response includes:
- Overall application health
- Individual service status (AI, Database, YouTube, Reddit)
- Environment information
- Version details

## 🔧 Service Architecture

### Services (Singleton Pattern)
Each service is implemented as a singleton for efficient resource usage:

- **AIService**: Manages Gemini AI integration
- **DatabaseService**: Handles MongoDB operations
- **YouTubeService**: Manages YouTube API calls
- **RedditService**: Handles Reddit API integration
- **CommentFetcher**: Orchestrates multi-source data collection

### Configuration Management
- Environment-based configuration classes
- Validation of required environment variables
- Graceful degradation when optional services are unavailable

### Error Handling
- Global error handlers for common HTTP errors
- Service-level error handling with fallbacks
- Comprehensive logging for debugging

## 🚀 Deployment

### Environment Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (`.env` file or system environment)
4. Run the application: `python main.py`

### Production Considerations
- Set `FLASK_ENV=production`
- Disable debug mode: `FLASK_DEBUG=False`
- Use a production WSGI server (gunicorn, uWSGI)
- Configure proper logging
- Set up environment variables securely

## 📚 Development

### Adding New Features
1. **Routes**: Add new blueprints in the `routes/` directory
2. **Services**: Create new services in the `services/` directory
3. **Utilities**: Add helper functions in the `utils/` directory
4. **Configuration**: Add new settings to `config.py`

### Project Philosophy
- **Modular Design**: Each component has a single responsibility
- **Service Layer**: Business logic separated from routes
- **Configuration Driven**: Behavior controlled via environment variables
- **Error Resilience**: Graceful handling of service failures
- **Logging**: Comprehensive logging for monitoring and debugging

## 🐛 Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Check `.env` file configuration
   - Verify environment variables are loaded
   - Check application logs for missing key warnings

2. **Database Connection Issues**
   - Verify MongoDB URI is correct
   - Check network connectivity
   - Ensure database credentials are valid

3. **Service Unavailable**
   - Check `/health` endpoint for service status
   - Review application logs for error details
   - Verify API quotas and rate limits

### Debug Mode
Enable debug mode for detailed error information:
```bash
python run.py --debug
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes following the existing code style
4. Add tests if applicable
5. Submit a pull request

---

**Version**: 2.1 - Modern Modular Architecture  
**Author**: YouTube Scrapping Team  
**Last Updated**: September 2025