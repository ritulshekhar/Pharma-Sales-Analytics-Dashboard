# Technical Interview Preparation Guide 🎓💬
## Pharma Sales Analytics Dashboard

This document provides a detailed breakdown of the technical decisions, architecture, engineering challenges, and business values of this project. It is designed to help you explain the project during technical interviews for Data Engineer, Full-Stack Developer, or Business Intelligence Engineer positions.

---

## 1. System Architecture & Tech Stack Justification

### Architectural Design
The project is built around a decoupled **three-tier architecture**:
1. **Data Generation / Ingestion Layer (Python + Pandas)**: Decoupled ETL script. The ingestion is separated from the app execution, preventing runtime slowdowns.
2. **Persistence Layer (PostgreSQL)**: Serves as a single source of truth. Structured queries are processed directly by the database engine instead of forcing Python to read all data in-memory.
3. **Presentation Layer (Streamlit + Plotly)**: A reactive web dashboard that queries the database dynamically on user request.

### Why PostgreSQL instead of SQLite or Pandas CSV loads?
In a production setting, loading data straight from CSV files or a single SQLite file fails at scale:
* **Concurrency**: SQLite locks the database file on writes and has poor concurrency. PostgreSQL handles hundreds of simultaneous client connections effortlessly, making it fit for production Streamlit apps shared inside a company.
* **Server-Side Computations**: By executing aggregations (`SUM`, `AVG`, `GROUP BY`) inside PostgreSQL, we transfer computation to the database server. The database returns only a tiny aggregated table (e.g., 4 rows for regions) rather than transferring 50,000 raw rows across the network for Pandas to compute.
* **Production-Grade Tooling**: PostgreSQL allows us to implement schema constraints, database roles, foreign keys, and perform query execution analysis (`EXPLAIN ANALYZE`).

---

## 2. Database Design & Optimization Strategies

### The Importance of Precision Types
In `schema.sql`, we used `NUMERIC(10, 2)` (aliases to `DECIMAL`) for `unit_price` and `total_revenue` instead of Python/SQL `FLOAT` or `DOUBLE PRECISION`.
* **The "Why"**: Floats represent decimal values using binary approximations (IEEE 754 standard). This leads to rounding errors during large aggregations (e.g., `0.1 + 0.2 = 0.30000000000000004`). For financial reporting, currency values must be stored in exact precision `DECIMAL` types to ensure arithmetic consistency down to the cent.

### Indexing Strategies
We created database indexes on:
1. `idx_pharma_sales_date` on `sale_date`
2. `idx_pharma_sales_region` on `region`
3. `idx_pharma_sales_category` on `category`
4. `idx_pharma_sales_drug` on `drug_name`

* **How Indexes Work**: PostgreSQL creates a B-Tree (Balanced Tree) structure representing the values of indexed columns.
* **Performance Impact**: Without indexes, a query filtering by date or region requires a **Sequential Scan** (PostgreSQL checks all 50,000 records one-by-one). With indexes, PostgreSQL performs an **Index Scan** (jumping directly to matching records in logarithmic time $O(\log N)$), speeding up dashboard filter rendering from milliseconds to microseconds.

---

## 3. Data Realism & Modeling Challenges

Generating random data using simple uniform distributions makes dashboards look fake (e.g., same amount of cold medicine sold in summer as winter). To show data engineering proficiency, we programmed real-world data behaviors:
1. **Customer Order Sizing**: Pharmacies buy in small units (1-10), clinics in medium batches (5-40), and hospitals order wholesale (10-100).
2. **Flu Seasonality**: We added a multiplier to respiratory and pain medications sold during winter months (Nov, Dec, Jan, Feb), creating a visible sales wave in the charts.
3. **Macro-Economic Shifts**: We introduced an inflation algorithm that gradually increases base pricing over 2 years, simulating realistic market conditions.
4. **Time of Day Distribution**: Transactions are concentrated between 8:00 AM and 8:00 PM to reflect realistic business working hours.

---

## 4. Key Engineering Challenges & Solutions

### Challenge 1: Streamlit’s Page Re-runs & Database Connection Overhead
* **Problem**: Streamlit works on a execution re-run model; whenever a user changes a filter, the entire `app.py` script executes from top to bottom. If we establish a new database connection on every filter change, we will quickly run out of database connections and slow down the dashboard response.
* **Solution**: We implemented connection pooling using SQLAlchemy's `create_engine` with parameters `pool_recycle=3600` and `pool_pre_ping=True`. We then wrapped it in Streamlit's `@st.cache_resource` decorator. This ensures the database driver establishes a pool once, holds it across re-runs, and verifies connection health automatically before using it.

### Challenge 2: SQL Injection Protection during Dynamic Filtering
* **Problem**: In dashboards, users choose regions or dates dynamically. Concatenating strings to form queries (e.g. `f"SELECT * FROM sales WHERE region = '{selected_region}'"`) creates serious SQL injection vulnerabilities.
* **Solution**: We built a secure dynamic SQL constructor. The python code converts multiselect options into parameterized lists (e.g., `:region_0`, `:region_1`) and passes a dictionary of inputs to SQLAlchemy's execution module:
  ```python
  conn.execute(text("SELECT * FROM pharma_sales WHERE region IN (:region_0, :region_1)"), params)
  ```
  This separates code logic from parameter values at the SQL engine level.

### Challenge 3: Streamlit UI Limitations
* **Problem**: Standard Streamlit apps have a simple look that makes them look like basic prototypes.
* **Solution**: We created a custom CSS file (`styles.css`) and injected it into the dashboard. We built customized HTML structures using grid cards, gradient accent highlights, glassmorphic shadows, and hover animations, maintaining compatibility with both light and dark operating system modes.

---

## 5. Business Value & Practical Application

When explaining this project, emphasize how these metrics solve real pharma business issues:

| Visual Feature | Business Insight | Actionable Decision |
| :--- | :--- | :--- |
| **KPIs (Top Drug & Region)** | Core revenue drivers. | Allocates local marketing budgets directly to the highest-converting drug families and regions. |
| **Monthly Revenue Trend** | Long-term growth & seasonality. | Allows procurement to pre-order inventory 3 months ahead of winter flu-spikes, avoiding stockouts. |
| **Customer Type Segment** | Order volume vs. Frequency. | Helps sales reps set up wholesale discounts for hospitals (high order size) while optimizing individual pharmacy margins. |
| **Payment Method Preference** | Transaction channels. | Highlights the volume of insurance-backed transactions, helping management prioritize integration with major insurance portals. |
| **SQL Console & Audit** | Compliance and Ad-hoc analytics. | Enables auditors to lookup individual transaction details, and allows business analysts to run custom SQL reports. |
