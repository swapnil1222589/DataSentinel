# Deployment Guide: DataSentinel on Render

DataSentinel can be deployed as a **Free Web Service** on [Render](https://render.com) in less than 3 minutes.

---

## Prerequisites

1. A free account on [Render.com](https://dashboard.render.com).
2. A free account on [GitHub](https://github.com).
3. Your local repository pushed to GitHub.

---

## Step 1: Push Code to GitHub

Open your terminal in the project directory:

```bash
# 1. Create a new empty repository on GitHub (e.g. named 'datasentinel')
# 2. Add your GitHub remote and push:
git remote add origin https://github.com/<your-username>/datasentinel.git
git branch -M master
git push -u origin master
```

---

## Step 2: Deploy on Render

### Option A: Automatic Blueprint (Recommended — 1-Click)
Render automatically detects the [`render.yaml`](../render.yaml) file in the root directory:

1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click the **New +** button in the top navigation bar.
3. Select **Blueprint**.
4. Connect and choose your `datasentinel` GitHub repository.
5. Render reads `render.yaml` and sets up everything automatically:
   - **Service Name**: `datasentinel`
   - **Environment**: `Python 3`
   - **Plan**: `Free`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run datasentinel/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`
6. Click **Apply**.

---

### Option B: Manual Web Service Setup

If you prefer configuring it manually:

1. In Render Dashboard, click **New +** -> **Web Service**.
2. Select your repository.
3. Configure the following fields:
   - **Name**: `datasentinel`
   - **Language / Runtime**: `Python 3`
   - **Branch**: `master` (or `main`)
   - **Region**: Closest to you (e.g., *Oregon (US West)* or *Frankfurt (EU)*)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**:
     ```bash
     streamlit run datasentinel/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
     ```
   - **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION` = `3.10.11`
5. Click **Create Web Service**.

---

## Step 3: Access Your Live Link

Once the build finishes (usually ~1–2 minutes):
- Render assigns a free public HTTPS URL:
  `https://datasentinel-xxxx.onrender.com`
- Your live DataSentinel app is ready to share with anyone!
