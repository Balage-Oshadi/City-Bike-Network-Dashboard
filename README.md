# 🚴‍♂️ City Bike Network Dashboard

An interactive dashboard that visualizes real-time data from the City Bike Network API, including network locations, station availability, and usage trends. Built in Python using **Streamlit**, **Pandas**, and **Plotly**.

---

## Demo App

[[Open in Streamlit](https://city-bike-network-dashboard.streamlit.app)

##  Colab Notebook

[[Open in Colab](https://colab.research.google.com/drive/1ouTfjPPlq0q2lGc0DnG8nrX3M7bednw4?usp=sharing)

---

##  Setup Instructions

This section explains how to set up and run the City Bike Network Dashboard locally or using Docker.

###  Option 1: Run Locally (Recommended for Development)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/Balage-Oshadi/City-Bike-Network-Dashboard.git
cd City-Bike-Network-Dashboard
```

#### Step 2: (Optional) Create and Activate a Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Run the Streamlit App
```bash
streamlit run DashBoardUi.py
```

Open your browser at: [http://localhost:8501](http://localhost:8501)

---

###  Option 2: Run Using Docker (Recommended for Deployment)

#### Step 1: Ensure Docker is Installed  
Download from: https://www.docker.com/products/docker-desktop

#### Step 2: Build and Launch the Container
```bash
docker-compose up --build
```

#### Step 3: Open in Browser
Visit: [http://localhost:8501](http://localhost:8501)

---

 **Note**
- To stop the app: Press `Ctrl + C` or run `docker-compose down`
- Default port is `8501`. Ensure it’s available before starting

---

##  Prerequisite Libraries

This project uses:
- `streamlit`
- `pandas`
- `plotly`
- `reportlab`
- `matplotlib`
- `requests`

(Install via `requirements.txt`)

---

##  Data Source

Data comes from the [CityBikes API](http://api.citybik.es/v2/) — a global dataset of public bike-sharing networks and real-time station availability.

---

##  Reference

This project is part of a learning initiative on dashboard design using real-time public APIs and Python data visualization tools.

---

##  Author

*Oshadi Yashodhika*  
[GitHub](https://github.com/Balage-Oshadi)

---
