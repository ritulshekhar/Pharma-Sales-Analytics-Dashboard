# Pharma Sales Analytics Dashboard 💊📊

A complete, beginner-friendly data engineering and business intelligence (BI) project that showcases the integration of **Python**, **Pandas**, **PostgreSQL**, and **Streamlit**. 

This repository contains everything needed to generate a realistic pharmaceutical sales dataset of **50,000 transactions**, set up a relational database schema, load the data using bulk insertion, execute SQL-based analytical queries, and present interactive charts via a gorgeous web dashboard.

---

## 🏗️ Project Architecture & Data Flow

```mermaid
graph TD
    A[data_generator.py] -->|1. Generates 50,000 rows CSV| B[pharma_sales_data.csv]
    B -->|2. Reads CSV into Pandas| C[db_loader.py]
    D[schema.sql] -->|3. Creates tables & indexes| E[(PostgreSQL Database)]
    C -->|4. Bulk inserts data via SQLAlchemy| E
    E -->|5. Dynamic queries based on filters| F[app.py Streamlit Frontend]
    F -->|6. Renders visual charts| G[Interactive Web Dashboard]
```

1. **Data Generation**: `data_generator.py` creates a synthetic dataset of 50,000 rows with real-world complexities (seasonality, business hours, customer-segment quantities, inflation trends) and saves it as `pharma_sales_data.csv`.
2. **Database Initialization**: `db_loader.py` reads `schema.sql` to construct tables and optimization indexes in **PostgreSQL**.
3. **ETL ingestion**: `db_loader.py` reads the CSV file into a Pandas DataFrame and loads it into PostgreSQL using chunks.
4. **Interactive Dashboard**: `app.py` runs a Streamlit server, connects to PostgreSQL, queries data using dynamic parameters, and renders analytical KPI cards, Plotly charts, audit grids, and an interactive SQL learning console.

---

## 🛠️ Tech Stack & Key Libraries

- **Programming Language**: Python 3.8+
- **Data Manipulation**: Pandas
- **Database**: PostgreSQL (relational storage with custom indexing)
- **Database Connection Layer**: SQLAlchemy & psycopg2-binary
- **Frontend App Framework**: Streamlit
- **Data Visualization**: Plotly Express (interactive, responsive charts)
- **Styling**: Custom CSS and HTML injection for glassmorphic elements

---

## 📁 Repository Structure

```
Pharma-Sales-Analytics-Dashboard/
│
├── README.md               # Setup instructions, architecture, and overview
├── INTERVIEW_PREP.md       # Prep guide explaining design decisions, challenges, and value
├── requirements.txt        # Required Python packages
├── data_generator.py       # Python script generating 50,000 rows of synthetic data
├── schema.sql              # SQL definitions for database tables, checks, and indexes
├── db_loader.py            # Python loader that creates the DB, applies schema, and loads data
├── queries.sql             # Reference file with analytical SQL queries
├── app.py                  # Main Streamlit web application
└── styles.css              # Custom styling for dashboard titles and KPI cards
```

---

## 🚀 Step-by-Step Setup Instructions

### Step 1: Install PostgreSQL
Ensure PostgreSQL is installed and running on your local machine.

* **macOS (via Homebrew)**:
  ```bash
  brew install postgresql@14
  brew services start postgresql@14
  ```
* **Windows/Linux**: Download the installer from the [PostgreSQL Official Website](https://www.postgresql.org/download/) and complete the installation wizard. Ensure the service is active in Windows Services.
* **Docker Option**: If you have Docker installed, you can spin up PostgreSQL in seconds:
  ```bash
  docker run --name pharma-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
  ```

### Step 2: Clone & Prepare Workspace
Open your terminal in the directory of this project.

### Step 3: Create a Virtual Environment & Install Dependencies
It is highly recommended to use a virtual environment to manage dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### Step 4: Configure Database Credentials (Optional)
By default, the loader and dashboard connect to PostgreSQL using:
- **Host**: `localhost`
- **Port**: `5432`
- **User**: `postgres`
- **Password**: `postgres`
- **Database**: `pharma_sales_db`

If your local PostgreSQL credentials differ, create a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_postgres_username
DB_PASSWORD=your_postgres_password
DB_NAME=pharma_sales_db
```

### Step 5: Run the Dataset Generator
Generate the 50,000-row synthetic pharma sales CSV file:
```bash
python data_generator.py
```
This output script creates `pharma_sales_data.csv` in the root folder.

### Step 6: Create Database & Load the Data
Execute the loader script to create the database, build tables, add optimizations, and upload data:
```bash
python db_loader.py
```
This script reads the SQL commands in `schema.sql`, builds the structure, and performs bulk inserts into PostgreSQL.

### Step 7: Launch the Streamlit Dashboard
Run the following command to start the web application:
```bash
streamlit run app.py
```
The application will automatically open in a new tab in your default browser (usually at `http://localhost:8501`).

---

## 💡 Analytical Dashboard Features

1. **Executive Overview Tab**:
   - **Custom KPI Cards**: Displays *Total Revenue*, *Total Units Sold*, *Top Performing Product*, and *Top Region* with beautiful, glassmorphic styling and hover animations.
   - **Monthly Sales Trend**: Interactive area chart tracking revenue growth over 2 years.
   - **Geographic Market Share**: Doughnut chart representing region-wise revenue contribution.
   - **Payment Method Analysis**: Distribution of cash, credit card, and insurance orders.
2. **Product & Category Performance**:
   - Ranked horizontal bar chart detailing individual drug performance.
   - Interactive Treemap showing revenue shares across therapy classifications (e.g., Analgesics vs. Statins).
3. **Customer Insights**:
   - Aggregated metrics of Hospitals, Clinics, and Pharmacies comparing total revenue and average transaction sizes.
4. **Transaction Database Audit Console**:
   - Direct database querying capability with text search, date bounds, and revenue filters. Fetches paginated outputs cleanly.
5. **SQL Learning Console**:
   - A playground where you can select preset queries (e.g., Seasonal trends, wholesale order sizing) to read their explanation and run them directly against PostgreSQL.
   - Includes a **Custom SQL Editor** where users can write their own read-only `SELECT` queries to query the database tables live.
