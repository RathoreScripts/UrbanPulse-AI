UrbanPulse AI 💧

AI-Powered Campus Water Management & Digital Twin

UrbanPulse AI is an intelligent campus water management prototype that combines machine learning, hydraulic network simulation, water allocation optimization, and real-time telemetry monitoring to support data-driven water management.

The system analyzes historical water consumption, forecasts future demand across campus zones, simulates hydraulic network conditions, and monitors simulated operational data through an interactive dashboard.

🚀 Key Features

- AI-Based Demand Forecasting: Random Forest models forecast water demand for five campus zones.
- Hydraulic Network Simulation: Models water distribution, pressure, flow rate, and tank levels.
- Scenario Analysis: Evaluates normal, peak demand, drought, leakage, pipe burst, and pump outage scenarios.
- Water Allocation Optimization: Calculates zone-wise water allocation based on forecast demand and available supply assumptions.
- Live Operations Dashboard: Displays telemetry, consumption trends, zone readings, and operational alerts.
- REST API: FastAPI backend provides telemetry and alert data.
- Data Visualization: Interactive charts and reports for monitoring and analysis.

🏗️ System Architecture

Historical Water Consumption Data
              |
              v
      Data Processing
              |
       +------+------+
       |             |
       v             v
 AI Demand       Hydraulic Network
 Forecasting       Simulation
       |             |
       +------+------+
              |
              v
     Water Optimization
              |
              v
       Scenario Analysis
              |
              v
      Telemetry Simulator
              |
              v
       FastAPI Backend
              |
              v
       SQLite Database
              |
              v
       Dash Dashboard

🧠 Machine Learning

UrbanPulse AI uses Random Forest regression models for zone-wise water demand forecasting.

The five modeled zones are:

1. Hostel
2. Academic
3. Canteen
4. Medical
5. Sports

Saved forecasting models are included in "models/forecasting/".

🛠️ Technology Stack

Component| Technologies
Programming| Python
Machine Learning| Scikit-learn, Pandas, NumPy
Visualization| Plotly
Frontend Dashboard| Dash, Dash Bootstrap Components
Backend API| FastAPI
Database| SQLite
Hydraulic Simulation| EPANET-based network simulation
Version Control| Git, GitHub

📂 Project Structure

UrbanPulse/
│
├── app.py
├── requirements.txt
│
├── config/
│
├── data/
│   └── synthetic/
│
├── models/
│   └── forecasting/
│
├── artifacts/
│   └── reports/
│
├── dashboard/
│   ├── app.py
│   ├── data_loader.py
│   ├── assets/
│   └── pages/
│       ├── overview.py
│       └── live.py
│
├── realtime/
│   ├── simulator.py
│   ├── runner.py
│   ├── storage.py
│   └── api/
│       └── main.py
│
├── scripts/
│
└── src/
    └── urbanpulse/

⚙️ Installation and Setup

1. Clone the repository

git clone https://github.com/RathoreScripts/UrbanPulse-AI.git
cd UrbanPulse-AI

2. Create a virtual environment

python -m venv .venv

Activate it on Windows:

.venv\Scripts\Activate.ps1

3. Install dependencies

pip install -r requirements.txt

4. Run the dashboard

python -m dashboard.app

Open:

"http://127.0.0.1:8050"

5. Run the FastAPI backend

Open another terminal:

uvicorn realtime.api.main:app --reload --host 127.0.0.1 --port 8000

API documentation:

"http://127.0.0.1:8000/docs"

6. Start the telemetry simulator

Open another terminal:

python -m realtime.runner

The dashboard uses the FastAPI backend to display simulated operational telemetry.

📡 Real-Time Monitoring

The Live Operations module provides:

- Campus water consumption monitoring
- Zone-wise consumption readings
- Simulated pressure monitoring
- Tank-level monitoring
- Operational status indicators
- Alert generation and acknowledgement
- Automatic dashboard refresh

Important: The current real-time module operates in simulation mode. It uses generated telemetry and prototype assumptions rather than readings from physical sensors or actual pump-control equipment.

📊 Current Project Scope

UrbanPulse AI is a working prototype designed to demonstrate how AI forecasting, hydraulic simulation, optimization, and operational monitoring can work together in a campus water management system.

The architecture can be extended in the future with IoT sensors, hardware integration, and real-time infrastructure data.

🔮 Future Enhancements

- ESP32 and IoT sensor integration
- Real-time water flow and pressure monitoring
- Hardware-connected tank-level monitoring
- Advanced leak detection
- Predictive maintenance
- Deployment to a cloud platform
- Enhanced digital twin visualization

👨‍💻 Developer

Aditya Singh Rathore

GitHub: "@RathoreScripts" (https://github.com/RathoreScripts)

Project: "UrbanPulse AI" (https://github.com/RathoreScripts/UrbanPulse-AI)

---

UrbanPulse AI — Smarter Water Management Through AI and Digital Twin Technology.
