# AI Marketing Performance Analyzer

An AI-powered web application that helps businesses understand the
performance of their marketing campaigns. The system accepts campaign
data in CSV/Excel format, validates and stores it, performs KPI and
campaign analysis, identifies customer trends, and generates AI-powered
insights and recommendations through an interactive dashboard.

## 🚀 Project Overview

Businesses often collect large amounts of marketing campaign data but
may find it difficult to identify which campaigns are performing well,
where money is being wasted, and what actions should be taken next.

The **AI Marketing Performance Analyzer** addresses this problem by
converting raw campaign data into meaningful business insights such as:

-   Best-performing campaigns
-   Poor-performing campaigns
-   Cost and conversion performance
-   Customer trends and segments
-   Channel performance
-   AI-generated campaign insights
-   Recommendations for future campaigns

## 🎯 Objectives

1.  Upload and validate marketing campaign data.
2.  Store campaign, customer, and analysis data securely.
3.  Calculate important marketing KPIs.
4.  Analyze campaign and customer performance.
5.  Use AI to generate meaningful insights and recommendations.
6.  Present the results through an easy-to-understand dashboard.

## ✨ Key Features

### 1. User Login & Registration

-   User registration and authentication
-   Secure access to the application
-   Separate user access to campaign analysis

### 2. Campaign Data Upload

-   Upload campaign data using CSV/Excel files
-   Receive uploaded data through the backend API
-   Validate the uploaded file before processing

### 3. Data Validation

-   Check required columns
-   Validate data types
-   Handle invalid or missing values
-   Prepare clean data for analysis

### 4. Campaign Data Storage

Campaign and application data are stored in a PostgreSQL database.

The database can contain: - Campaign data - User information - Analysis
results - Application logs

### 5. KPI Analysis

The system processes campaign data using Python and Pandas and
calculates useful marketing KPIs such as:

-   Cost Per Lead (CPL)
-   Conversion Rate
-   Click-Through Rate (CTR)
-   Return on Investment (ROI)
-   Return on Ad Spend (ROAS), when the required data is available

### 6. Campaign Performance Analysis

The system identifies: - Best-performing campaigns - Poor-performing
campaigns - Overall campaign performance - Campaign/channel performance
patterns

### 7. Customer Trend Analysis

Customer data is analyzed to identify: - Customer trends - Customer
segments - Age-based trends, when available - Location-based trends,
when available - Channel usage and engagement patterns

### 8. AI Insights & Recommendations

AI is used to transform the calculated analytics into understandable
business insights.

The AI layer can generate: - Campaign insights - Budget
recommendations - Campaign suggestions - Customer targeting
recommendations - Future campaign recommendations

### 9. Results API

The backend sends processed analytics and AI-generated insights to the
frontend through REST APIs.

### 10. Results Dashboard

The frontend presents the results using: - KPI cards - Charts and
graphs - Best and poor campaign summaries - Customer trend
visualizations - AI-generated recommendations

## 🏗️ System Architecture

``` text
User
  │
  ▼
React Frontend
  │
  │ Login / Upload / Dashboard
  ▼
FastAPI Backend
  │
  ├── Authentication
  ├── File Handling & Validation
  ├── REST APIs
  │
  ▼
PostgreSQL Database
  │
  ├── Campaign Data
  ├── User Data
  ├── Analysis Results
  └── Application Logs
  │
  ▼
Python + Pandas
  │
  ├── Data Cleaning
  ├── Data Processing
  └── KPI Calculation
  │
  ▼
AI Layer
  │
  ├── Campaign Insights
  ├── Recommendations
  └── Customer Targeting Suggestions
  │
  ▼
FastAPI Results API
  │
  ▼
React Dashboard
```

## 🛠️ Technology Stack

  Layer                  Technology
  ---------------------- ------------------------
  Frontend               React.js
  Backend                FastAPI
  Programming Language   Python
  Data Processing        Pandas
  Database               PostgreSQL
  ORM                    SQLAlchemy
  AI                     Groq API
  API Communication      REST API
  Data Input             CSV / Excel
  Visualization          React charting library

## 👥 Team Responsibilities

### Frontend / UI --- Apeksha C Rao

-   Build the React frontend
-   Create login and registration pages
-   Build campaign data upload interface
-   Design the results dashboard
-   Create KPI cards
-   Display charts and graphs
-   Display customer trends
-   Display AI recommendations
-   Connect frontend with backend APIs

### Backend / API / Database --- Sushanth S

-   Build FastAPI backend
-   Implement authentication APIs
-   Handle file uploads and validation
-   Create REST APIs
-   Design database structure
-   Implement SQLAlchemy models
-   Connect FastAPI with PostgreSQL
-   Store campaign and analysis data

### Analytics / AI --- Vishal S Naik

-   Process campaign data using Python and Pandas
-   Clean and preprocess data
-   Calculate marketing KPIs
-   Perform campaign performance analysis
-   Analyze customer trends
-   Integrate Groq API
-   Generate AI insights
-   Generate campaign and targeting recommendations

### Database --- PostgreSQL

PostgreSQL is used as the persistent data storage layer for: - Campaign
data - User data - Analysis results - Application logs

## 📊 Example KPIs

### Cost Per Lead

``` text
CPL = Total Campaign Cost / Number of Leads
```

### Conversion Rate

``` text
Conversion Rate = (Conversions / Leads) × 100
```

### Click-Through Rate

``` text
CTR = (Clicks / Impressions) × 100
```

### ROI

``` text
ROI = ((Revenue - Cost) / Cost) × 100
```

The exact KPI calculations depend on which fields are available in the
uploaded dataset.

## 🔄 Application Workflow

1.  User opens the application.
2.  User registers or logs in.
3.  User uploads campaign data in CSV/Excel format.
4.  FastAPI receives the uploaded file.
5.  Backend validates the file and its data.
6.  Valid campaign data is stored in PostgreSQL.
7.  Python/Pandas processes and cleans the data.
8.  Marketing KPIs are calculated.
9.  Campaign performance is analyzed.
10. Customer trends are identified.
11. The AI layer generates insights and recommendations.
12. FastAPI sends the results to the React frontend.
13. The dashboard displays KPIs, charts, trends, and recommendations.

## 📁 Suggested Project Structure

``` text
ai-marketing-performance-analyzer/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── models/
│   │   ├── services/
│   │   ├── analytics/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env
│
├── data/
│   └── sample_campaign_data.csv
│
├── README.md
└── .gitignore
```

## ⚙️ Installation & Setup

### Prerequisites

Make sure the following are installed:

-   Node.js
-   npm
-   Python 3.x
-   PostgreSQL
-   Git

### 1. Clone the Repository

``` bash
git clone <repository-url>
cd ai-marketing-performance-analyzer
```

### 2. Frontend Setup

``` bash
cd frontend
npm install
npm run dev
```

### 3. Backend Setup

``` bash
cd backend
python -m venv venv
```

Activate the virtual environment.

**Windows:**

``` bash
venv\Scripts\activate
```

**macOS/Linux:**

``` bash
source venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Run the FastAPI server:

``` bash
uvicorn app.main:app --reload
```

### 4. Database Setup

Create a PostgreSQL database and configure the database connection in
the backend environment variables.

Example:

``` env
DATABASE_URL=postgresql://username:password@localhost:5432/marketing_analyzer
GROQ_API_KEY=your_api_key
```

> Keep API keys and passwords in environment variables. Never commit
> `.env` files or secret keys to GitHub.

## 📥 Sample Input

The application can accept campaign data containing fields such as:

``` text
Campaign Name
Campaign Type
Channel
Impressions
Clicks
Leads
Conversions
Cost
Revenue
Customer Age
Customer Location
```

The exact fields can be adapted to the dataset used by the project.

## 📤 Expected Output

After processing the uploaded data, the dashboard can show:

``` text
┌─────────────────────────────────────┐
│          KPI DASHBOARD              │
├───────────┬───────────┬─────────────┤
│ Total Cost│   Leads   │ Conversions │
├───────────┼───────────┼─────────────┤
│    CPL    │ Conversion│    ROI      │
│           │   Rate    │             │
└───────────┴───────────┴─────────────┘

Best Performing Campaign
        ↓
Customer Trends
        ↓
AI Insights
        ↓
Recommendations for Next Campaign
```

## 🤖 Why AI?

Traditional analytics can calculate numbers, but business users may
still need help understanding **what those numbers mean and what to do
next**.

The AI component adds an interpretation layer by converting analytical
results into actionable recommendations.

For example:

> A campaign may have a high number of clicks but a low conversion rate.

The analytics layer identifies the pattern, while the AI layer can
explain the possible issue and suggest actions such as reviewing
targeting, landing-page effectiveness, or campaign messaging.

## 🔐 Security Considerations

-   Store passwords securely using appropriate password hashing.
-   Keep API keys in environment variables.
-   Validate uploaded files before processing.
-   Restrict accepted file types and file sizes.
-   Use authentication for protected API endpoints.
-   Avoid exposing sensitive database credentials to the frontend.

## 🔮 Future Enhancements

-   Real-time marketing data integration
-   Google Ads / Meta Ads integration
-   Automated scheduled reports
-   PDF report generation
-   Email reports
-   Campaign performance forecasting
-   Budget optimization
-   Predictive customer segmentation
-   Advanced anomaly detection
-   Role-based access control
-   More AI-powered natural-language queries

## 🌟 Project Highlights

-   Full-stack AI-powered analytics application
-   Automated campaign KPI calculation
-   Customer trend analysis
-   Interactive visualization dashboard
-   AI-generated marketing recommendations
-   CSV/Excel data processing
-   REST API-based frontend/backend communication
-   PostgreSQL-backed data persistence

## 📌 Project Status

🚧 **In Development**

This project is being developed as a team-based full-stack application
with separate responsibilities for frontend development,
backend/database development, and analytics/AI development.

## 👩‍💻 Team

  Member          Responsibility
  --------------- --------------------------
  Apeksha C Rao   Frontend / UI
  Sushanth S      Backend / API / Database
  Vishal S Naik   Analytics / AI

------------------------------------------------------------------------

**AI Marketing Performance Analyzer --- Turn campaign data into
actionable marketing decisions.**
