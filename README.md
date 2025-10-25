🌍 COVID-19 Global Data Visualization Dashboard

This project is an interactive dashboard built using Python and Dash (Plotly) for visualizing global COVID-19 data, including cases, deaths, and vaccination rates, sourced from Our World in Data (OWID).

✨ Features

The dashboard provides real-time analysis with the following key features:

Global Choropleth Map: An interactive world map showing the latest available metrics (Cases per Million, Deaths per Million, or Fully Vaccinated per Hundred) for every country.

Country Comparison: Allows users to select two countries simultaneously to compare their 7-day rolling averages for new cases or deaths on a single time series chart.

Key Metrics: Displays the latest total cases, total deaths, total fully vaccinated people, and the final vaccination rate for the selected primary country.

Data Persistence: The application attempts to download the latest data from the OWID GitHub repository on startup, saving a local copy (dataset/owid-covid-data.csv) as a fallback for offline or restricted network access.

🚀 Installation and Setup

Prerequisites

Python 3.8+

A stable internet connection for the initial data download.

Steps

Clone the Repository:

git clone [https://github.com/Anavi972/covid-dash-project.git](https://github.com/Anavi972/covid-dash-project.git)
cd covid-dash-project


Create a Virtual Environment (Recommended):

# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate


Install Dependencies:
Install all required Python packages listed in requirements.txt.

pip install -r requirements.txt


Run the Application:
Start the Dash server.

python app.py


The application will automatically attempt to open in your web browser at http://127.0.0.1:8050/. If it doesn't open automatically, navigate to the URL manually.

📊 Data Source

The data used in this dashboard is provided by Our World in Data (OWID) and is refreshed daily from their dedicated GitHub repository.

Source Repository: https://github.com/owid/covid-19-data

Direct CSV URL: https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv

⚙️ Project Structure

covid-dash-project/
├── app.py              # Main Python Dash application file
├── requirements.txt    # List of required Python packages (Dash, Pandas, Plotly)
├── .gitignore          # Ignores venv/ and the downloaded dataset/ folder
└── README.md           # Project documentation (this file)
└── dataset/
    └── owid-covid-data.csv # Downloaded data (Ignored by Git)

