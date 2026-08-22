# NeuralLens
## AI-Powered Image Super-Resolution Web Application

> Enhance low-resolution images into high-quality, photo-realistic outputs — powered by Generative Adversarial Networks.

---

## Problem Statement

Low-resolution images are a persistent challenge across photography, medical imaging, satellite imagery, and digital archiving. Traditional interpolation methods (bicubic, bilinear) produce blurry, artifact-ridden results that lack fine detail. Deep learning-based super-resolution, specifically **GANs**, can reconstruct photorealistic textures and edges that conventional methods cannot.

---

## Solution

**NeuralLens** is a full-stack web application that allows authenticated users to upload a low-resolution image and receive an AI-enhanced, high-resolution output in seconds. The application is powered by a **Real-ESRGAN** model (a production-quality variant of SRGAN) running on a Python backend, with a modern React frontend that provides a seamless upload-to-result experience.

---

## Core Features

| Feature | Description |
|---------|-------------|
| **Authentication** | Sign up and log in via Email/Password or Google OAuth |
| **Profile Screen** | View account details, usage summary, and manage session |
| **Image Upload** | Upload a JPEG or PNG low-resolution image (up to 2MB) |
| **AI Enhancement** | Backend processes the image using a Real-ESRGAN model for 4× upscaling |
| **Side-by-Side Comparison** | Interactive slider to compare original vs. enhanced image |
| **Download Result** | Save the upscaled high-resolution image to your device |
| **Enhancement History** | View all past image enhancement jobs tied to your account |

---

## Tech Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| **React 18 + Vite** | Fast, modern UI framework with hot-reload dev server |
| **React Router v6** | Client-side routing with protected authenticated routes |
| **Firebase Auth SDK** | Handles Google OAuth and Email/Password authentication |
| **Axios** | HTTP client for all API communication with auth token injection |
| **Vanilla CSS** | Custom styling with CSS variables — no framework dependencies |

### Backend
| Technology | Purpose |
|-----------|---------|
| **Python 3.11** | Core backend runtime |
| **FastAPI** | High-performance async REST API framework |
| **PyTorch** | Deep learning inference engine for the SRGAN model |
| **Real-ESRGAN** | Pre-trained GAN model for 4× photorealistic super-resolution |
| **OpenCV + Pillow** | Low-resolution image preprocessing and output postprocessing |
| **Firebase Admin SDK** | Server-side verification of Firebase ID tokens on protected routes |
| **SQLAlchemy + SQLite** | ORM and lightweight database for user records and job history |

---

## Application Screens

### 1. Login / Signup
Clean authentication screens with Email/Password fields and a **"Sign in with Google"** button powered by Firebase OAuth. Includes form validation and error feedback.

### 2. Dashboard
The primary workspace. Users upload a low-resolution image via a drag-and-drop or file picker interface. On submission, the image is sent to the backend, processed through Real-ESRGAN, and the enhanced result is displayed alongside the original in an interactive comparison slider.

### 3. History
A chronological list of all past enhancement jobs for the authenticated user, showing thumbnail previews, upload timestamps, and a download button for each result.

### 4. Profile
Displays the user's account information (name, email, provider), total number of images enhanced, and a logout option.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                  React Frontend (Vite)                    │
│                                                          │
│   Firebase Auth  →  Google OAuth / Email+Password        │
│   Dashboard      →  Upload Image  →  View SR Result      │
│   History        →  Past Enhancement Jobs                │
└────────────────────────┬─────────────────────────────────┘
                         │  HTTPS + Bearer Token (Firebase JWT)
┌────────────────────────▼─────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  Auth Middleware  →  Verify Firebase ID Token            │
│  /api/enhance     →  Preprocess → SRGAN Inference        │
│                   →  Save Result → Log to DB             │
│                   →  Return Enhanced Image URL           │
│  /api/history     →  Fetch user's enhancement records    │
│  /api/profile     →  Return user metadata                │
└────────────────────────┬─────────────────────────────────┘
                         │
            ┌────────────▼────────────┐
            │  SQLite Database        │  ←  Enhancement records
            │  Local Filesystem       │  ←  Uploaded & result images
            └─────────────────────────┘
```

### Authentication Flow

```
1. User authenticates via Firebase (Google OAuth or Email/Password)
2. Firebase returns a signed ID Token (JWT) to the browser
3. React includes the token in every API request header
4. FastAPI middleware verifies the token using Firebase Admin SDK
5. Verified uid and email are used to scope all database queries
```

---

## Model Details

| Property | Value |
|----------|-------|
| **Model** | Real-ESRGAN (x4plus variant) |
| **Upscale Factor** | 4× |
| **Weights Size** | ~65 MB |
| **Inference Time** | ~1–3s (CPU) / <1s (GPU) |
| **Input Formats** | JPEG, PNG |
| **Max Input Size** | 2MB |

The Real-ESRGAN model is loaded **once at server startup** as a singleton to avoid repeated disk I/O on every request. No model training is required — the pre-trained weights provide production-quality results out of the box.

---

## Project Structure

```
NeuralLens/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── routers/
│   │   ├── enhance.py             # POST /api/enhance
│   │   ├── history.py             # GET  /api/history
│   │   └── profile.py             # GET  /api/profile
│   ├── services/
│   │   ├── srgan.py               # Real-ESRGAN inference wrapper
│   │   └── image_utils.py         # OpenCV/Pillow pre & postprocessing
│   ├── models/
│   │   └── database.py            # SQLAlchemy models & DB session
│   ├── middleware/
│   │   └── auth.py                # Firebase token verification
│   ├── weights/
│   │   └── RealESRGAN_x4plus.pth  # Pre-trained model weights
│   ├── uploads/                   # Stored LR images (gitignored)
│   ├── results/                   # Stored SR images (gitignored)
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Signup.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── History.jsx
│   │   │   └── Profile.jsx
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── ImageCompare.jsx   # LR vs SR interactive slider
│   │   │   └── ProtectedRoute.jsx
│   │   ├── firebase.js            # Firebase SDK configuration
│   │   ├── api.js                 # Axios instance with auth interceptor
│   │   ├── App.jsx
│   │   └── index.css
│   ├── index.html
│   └── vite.config.js
│
└── PROJECT.md
```

---

## Phase 2 — Future Enhancements

- **Batch Processing** — Upload and enhance multiple images simultaneously
- **Scale Factor Selection** — User-selectable 2×, 4×, or 8× upscaling
- **Cloud Storage Migration** — Move from local FS to Firebase Storage or AWS S3
- **Model Comparison View** — Side-by-side output from multiple SR models
- **Download as ZIP** — Bulk export of enhanced images
- **Usage Quotas** — Per-account enhancement limits for resource management
- **PWA Support** — Offline-capable Progressive Web App

---

*Developed as a solo full-stack AI project · React + FastAPI + PyTorch + Firebase*
