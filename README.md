# Kartik Bhor — Full Stack Developer & AI Engineer Portfolio

A complete, high-performance, responsive personal portfolio website with a charcoal & electric purple glassmorphic design, scroll animations, dynamic typing, and a secure **Two-Step Email OTP Verification Contact System** integrated with **Supabase PostgreSQL**.

---

## 🌟 Key Features

1. **Modern UI/UX Design**:
   - Dark charcoal canvas (`#121214`) with electric purple neon accents and ambient floating gradient halos.
   - Glassmorphism cards with backdrop blur, micro-interactions, and code previews.
   - Transparent cutout portrait with halo lighting and floating expertise badges.
   - Accessible keyboard navigation and respect for `prefers-reduced-motion`.

2. **Core Sections**:
   - **Hero Section**: Dynamic typing effect, role badge, quick CTAs, and featured portrait.
   - **Metrics Strip**: Repositories, open-source commitment, and full-stack architecture stats.
   - **About Me**: Engineering philosophy and system design methodology.
   - **Skills & Technologies**: Categorized into Backend & Architecture, AI & Computer Vision, Databases & Cloud, and Frontend.
   - **Featured Projects**:
     - *Smart Attendance System* (Real-time Computer Vision & Face Recognition)
     - *Enterprise Resource Planning (ERP) System* (Full-Stack ERP with Role Authentication)
     - *Hospital Management System* (Patient workflow & backend security)
     - *Auto Paper Checking System* (Flagship AI Project: OCR evaluation of handwritten sheets)
     - *Email Spam Detection Classifier* (NLP Machine Learning security filter)
   - **Development Process**: 4-step disciplined engineering lifecycle.
   - **Interactive Contact Form with 2-Step OTP Verification**: Protects inbox against spam and spoofing.
   - **Resume Summary Modal**: Quick on-page modal for reviewing engineering credentials.

3. **Backend & Security Architecture**:
   - **Python 3 & Flask** modular backend.
   - **Cryptographic 6-digit OTPs** generated with `secrets` module and salted SHA-256 HMAC digest verification.
   - **Strict Rate Limiting**: Max 1 OTP send per 45 seconds per email/IP, and max 5 verification attempts per session.
   - **Supabase PostgreSQL**: Persistent storage for verified messages in `contact_messages` and verification records in `email_otps`.
   - **Row Level Security (RLS)**: Enforces least-privilege security policies so public visitors can never read messages or hashes.
   - **Dual Email Delivery**: Uses SMTP with TLS to deliver OTPs to visitors and notifications to Kartik's inbox; gracefully falls back to local terminal logging during offline development.

---

## 📁 Project Structure

```
kartik-portfolio/
├── app.py                  # Flask backend API & security routes
├── requirements.txt        # Python package dependencies
├── schema.sql              # Supabase PostgreSQL database schema & RLS policies
├── .env.example            # Environment variables template
├── .gitignore              # Protects .env, virtualenvs, and sensitive files
├── README.md               # Beginner-friendly setup & deployment documentation
├── templates/
│   └── index.html          # Semantic HTML5 portfolio template
└── static/
    ├── css/
    │   └── style.css       # Glassmorphism, animations & responsive styling
    ├── js/
    │   └── script.js       # Auto-advancing OTP, typing effect & scroll reveals
    └── images/
        └── kartik.png      # Profile cutout photo
```

---

## ⚡ Quick Start (Local Setup on Windows)

### 1. Open PowerShell & Navigate to the Project Folder
```powershell
cd "c:\Users\iNDIA\OneDrive\Desktop\kartik portfilio"
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell shows an execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again).*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Your Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and configure your credentials:
```env
FLASK_SECRET_KEY=your_generated_random_secret_string
SUPABASE_URL=https://uhreznoytbvlommykqpe.supabase.co
SUPABASE_KEY=your_supabase_service_role_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
CONTACT_INBOX=your_personal_email@gmail.com
```
> **Note on Local Testing:** If you don't configure SMTP immediately, the backend runs in **Local Development Mode** and displays the 6-digit OTP directly inside your terminal window, allowing you to test the complete verification flow instantly!

### 5. Setup the Database in Supabase
1. Open your [Supabase Project Dashboard](https://supabase.com/dashboard/project/uhreznoytbvlommykqpe).
2. Click **SQL Editor** from the left navigation bar.
3. Click **New query**.
4. Open the `schema.sql` file in this repository, copy its entire contents, paste it into the Supabase editor, and click **Run**.
5. Both `contact_messages` and `email_otps` tables will be created with Row Level Security enabled.

### 6. Run the Application
```powershell
python app.py
```
Open your browser and visit: **`http://localhost:5000`**

---

## 🧪 Testing the User Flows

1. **Visit Home Page**:
   - Open `http://localhost:5000`. Observe the entrance animations, glowing background, dynamic typed roles, and project cards.
2. **Health Check Endpoint**:
   - Visit `http://localhost:5000/health`.
   - Verify that the API returns HTTP 200 with JSON status.
3. **Contact & OTP Verification**:
   - Scroll to the **Contact** section.
   - Enter your name, email, subject, and a message (minimum 10 characters).
   - Click **Proceed to Verification**.
   - Check your terminal (or your real inbox if SMTP was configured) to see the 6-digit code.
   - Enter the 6-digit code in the boxes (you can also copy and paste the entire 6-digit code into the first box).
   - Click **Verify & Send Message**.
   - Confirm that the message reaches the success screen and is recorded!

---

## 🚀 Free Deployment Guide

You can deploy the entire application for free on platforms like **Render.com**:

1. **Push to GitHub**:
   ```powershell
   git add .
   git commit -m "Build complete developer portfolio for Kartik Bhor"
   git branch -M main
   git remote add origin https://github.com/kartikbhor413-hash/<your-repo-name>.git
   git push -u origin main
   ```
2. **Deploy on Render (Web Service)**:
   - Create a free account at [render.com](https://render.com).
   - Click **New** -> **Web Service** -> Connect your GitHub repository.
   - Runtime: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Under **Environment Variables**, add:
     - `FLASK_SECRET_KEY`
     - `SUPABASE_URL`
     - `SUPABASE_KEY`
     - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
     - `CONTACT_INBOX`
3. Click **Deploy**. Render will provide a free live HTTPS URL (e.g., `https://kartik-bhor.onrender.com`).

---

## 🔒 Security Best Practices

- Real credentials must always reside in `.env` and are strictly excluded via `.gitignore`.
- OTP codes are hashed before storage and are never returned in client-side JSON responses.
- OTPs expire after 5 minutes and are automatically invalidated once used.
- IP-based rate limiting safeguards against bot abuse and denial-of-service attempts.
