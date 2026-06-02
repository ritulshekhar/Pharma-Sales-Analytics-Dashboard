"""
Pharma Sales Analytics Dashboard
A Streamlit web application powered by PostgreSQL, Pandas, and Plotly.
Provides real-time interactive business intelligence filters, custom KPI metrics,
dynamic charts, transaction auditing, and an interactive SQL console for education.
"""

import os
from datetime import datetime, date, time
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Pharma Sales Analytics Dashboard",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Styles
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("styles.css")

# Database configuration settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "pharma_sales_db")

# Cache database connection engine using Streamlit resource caching
@st.cache_resource
def get_db_engine():
    """Establishes and caches the database engine connection."""
    query_params = {}
    if DB_HOST and DB_HOST != "localhost" and DB_HOST != "127.0.0.1":
        query_params["sslmode"] = "require"
        
    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query=query_params
    )
    # pool_recycle re-creates connections every hour, preventing timeout drops
    return create_engine(connection_url, pool_recycle=3600, pool_pre_ping=True)

# Helper function to test connection
def test_db_connection():
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, ""
    except Exception as e:
        return False, str(e)

# Standard Drug Categories for validation
ALLOWED_CATEGORIES = [
    "Analgesics", "Antibiotics", "Statins", "Antidiabetics", 
    "Antacids", "Cardiovascular", "Respiratory", "Thyroid"
]

# Database Setup Tutorial (If DB connection fails)
def render_connection_error_page(error_msg):
    st.markdown('<div class="dashboard-header"><h1 class="dashboard-title">💊 Pharma Sales Analytics Dashboard</h1></div>', unsafe_allow_html=True)
    
    st.error("### ⚠️ Database Connection Error")
    st.markdown(f"Could not connect to PostgreSQL database **'{DB_NAME}'** on **{DB_HOST}:{DB_PORT}**.")
    
    with st.expander("Show detailed technical error", expanded=False):
        st.code(error_msg)
        
    st.markdown("---")
    st.markdown("### ⚙️ How to Fix: Step-by-Step Setup Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 1. Start PostgreSQL
        Ensure PostgreSQL is running on your machine:
        * **macOS (Homebrew)**:
          ```bash
          brew services start postgresql
          ```
        * **Windows (Services)**:
          Open `services.msc`, locate **postgresql-x64-XX**, and click **Start**.
        * **Docker**:
          ```bash
          docker run --name pharma-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
          ```
        
        #### 2. Configure Environment Variables
        Create a `.env` file in the root directory to customize credentials if they differ from the defaults:
        ```env
        DB_HOST=localhost
        DB_PORT=5432
        DB_USER=postgres
        DB_PASSWORD=your_secure_password
        DB_NAME=pharma_sales_db
        ```
        """)
        
    with col2:
        st.markdown("""
        #### 3. Generate the Dataset
        Before loading, generate the mock dataset of 50,000 sales entries:
        ```bash
        python data_generator.py
        ```
        This creates a file named `pharma_sales_data.csv`.
        
        #### 4. Load the Data into PostgreSQL
        Run the loader script. This automatically creates the database, table schema, indexes, and loads all 50,000 rows:
        ```bash
        python db_loader.py
        ```
        """)
        
    st.info("🔄 Refresh this page once PostgreSQL is running and the database is loaded.")
    if st.button("Retry Database Connection"):
        st.rerun()

# ------------------------------------------------------------------------------
# MAIN APPLICATION LOGIC
# ------------------------------------------------------------------------------
db_connected, error_details = test_db_connection()

if not db_connected:
    render_connection_error_page(error_details)
else:
    engine = get_db_engine()
    
    # Query static metadata limits for filters (min/max date, list of regions & categories)
    # We cache this query to make page loads incredibly snappy!
    @st.cache_data
    def get_filter_metadata():
        with engine.connect() as conn:
            min_max_date = conn.execute(text(
                "SELECT MIN(sale_date), MAX(sale_date) FROM pharma_sales"
            )).fetchone()
            regions = [r[0] for r in conn.execute(text(
                "SELECT DISTINCT region FROM pharma_sales ORDER BY region"
            )).fetchall()]
            categories = [c[0] for c in conn.execute(text(
                "SELECT DISTINCT category FROM pharma_sales ORDER BY category"
            )).fetchall()]
            
        return {
            "min_date": min_max_date[0].date() if min_max_date[0] else date(2024, 1, 1),
            "max_date": min_max_date[1].date() if min_max_date[1] else date(2026, 1, 1),
            "regions": regions,
            "categories": categories
        }
    
    metadata = get_filter_metadata()
    
    # --- SIDEBAR FILTERS ---
    st.sidebar.markdown("### 💊 Analytics Filters")
    st.sidebar.markdown("Use the controls below to slice and dice the sales dataset.")
    
    # Date Range Filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(metadata["min_date"], metadata["max_date"]),
        min_value=metadata["min_date"],
        max_value=metadata["max_date"]
    )
    
    # Extract date range values carefully
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    elif isinstance(date_range, tuple) and len(date_range) == 1:
        start_date = date_range[0]
        end_date = metadata["max_date"]
    else:
        start_date = metadata["min_date"]
        end_date = metadata["max_date"]
        
    # Region Multi-select
    selected_regions = st.sidebar.multiselect(
        "Select Region(s)",
        options=metadata["regions"],
        default=metadata["regions"]
    )
    
    # Category Multi-select
    selected_categories = st.sidebar.multiselect(
        "Select Drug Category(s)",
        options=metadata["categories"],
        default=metadata["categories"]
    )
    
    # Clear / Reset Button
    if st.sidebar.button("Reset Filters"):
        st.session_state.clear()
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    💡 **Database Info:**
    * **Engine**: PostgreSQL
    * **Database**: `pharma_sales_db`
    * **Table Size**: 50,000 Records
    """)
    
    # --- HELPER FUNCTION: DYNAMIC FILTER SQL CONSTRUCTOR ---
    def execute_filtered_query(query_template, override_select=None):
        """
        Dynamically appends WHERE clause filters and binds parameters.
        Runs securely via SQLAlchemy using bound variables to avoid SQL Injection.
        """
        where_clauses = ["sale_date BETWEEN :start_date AND :end_date"]
        params = {
            "start_date": datetime.combine(start_date, time.min),
            "end_date": datetime.combine(end_date, time.max)
        }
        
        # Region filtering
        if selected_regions:
            valid_regions = [r for r in selected_regions if r in metadata["regions"]]
            if valid_regions:
                placeholders = []
                for i, r in enumerate(valid_regions):
                    p_name = f"region_{i}"
                    placeholders.append(f":{p_name}")
                    params[p_name] = r
                where_clauses.append(f"region IN ({', '.join(placeholders)})")
        else:
            # If empty array, return no results
            where_clauses.append("1=0")
            
        # Category filtering
        if selected_categories:
            valid_categories = [c for c in selected_categories if c in metadata["categories"]]
            if valid_categories:
                placeholders = []
                for i, c in enumerate(valid_categories):
                    p_name = f"cat_{i}"
                    placeholders.append(f":{p_name}")
                    params[p_name] = c
                where_clauses.append(f"category IN ({', '.join(placeholders)})")
        else:
            where_clauses.append("1=0")
            
        # Construct full query
        where_sql = " AND ".join(where_clauses)
        
        # Replace the placeholders in template
        # Expects {where_filters} inside the query_template
        final_query = query_template.replace("{where_filters}", where_sql)
        
        with engine.connect() as conn:
            df = pd.read_sql_query(text(final_query), conn, params=params)
        return df

    # --- MAIN TITLE SECTION ---
    st.markdown(
        """
        <div class="dashboard-header">
            <h1 class="dashboard-title">💊 Pharma Sales Analytics Dashboard</h1>
            <p class="dashboard-subtitle">Enterprise Performance Management Portal powered by PostgreSQL & Streamlit</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # --- FETCH KPI DATA ---
    kpi_template = """
        SELECT 
            COALESCE(SUM(total_revenue), 0) AS total_revenue,
            COALESCE(SUM(quantity), 0) AS total_units_sold,
            (SELECT drug_name FROM pharma_sales WHERE {where_filters} GROUP BY drug_name ORDER BY SUM(total_revenue) DESC LIMIT 1) AS top_drug,
            (SELECT SUM(total_revenue) FROM pharma_sales WHERE {where_filters} GROUP BY drug_name ORDER BY SUM(total_revenue) DESC LIMIT 1) AS top_drug_revenue,
            (SELECT region FROM pharma_sales WHERE {where_filters} GROUP BY region ORDER BY SUM(quantity) DESC LIMIT 1) AS top_region,
            (SELECT SUM(quantity) FROM pharma_sales WHERE {where_filters} GROUP BY region ORDER BY SUM(quantity) DESC LIMIT 1) AS top_region_units
        FROM pharma_sales
        WHERE {where_filters}
    """
    
    with st.spinner("Fetching data from PostgreSQL..."):
        kpi_df = execute_filtered_query(kpi_template)
        
    kpi_data = kpi_df.iloc[0] if not kpi_df.empty else None
    
    if kpi_data is None or kpi_data["total_revenue"] == 0:
        st.warning("⚠️ No data matches your active filters. Try adjusting the date range or selecting more regions/categories.")
    else:
        # Display KPI Cards with custom CSS
        revenue = kpi_data["total_revenue"]
        units = kpi_data["total_units_sold"]
        top_drug = kpi_data["top_drug"] or "N/A"
        top_drug_rev = kpi_data["top_drug_revenue"] or 0
        top_region = kpi_data["top_region"] or "N/A"
        top_region_units = kpi_data["top_region_units"] or 0
        
        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card kpi-revenue">
                <span class="kpi-title">Total Revenue</span>
                <span class="kpi-value">${revenue:,.2f}</span>
                <span class="kpi-desc">Across selected filters</span>
            </div>
            <div class="kpi-card kpi-units">
                <span class="kpi-title">Total Units Sold</span>
                <span class="kpi-value">{int(units):,}</span>
                <span class="kpi-desc">Packs / Bottles distributed</span>
            </div>
            <div class="kpi-card kpi-drug">
                <span class="kpi-title">Top Performing Drug</span>
                <span class="kpi-value" style="font-size:1.5rem;">{top_drug}</span>
                <span class="kpi-desc">Revenue: <span class="kpi-accent-text">${top_drug_rev:,.2f}</span></span>
            </div>
            <div class="kpi-card kpi-region">
                <span class="kpi-title">Top Region</span>
                <span class="kpi-value">{top_region}</span>
                <span class="kpi-desc">Units Sold: <span class="kpi-accent-text">{int(top_region_units):,}</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # --- TAB STRUCTURE ---
        tab_overview, tab_products, tab_customers, tab_audit, tab_sql = st.tabs([
            "📊 Executive Overview",
            "💊 Product & Category Performance",
            "👥 Customer Insights",
            "🔍 Transaction Database Audit",
            "💻 SQL Learning Console"
        ])
        
        # ==============================================================================
        # TAB 1: EXECUTIVE OVERVIEW
        # ==============================================================================
        with tab_overview:
            st.markdown('<div class="section-header"><span class="section-icon">📈</span>Monthly Sales & Revenue Trends</div>', unsafe_allow_html=True)
            
            trend_query = """
                SELECT 
                    DATE_TRUNC('month', sale_date) AS sale_month,
                    SUM(total_revenue) AS revenue,
                    SUM(quantity) AS units
                FROM pharma_sales
                WHERE {where_filters}
                GROUP BY sale_month
                ORDER BY sale_month
            """
            trend_df = execute_filtered_query(trend_query)
            
            if not trend_df.empty:
                # Convert Timestamp to date for beautiful Chart formatting
                trend_df['sale_month'] = pd.to_datetime(trend_df['sale_month']).dt.date
                
                # Double axis line chart or side-by-side area chart
                # Plotly Express Area Chart
                fig_trend = px.area(
                    trend_df, 
                    x="sale_month", 
                    y="revenue",
                    title="Monthly Revenue Trend ($)",
                    labels={"sale_month": "Month", "revenue": "Revenue ($)"},
                    color_discrete_sequence=["#6366f1"]
                )
                fig_trend.update_layout(
                    margin=dict(l=40, r=40, t=40, b=40),
                    hovermode="x unified",
                    xaxis_title="",
                    yaxis_title="Revenue ($)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("No trend data available for selected filters.")
                
            # Row with two columns
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown('<div class="section-header"><span class="section-icon">🗺️</span>Geographic Market Share</div>', unsafe_allow_html=True)
                region_query = """
                    SELECT 
                        region,
                        SUM(total_revenue) AS revenue,
                        SUM(quantity) AS units
                    FROM pharma_sales
                    WHERE {where_filters}
                    GROUP BY region
                    ORDER BY revenue DESC
                """
                region_df = execute_filtered_query(region_query)
                
                if not region_df.empty:
                    fig_region = px.pie(
                        region_df, 
                        names="region", 
                        values="revenue",
                        hole=0.4,
                        title="Revenue Share by Region",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig_region.update_layout(
                        margin=dict(l=30, r=30, t=40, b=30),
                        paper_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_region, use_container_width=True)
                else:
                    st.info("No regional data available.")
                    
            with col_right:
                st.markdown('<div class="section-header"><span class="section-icon">💳</span>Payment Methods Preference</div>', unsafe_allow_html=True)
                payment_query = """
                    SELECT 
                        payment_method,
                        COUNT(sale_id) AS transactions,
                        SUM(total_revenue) AS revenue
                    FROM pharma_sales
                    WHERE {where_filters}
                    GROUP BY payment_method
                    ORDER BY transactions DESC
                """
                payment_df = execute_filtered_query(payment_query)
                
                if not payment_df.empty:
                    fig_payment = px.bar(
                        payment_df,
                        x="payment_method",
                        y="transactions",
                        color="payment_method",
                        text_auto=True,
                        title="Transaction Count by Payment Method",
                        labels={"payment_method": "Payment Method", "transactions": "No. of Sales"},
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    fig_payment.update_layout(
                        showlegend=False,
                        margin=dict(l=30, r=30, t=40, b=30),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_payment, use_container_width=True)
                else:
                    st.info("No payment method data available.")
                    
        # ==============================================================================
        # TAB 2: PRODUCT & CATEGORY PERFORMANCE
        # ==============================================================================
        with tab_products:
            st.markdown('<div class="section-header"><span class="section-icon">💊</span>Product Portfolio Optimization</div>', unsafe_allow_html=True)
            
            prod_query = """
                SELECT 
                    drug_name,
                    category,
                    SUM(quantity) AS units_sold,
                    SUM(total_revenue) AS total_revenue,
                    ROUND(AVG(unit_price), 2) AS avg_unit_price
                FROM pharma_sales
                WHERE {where_filters}
                GROUP BY drug_name, category
                ORDER BY total_revenue DESC
            """
            prod_df = execute_filtered_query(prod_query)
            
            if not prod_df.empty:
                col_chart, col_table = st.columns([3, 2])
                
                with col_chart:
                    fig_prod = px.bar(
                        prod_df,
                        x="total_revenue",
                        y="drug_name",
                        orientation="h",
                        color="category",
                        title="Drug Revenue Ranking (Colored by Category)",
                        labels={"total_revenue": "Total Revenue ($)", "drug_name": "Drug Name", "category": "Category"},
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    # Reverse y-axis to list highest revenue on top
                    fig_prod.update_layout(
                        yaxis={'categoryorder': 'total ascending'},
                        margin=dict(l=40, r=40, t=40, b=40),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_prod, use_container_width=True)
                    
                with col_table:
                    st.markdown("##### Product Performance Details")
                    
                    # Style table for display
                    styled_prod_df = prod_df.copy()
                    styled_prod_df["total_revenue"] = styled_prod_df["total_revenue"].apply(lambda x: f"${x:,.2f}")
                    styled_prod_df["avg_unit_price"] = styled_prod_df["avg_unit_price"].apply(lambda x: f"${x:,.2f}")
                    styled_prod_df["units_sold"] = styled_prod_df["units_sold"].apply(lambda x: f"{x:,}")
                    
                    # Columns rename
                    styled_prod_df.columns = ["Drug Name", "Category", "Units Sold", "Total Revenue", "Avg Unit Price"]
                    
                    st.dataframe(
                        styled_prod_df,
                        hide_index=True,
                        use_container_width=True
                    )
                    
                st.markdown('<div class="section-header"><span class="section-icon">🏷️</span>Therapeutic Category Distribution</div>', unsafe_allow_html=True)
                
                # Category aggregation query
                cat_query = """
                    SELECT 
                        category,
                        SUM(total_revenue) AS revenue,
                        SUM(quantity) AS units,
                        COUNT(sale_id) AS transactions
                    FROM pharma_sales
                    WHERE {where_filters}
                    GROUP BY category
                    ORDER BY revenue DESC
                """
                cat_df = execute_filtered_query(cat_query)
                
                if not cat_df.empty:
                    fig_cat = px.treemap(
                        cat_df,
                        path=["category"],
                        values="revenue",
                        title="Revenue Contribution by Drug Category (Treemap size represents Revenue)",
                        color="revenue",
                        color_continuous_scale="Purples",
                        labels={"revenue": "Revenue ($)", "category": "Category"}
                    )
                    fig_cat.update_layout(margin=dict(t=40, l=10, r=10, b=10))
                    st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.info("No product performance data available.")
                
        # ==============================================================================
        # TAB 3: CUSTOMER INSIGHTS
        # ==============================================================================
        with tab_customers:
            st.markdown('<div class="section-header"><span class="section-icon">👥</span>Customer Segments Analytics</div>', unsafe_allow_html=True)
            
            cust_query = """
                SELECT 
                    customer_type,
                    COUNT(sale_id) AS total_orders,
                    SUM(quantity) AS total_units,
                    SUM(total_revenue) AS total_revenue,
                    ROUND(AVG(quantity), 2) AS avg_units_per_order,
                    ROUND(AVG(total_revenue), 2) AS avg_order_value
                FROM pharma_sales
                WHERE {where_filters}
                GROUP BY customer_type
                ORDER BY total_revenue DESC
            """
            cust_df = execute_filtered_query(cust_query)
            
            if not cust_df.empty:
                col_c1, col_c2 = st.columns(2)
                
                with col_c1:
                    fig_cust_rev = px.bar(
                        cust_df,
                        x="customer_type",
                        y="total_revenue",
                        title="Total Revenue Contribution by Customer Segment",
                        labels={"customer_type": "Customer Type", "total_revenue": "Revenue ($)"},
                        color="customer_type",
                        color_discrete_sequence=["#4f46e5", "#06b6d4", "#ec4899"]
                    )
                    fig_cust_rev.update_layout(
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_cust_rev, use_container_width=True)
                    
                with col_c2:
                    fig_cust_val = px.bar(
                        cust_df,
                        x="customer_type",
                        y="avg_order_value",
                        title="Average Order Value ($) by Segment",
                        labels={"customer_type": "Customer Type", "avg_order_value": "Avg Order Value ($)"},
                        color="customer_type",
                        color_discrete_sequence=["#4f46e5", "#06b6d4", "#ec4899"]
                    )
                    # Add labels on top of bar charts
                    fig_cust_val.update_traces(texttemplate='$%{y:.2f}', textposition='outside')
                    fig_cust_val.update_layout(
                        showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_cust_val, use_container_width=True)
                    
                st.markdown("##### Customer Segment Summary Statistics")
                
                # Format table values
                styled_cust_df = cust_df.copy()
                styled_cust_df["total_revenue"] = styled_cust_df["total_revenue"].apply(lambda x: f"${x:,.2f}")
                styled_cust_df["avg_order_value"] = styled_cust_df["avg_order_value"].apply(lambda x: f"${x:,.2f}")
                styled_cust_df["total_units"] = styled_cust_df["total_units"].apply(lambda x: f"{x:,}")
                styled_cust_df["total_orders"] = styled_cust_df["total_orders"].apply(lambda x: f"{x:,}")
                
                styled_cust_df.columns = ["Customer Type", "Total Orders (Transactions)", "Total Units Sold", "Total Revenue", "Avg Units/Order", "Avg Order Value ($)"]
                st.dataframe(styled_cust_df, hide_index=True, use_container_width=True)
            else:
                st.info("No customer segment data available.")
                
        # ==============================================================================
        # TAB 4: TRANSACTION DATABASE AUDIT
        # ==============================================================================
        with tab_audit:
            st.markdown('<div class="section-header"><span class="section-icon">🔍</span>Transaction Database Audit Console</div>', unsafe_allow_html=True)
            st.markdown("Look up and filter individual database transaction records in real-time.")
            
            # Simple controls for database lookup
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                search_drug = st.text_input("Search Drug Name", value="")
            with c2:
                min_rev = st.number_input("Min Revenue ($)", min_value=0.0, value=0.0, step=50.0)
            with c3:
                max_records = st.selectbox("Max Rows to Fetch", options=[50, 100, 500], index=1)
                
            # Construct the dynamic audit query
            audit_template = """
                SELECT 
                    sale_id AS "Sale ID",
                    sale_date AS "Sale Timestamp",
                    drug_name AS "Drug Name",
                    category AS "Category",
                    quantity AS "Quantity",
                    unit_price AS "Unit Price ($)",
                    total_revenue AS "Total Revenue ($)",
                    region AS "Region",
                    customer_type AS "Customer Type",
                    payment_method AS "Payment"
                FROM pharma_sales
                WHERE {where_filters}
                {extra_filters}
                ORDER BY sale_date DESC
                LIMIT :limit_rows
            """
            
            # Extra conditional SQL string building
            extra_sql = []
            audit_params = {
                "limit_rows": max_records
            }
            
            if search_drug:
                extra_sql.append("AND drug_name ILIKE :search_term")
                audit_params["search_term"] = f"%{search_drug}%"
            if min_rev > 0:
                extra_sql.append("AND total_revenue >= :min_revenue")
                audit_params["min_revenue"] = min_rev
                
            extra_filters_str = " ".join(extra_sql)
            
            # Form final query
            final_audit_query = audit_template.replace("{extra_filters}", extra_filters_str)
            
            # Execute
            where_clauses = ["sale_date BETWEEN :start_date AND :end_date"]
            params = {
                "start_date": datetime.combine(start_date, time.min),
                "end_date": datetime.combine(end_date, time.max),
                **audit_params
            }
            
            # Apply filters
            if selected_regions:
                valid_regions = [r for r in selected_regions if r in metadata["regions"]]
                if valid_regions:
                    placeholders = []
                    for i, r in enumerate(valid_regions):
                        p_name = f"region_{i}"
                        placeholders.append(f":{p_name}")
                        params[p_name] = r
                    where_clauses.append(f"region IN ({', '.join(placeholders)})")
            if selected_categories:
                valid_categories = [c for c in selected_categories if c in metadata["categories"]]
                if valid_categories:
                    placeholders = []
                    for i, c in enumerate(valid_categories):
                        p_name = f"cat_{i}"
                        placeholders.append(f":{p_name}")
                        params[p_name] = c
                    where_clauses.append(f"category IN ({', '.join(placeholders)})")
                    
            final_query = final_audit_query.replace("{where_filters}", " AND ".join(where_clauses))
            
            with engine.connect() as conn:
                audit_df = pd.read_sql_query(text(final_query), conn, params=params)
                
            if not audit_df.empty:
                st.markdown(f"**Showing the latest {len(audit_df)} matching transactions:**")
                st.dataframe(
                    audit_df,
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No transactions found matching the specific search parameters.")
                
        # ==============================================================================
        # TAB 5: SQL LEARNING CONSOLE
        # ==============================================================================
        with tab_sql:
            st.markdown('<div class="section-header"><span class="section-icon">💻</span>Interactive SQL Learning Console</div>', unsafe_allow_html=True)
            st.markdown("Learn how to retrieve analytical insights using SQL. Choose a preset query, inspect its code, and run it, or write your own custom SQL query!")
            
            # Predefined queries
            preset_queries = {
                "1. Total Sales by Customer Segments (Revenue & Avg Size)": """-- Analyze order counts and sizing by buyer segment
SELECT 
    customer_type,
    COUNT(sale_id) AS total_transactions,
    SUM(quantity) AS total_units_sold,
    SUM(total_revenue) AS total_revenue_usd,
    ROUND(AVG(quantity), 2) AS avg_units_per_order
FROM pharma_sales
GROUP BY customer_type
ORDER BY total_revenue_usd DESC;""",

                "2. Seasonality Spikes in Analgesics & Respiratory Drugs": """-- Group seasonal drug sales by calendar month to find seasonal peaks
SELECT 
    EXTRACT(MONTH FROM sale_date) AS month_num,
    TO_CHAR(sale_date, 'Month') AS month_name,
    SUM(CASE WHEN category IN ('Respiratory', 'Analgesics') THEN quantity ELSE 0 END) AS seasonal_units_sold,
    SUM(CASE WHEN category IN ('Respiratory', 'Analgesics') THEN total_revenue ELSE 0 END) AS seasonal_revenue_usd,
    SUM(quantity) AS total_units_all_categories
FROM pharma_sales
GROUP BY month_num, month_name
ORDER BY month_num;""",

                "3. Average Price & Revenue per Drug (Pricing Strategy Control)": """-- Track pricing fluctuations and overall market contribution per drug
SELECT 
    drug_name,
    category,
    ROUND(MIN(unit_price), 2) AS min_observed_price,
    ROUND(MAX(unit_price), 2) AS max_observed_price,
    ROUND(AVG(unit_price), 2) AS avg_unit_price,
    SUM(quantity) AS total_units_sold,
    SUM(total_revenue) AS total_revenue_usd
FROM pharma_sales
GROUP BY drug_name, category
ORDER BY total_revenue_usd DESC;""",

                "4. Top 10 Wholesale Large-Volume Purchases (Hospitals & Clinics)": """-- Fetch the 10 largest transactions by units sold to audit bulk orders
SELECT 
    sale_id,
    sale_date,
    drug_name,
    customer_type,
    quantity,
    total_revenue,
    region
FROM pharma_sales
ORDER BY quantity DESC
LIMIT 10;"""
            }
            
            # Layout columns
            col_preset, col_custom = st.columns([1, 1])
            
            # Preset queries selection
            with col_preset:
                st.markdown("##### 📁 Preset Analytical Queries")
                selected_preset = st.selectbox(
                    "Choose an analytical scenario:",
                    options=list(preset_queries.keys())
                )
                
                # Show SQL code
                selected_sql = preset_queries[selected_preset]
                st.code(selected_sql, language="sql")
                
                if st.button("Execute Selected Preset"):
                    st.session_state["sql_console_query"] = selected_sql
                    st.session_state["execute_sql"] = True
                    
            # Custom SQL Box
            with col_custom:
                st.markdown("##### ✍️ Write Custom SQL Query")
                st.markdown("Write any valid `SELECT` query against the `pharma_sales` table.")
                
                custom_sql = st.text_area(
                    "SQL Editor",
                    value=st.session_state.get("sql_console_query", "SELECT * FROM pharma_sales LIMIT 5;"),
                    height=180
                )
                
                if st.button("Execute Custom SQL"):
                    st.session_state["sql_console_query"] = custom_sql
                    st.session_state["execute_sql"] = True
                    
            # Execution Results
            if st.session_state.get("execute_sql", False):
                query_to_run = st.session_state.get("sql_console_query", "")
                st.markdown("---")
                st.markdown("##### 📊 Query Execution Results")
                
                # Validation to protect against database writes (extremely basic safety barrier for learning environment)
                sql_upper = query_to_run.upper().strip()
                forbidden_words = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]
                
                is_safe = True
                for word in forbidden_words:
                    # Look for word bounded by whitespace or start/end of query to prevent false positives
                    if word in sql_upper:
                        # Allow CREATE only if followed by temp or view, but for simplicity let's block it
                        is_safe = False
                        blocked_word = word
                        break
                        
                if not is_safe:
                    st.error(f"❌ Execution Blocked: The query contains a modification statement ('{blocked_word}'). The SQL console only allows read-only (SELECT) queries for safety.")
                else:
                    try:
                        with engine.connect() as conn:
                            # Running raw SQL input
                            sql_result_df = pd.read_sql_query(text(query_to_run), conn)
                            
                        if not sql_result_df.empty:
                            st.success(f"✔️ Query executed successfully. Returned {len(sql_result_df):,} rows.")
                            st.dataframe(sql_result_df, hide_index=True, use_container_width=True)
                        else:
                            st.info("✔️ Query executed successfully, but returned 0 rows.")
                            
                    except Exception as e:
                        st.error(f"❌ SQL Execution Error:\n{str(e)}")
                        
                # Reset the trigger
                st.session_state["execute_sql"] = False
