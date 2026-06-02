# Deployment Guide 🚀🌐
## Pharma Sales Analytics Dashboard

This guide explains how to host your Streamlit dashboard and PostgreSQL database in the cloud for free.

---

## ⚠️ Important: Streamlit on Vercel
**Vercel is not designed for stateful, long-running Python servers like Streamlit.** 
* **The Reason**: Vercel executes code using **Serverless Functions** (ephemeral instances that shut down after 10–60 seconds). Streamlit requires a persistent, stateful background server with active WebSockets to synchronize UI state.
* **The Solution**: The standard and easiest way to deploy a Streamlit app is **Streamlit Community Cloud** (100% Free, secure, and native) or **Render** (free persistent container hosting). 

This guide details deployment using **Streamlit Community Cloud** (Frontend) + **Neon** (Serverless PostgreSQL Database).

---

## Step 1: Deploying the PostgreSQL Database on Neon (Free)

Since your database is currently local, you need a cloud-hosted PostgreSQL instance. We recommend **Neon.tech** because it is serverless, offers a generous free tier, and sets up in seconds.

1. Go to [Neon.tech](https://neon.tech/) and sign up for a free account.
2. Create a new project:
   * **Project Name**: `pharma-sales-analytics`
   * **PostgreSQL Version**: Select the default (e.g., 15 or 16)
   * **Region**: Choose the region closest to you
3. Once the database is created, Neon will show you a connection string. Copy the **Connection String** (it starts with `postgresql://...`).
4. In your connection string, identify the connection parameters:
   * **Host**: e.g., `ep-cool-snowflake-123456.us-east-2.aws.neon.tech`
   * **Database**: `neondb` (or your custom database name)
   * **Username**: e.g., `neondb_owner`
   * **Password**: The password shown by Neon
   * **Port**: `5432`

---

## Step 2: Seed the Cloud Database

Before deploying the frontend, you need to load the schema and the 50,000 rows of data into your new Neon database.

1. In your local workspace, open your `.env` file (or create one).
2. Edit the `.env` variables to match your Neon database credentials:
   ```env
   DB_HOST=ep-your-database-host.neon.tech
   DB_PORT=5432
   DB_USER=your_neon_username
   DB_PASSWORD=your_neon_password
   DB_NAME=neondb
   ```
3. Run the database loader script locally to upload the schema and dataset into your cloud database:
   ```bash
   python db_loader.py
   ```
   *(Since this runs over the network to a cloud server, it may take 20–30 seconds to upload all 50,000 rows. Wait for the `SUCCESS: Row count matches perfectly!` confirmation.)*

---

## Step 3: Deploy the Frontend to Streamlit Community Cloud (Free)

Streamlit Community Cloud hosts your dashboard directly from a GitHub repository.

### 1. Push Your Code to GitHub
1. Create a new public or private repository on GitHub (e.g., `pharma-sales-dashboard`).
2. Initialize git, commit your files, and push them to your repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Pharma dashboard"
   git branch -M main
   git remote add origin https://github.com/your-username/pharma-sales-dashboard.git
   git push -u origin main
   ```
   *Note: Make sure your `.env` file and `pharma_sales_data.csv` are in your `.gitignore` to avoid uploading passwords and large files to GitHub.*

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **New app**.
3. Fill in your repository details:
   * **Repository**: `your-username/pharma-sales-dashboard`
   * **Branch**: `main`
   * **Main file path**: `app.py`
4. Click **Advanced settings...** (this is where we configure our database credentials safely!).
5. Under **Secrets**, copy and paste your database credentials:
   ```toml
   DB_HOST = "ep-your-database-host.neon.tech"
   DB_PORT = "5432"
   DB_USER = "your_neon_username"
   DB_PASSWORD = "your_neon_password"
   DB_NAME = "neondb"
   ```
   *(Streamlit reads these secrets and injects them automatically as environment variables for `app.py`.)*
6. Click **Save**, then click **Deploy!**

Your app will build, install the dependencies from `requirements.txt`, and boot up. In 1–2 minutes, your dashboard will be live at a public URL (e.g., `https://pharma-sales.streamlit.app/`).

---

## Alternative: Deploying Streamlit on Render (Free)

If you prefer a platform like Vercel for continuous deployment of web apps, **Render** is the best alternative.

1. Create a free account on [Render.com](https://render.com/).
2. Click **New** -> **Web Service**.
3. Connect your GitHub repository.
4. Configure the Web Service:
   * **Name**: `pharma-sales-dashboard`
   * **Runtime**: `Python`
   * **Build Command**: `pip install -r requirements.txt`
   * **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
5. Under **Advanced**, click **Add Environment Variable** and add:
   * `DB_HOST` = `your_neon_host`
   * `DB_PORT` = `5432`
   * `DB_USER` = `your_neon_user`
   * `DB_PASSWORD` = `your_neon_password`
   * `DB_NAME` = `neondb`
6. Click **Deploy Web Service**. Render will spin up a persistent container and provide a live URL (e.g., `https://pharma-sales-dashboard.onrender.com`).
