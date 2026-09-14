import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from src.database.db import get_all_students, get_teacher_subjects
import os

app = FastAPI(
    title="SnapClass API & Landing Portal",
    description="AI-Powered Classroom Attendance System with InsightFace & Streamlit Integration",
    version="2.0.0"
)

HTML_LANDING_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SnapClass — AI Attendance System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Climate+Crisis&family=Outfit:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #E0E3FF;
            --primary: #5865F2;
            --secondary: #EB459E;
            --dark-purple: #2E1065;
            --card-bg: #FFFFFF;
            --text-dark: #000000;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-main);
            color: var(--text-dark);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: transparent;
            padding: 2rem 5%;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo-box {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo-box img {
            height: 60px;
        }

        .logo-box h1 {
            font-family: 'Climate Crisis', sans-serif;
            font-size: 1.8rem;
            color: var(--secondary);
            line-height: 1.1;
        }

        nav {
            display: flex;
            gap: 15px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            border-radius: 30px;
            font-weight: 700;
            text-decoration: none;
            transition: all 0.25s ease-in-out;
            cursor: pointer;
            font-size: 0.95rem;
            border: none;
        }

        .btn-primary {
            background: var(--primary);
            color: white !important;
        }

        .btn-secondary {
            background: var(--secondary);
            color: white !important;
        }

        .btn-dark {
            background: black;
            color: white !important;
        }

        .btn:hover {
            transform: scale(1.05);
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }

        .hero {
            padding: 4rem 5% 3rem 5%;
            text-align: center;
            max-width: 1000px;
            margin: 0 auto;
        }

        .hero h2 {
            font-family: 'Climate Crisis', sans-serif;
            font-size: 3.2rem;
            color: var(--dark-purple);
            margin-bottom: 1.5rem;
            line-height: 1.15;
        }

        .hero p {
            font-size: 1.25rem;
            color: #2D3748;
            margin-bottom: 2.5rem;
            line-height: 1.6;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }

        .hero-actions {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }

        .features-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            padding: 3rem 5%;
            max-width: 1200px;
            margin: 0 auto;
            width: 100%;
        }

        .card {
            background: var(--card-bg);
            border-radius: 24px;
            padding: 30px;
            border: 2px solid #000000;
            border-left: 8px solid var(--secondary);
            box-shadow: 0 8px 16px rgba(0,0,0,0.05);
            transition: transform 0.25s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card-icon {
            font-size: 2.5rem;
            margin-bottom: 15px;
        }

        .card h3 {
            font-size: 1.4rem;
            color: var(--dark-purple);
            margin-bottom: 10px;
            font-weight: 700;
        }

        .card p {
            font-size: 1rem;
            color: #4A5568;
            line-height: 1.5;
        }

        .api-banner {
            background: #1D1E24;
            color: white;
            padding: 3rem 5%;
            margin-top: auto;
            border-top: 4px solid var(--primary);
        }

        .api-content {
            max-width: 1000px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        .api-content h3 {
            font-family: 'Climate Crisis', sans-serif;
            font-size: 1.8rem;
            color: var(--bg-main);
        }

        footer {
            background: #111217;
            color: #A0AEC0;
            text-align: center;
            padding: 1.5rem;
            font-size: 0.9rem;
        }

        footer a {
            color: var(--secondary);
            text-decoration: none;
        }

        /* Responsive Breakpoints */
        @media (max-width: 768px) {
            header {
                flex-direction: column;
                gap: 1.5rem;
                text-align: center;
                padding: 1.5rem 4%;
            }

            .logo-box {
                justify-content: center;
            }

            nav {
                width: 100%;
                justify-content: center;
                flex-wrap: wrap;
            }

            .hero {
                padding: 2.5rem 4% 2rem 4%;
            }

            .hero h2 {
                font-size: 2.2rem;
                margin-bottom: 1rem;
            }

            .hero p {
                font-size: 1.05rem;
                margin-bottom: 1.8rem;
            }

            .hero-actions {
                flex-direction: column;
                width: 100%;
            }

            .hero-actions .btn {
                width: 100%;
                justify-content: center;
            }

            .features-grid {
                grid-template-columns: 1fr;
                padding: 2rem 4%;
                gap: 18px;
            }

            .card {
                padding: 22px;
            }

            .api-content {
                flex-direction: column;
                text-align: center;
                align-items: center;
            }

            .api-content div {
                display: flex;
                flex-direction: column;
                width: 100%;
                align-items: center;
                gap: 10px;
            }

            .api-banner {
                padding: 2rem 4%;
            }
        }

        @media (max-width: 480px) {
            .hero h2 {
                font-size: 1.8rem;
            }

            .logo-box img {
                height: 48px;
            }

            .logo-box h1 {
                font-size: 1.4rem;
            }

            .btn {
                padding: 10px 18px;
                font-size: 0.9rem;
            }
        }
    </style>
</head>
<body>

    <header>
        <div class="logo-box">
            <img src="https://i.ibb.co/YTYGn5qV/logo.png" alt="SnapClass Logo">
            <h1>SNAP<br/>CLASS</h1>
        </div>
        <nav>
            <a href="http://localhost:8501" class="btn btn-primary">🚀 Launch App</a>
            <a href="/docs" class="btn btn-dark">⚡ OpenAPI Docs</a>
        </nav>
    </header>

    <section class="hero">
        <h2>AI-Powered Attendance Recognition</h2>
        <p>
            SnapClass is a next-generation classroom management platform leveraging InsightFace deep-learning embeddings, 
            live WebRTC video streams, automated session controls, and student dispute notifications.
        </p>
        <div class="hero-actions">
            <a href="http://localhost:8501" class="btn btn-primary" style="font-size: 1.1rem; padding: 15px 32px;">
                🎓 Student & Teacher Portals
            </a>
            <a href="https://github.com/mdafrid6370-beep/SnapClass" target="_blank" class="btn btn-secondary" style="font-size: 1.1rem; padding: 15px 32px;">
                ⭐ View on GitHub
            </a>
        </div>
    </section>

    <div class="features-grid">
        <div class="card">
            <div class="card-icon">🤖</div>
            <h3>Deep Learning Face Matching</h3>
            <p>High-accuracy face detection and 512-dimensional vector matching using InsightFace ArcFace models.</p>
        </div>

        <div class="card">
            <div class="card-icon">📹</div>
            <h3>Live WebRTC Video Stream</h3>
            <p>Real-time classroom camera video processing for instantaneous attendance recording during live lectures.</p>
        </div>

        <div class="card">
            <div class="card-icon">🔔</div>
            <h3>Student Disputes & Alerts</h3>
            <p>Students can review attendance session alerts and raise claims if unrecognized, allowing 1-click teacher approval.</p>
        </div>

        <div class="card">
            <div class="card-icon">🛡️</div>
            <h3>Automated Session Safety</h3>
            <p>Active attendance sessions automatically terminate when teachers log out or close the browser tab.</p>
        </div>
    </div>

    <div class="api-banner">
        <div class="api-content">
            <div>
                <h3>FastAPI Service Ready</h3>
                <p style="color:#CBD5E0; margin-top:5px;">Explore interactive API endpoints, OpenAPI schemas, and health metrics.</p>
            </div>
            <div style="display:flex; gap:12px;">
                <a href="/docs" class="btn btn-primary">Swagger UI (/docs)</a>
                <a href="/redoc" class="btn btn-secondary">ReDoc (/redoc)</a>
            </div>
        </div>
    </div>

    <footer>
        <p>© 2026 SnapClass — Built with Streamlit, FastAPI & InsightFace. <a href="https://github.com/mdafrid6370-beep/SnapClass" target="_blank">GitHub Repository</a></p>
    </footer>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def landing_page():
    return HTML_LANDING_PAGE

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "SnapClass FastAPI Landing Portal", "version": "2.0.0"}

@app.get("/api/v1/stats")
def app_stats():
    try:
        students = get_all_students()
        return {
            "total_students": len(students) if students else 0,
            "status": "active"
        }
    except Exception as e:
        return {"status": "active", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
