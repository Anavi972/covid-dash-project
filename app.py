import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import warnings
import os 

# Suppress FutureWarning from pandas when accessing columns
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIGURATION ---
DATA_URL = 'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv'
LOCAL_FILE = 'dataset/owid-covid-data.csv' 

# --- DATA LOADING AND PREPARATION ---

def load_data():
    """Attempts to load data from URL, falls back to local file if network fails."""
    df = None
    try:
        print(f"Attempting to download data from: {DATA_URL}")
        df = pd.read_csv(DATA_URL)
        print("Data downloaded successfully.")
        
        # LOGIC: Ensure the 'dataset' directory exists before saving
        local_dir = os.path.dirname(LOCAL_FILE)
        if local_dir:
            # os.makedirs(..., exist_ok=True) creates the directory if it doesn't exist.
            os.makedirs(local_dir, exist_ok=True)
            print(f"Ensured directory exists: {local_dir}") 
        
        # Save to local file for future offline use
        df.to_csv(LOCAL_FILE, index=False)
        
    except Exception as e:
        print(f"Error loading data from URL: {e}. Attempting to load from local file: {LOCAL_FILE}")
        try:
            # Load from the correct local path
            df = pd.read_csv(LOCAL_FILE) 
            print("Data loaded from local file successfully.")
        except FileNotFoundError:
            # --- CRITICAL DIAGNOSTIC ADDITION ---
            abs_path = os.path.abspath(LOCAL_FILE)
            print("--------------------------------------------------")
            print("FATAL ERROR: Local data file not found.")
            print(f"Please ensure the file exists at this EXACT path: {abs_path}")
            print("--------------------------------------------------")
            return None
        except Exception as e_local:
            print(f"Error loading local data file: {e_local}")
            return None
    
    if df is not None:
        # Standard Data Cleaning and Feature Engineering
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by=['location', 'date']).reset_index(drop=True)
        # Calculate rolling averages for smoother curves (e.g., 7-day)
        df['new_cases_smoothed'] = df.groupby('location')['new_cases'].transform(lambda x: x.rolling(7).mean())
        df['new_deaths_smoothed'] = df.groupby('location')['new_deaths'].transform(lambda x: x.rolling(7).mean())
        return df

df = load_data()

# Handle case where data loading failed
if df is None:
    print("Application failed to start due to missing data.")
    exit()

# Pre-calculate unique locations and default country
locations = df['location'].unique()
locations.sort()
DEFAULT_LOCATION = 'United States'
DEFAULT_COMPARE_LOCATION = 'Canada'

# --- DATA FOR WORLD MAP (Requires latest metrics only) ---
# Filter out non-country data (continents, income groups) using 'iso_code'
# Note: 'iso_code' is present only for countries in the OWID dataset
df_latest = df[df['iso_code'].notna()].copy() 

# Get the latest data point for each location (country)
df_map = df_latest.sort_values('date').groupby('location').tail(1).reset_index(drop=True)


# --- DASH APP SETUP ---
app = Dash(__name__, title="COVID-19 Dashboard")
server = app.server 

# Define common style settings
CARD_STYLE = 'bg-white p-6 rounded-xl shadow-lg m-4'
TITLE_STYLE = 'text-3xl font-bold mb-4 text-gray-800'
HEADER_STYLE = 'text-xl font-semibold mb-2 text-indigo-700'
MAP_METRIC_OPTIONS = [
    {'label': 'Total Cases per Million', 'value': 'total_cases_per_million'},
    {'label': 'People Fully Vaccinated per Hundred', 'value': 'people_fully_vaccinated_per_hundred'},
    {'label': 'Total Deaths per Million', 'value': 'total_deaths_per_million'}
]

app.layout = html.Div(
    className='min-h-screen bg-gray-100 p-8 font-sans',
    children=[
        # Title Section
        html.Header(
            className='text-center py-6 bg-indigo-700 text-white rounded-xl shadow-2xl mb-8',
            children=[
                html.H1("COVID-19 Global Data Visualization", className='text-4xl md:text-5xl font-extrabold'),
                html.P("Analyzing cases, deaths, and vaccinations across the world (Source: OWID)", className='text-lg mt-2')
            ]
        ),

        # World Map Section 
        html.Div(
            className=CARD_STYLE + ' mb-8',
            children=[
                html.H2("Global Overview: Choropleth Map", className=HEADER_STYLE),
                html.Div(
                    className='flex flex-col md:flex-row items-center justify-start mb-4',
                    children=[
                        html.Label("Map Metric:", className='text-lg font-medium mr-4'),
                        dcc.Dropdown(
                            id='map-metric-dropdown',
                            options=MAP_METRIC_OPTIONS,
                            value='people_fully_vaccinated_per_hundred',
                            clearable=False,
                            className='w-full md:w-1/3 text-gray-900'
                        )
                    ]
                ),
                # WRAP THE MAP IN A LOADING COMPONENT
                dcc.Loading(
                    id="loading-map",
                    type="default",
                    children=dcc.Graph(id='world-map-graph', config={'displayModeBar': False})
                )
            ]
        ),

        # Control Panel (Existing) - UPDATED FOR COUNTRY COMPARISON
        html.Div(
            className=CARD_STYLE + ' flex flex-col md:flex-row items-center justify-between',
            children=[
                html.Div(
                    className='w-full md:w-1/3 p-2',
                    children=[
                        html.Label("Primary Country/Region:", className=HEADER_STYLE),
                        dcc.Dropdown(
                            id='location-dropdown',
                            options=[{'label': loc, 'value': loc} for loc in locations],
                            value=DEFAULT_LOCATION,
                            className='text-gray-900'
                        )
                    ]
                ),
                # NEW SECOND DROPDOWN FOR COMPARISON
                html.Div(
                    className='w-full md:w-1/3 p-2 mt-4 md:mt-0',
                    children=[
                        html.Label("Compare With:", className=HEADER_STYLE),
                        dcc.Dropdown(
                            id='compare-dropdown',
                            options=[{'label': loc, 'value': loc} for loc in locations],
                            value=DEFAULT_COMPARE_LOCATION,
                            className='text-gray-900'
                        )
                    ]
                ),
                html.Div(
                    className='w-full md:w-1/3 p-2 mt-4 md:mt-0',
                    children=[
                        html.Label("Select Metric:", className=HEADER_STYLE),
                        dcc.RadioItems(
                            id='metric-selector',
                            options=[
                                {'label': ' New Cases (7-day Avg) ', 'value': 'new_cases_smoothed'},
                                {'label': ' New Deaths (7-day Avg) ', 'value': 'new_deaths_smoothed'},
                            ],
                            value='new_cases_smoothed',
                            inline=True,
                            className='flex justify-around mt-2 text-lg text-gray-600'
                        )
                    ]
                ),
            ]
        ),

        # Main Visualization Row (Time Series & Key Metrics)
        html.Div(
            className='grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8',
            children=[
                # Time Series Graph (2/3 width on large screens)
                html.Div(
                    className='lg:col-span-2 ' + CARD_STYLE,
                    children=[
                        html.H2(id='timeseries-title', className=HEADER_STYLE),
                        # WRAP THE TIME SERIES GRAPH
                        dcc.Loading(
                            id="loading-timeseries",
                            type="default",
                            children=dcc.Graph(id='timeseries-graph', config={'displayModeBar': False})
                        )
                    ]
                ),
                # Key Metrics (1/3 width on large screens)
                html.Div(
                    className='lg:col-span-1 ' + CARD_STYLE,
                    children=[
                        html.H2("Key Vaccination & Testing Metrics", className=HEADER_STYLE),
                        dcc.Loading(
                            id="loading-metrics",
                            type="default",
                            children=html.Div(id='key-metrics', className='space-y-4 mt-4')
                        )
                    ]
                ),
            ]
        ),

        # Secondary Visualization Row (Vaccination and Testing)
        html.Div(
            className='grid grid-cols-1 md:grid-cols-2 gap-8 mt-8',
            children=[
                html.Div(
                    className=CARD_STYLE,
                    children=[
                        html.H2("Total Vaccinations Per Capita", className=HEADER_STYLE),
                        # WRAP THE VACCINATION GRAPH
                        dcc.Loading(
                            id="loading-vax",
                            type="default",
                            children=dcc.Graph(id='vaccination-graph', config={'displayModeBar': False})
                        )
                    ]
                ),
                html.Div(
                    className=CARD_STYLE,
                    children=[
                        html.H2("Total Tests Per Thousand People", className=HEADER_STYLE),
                        # WRAP THE TESTING GRAPH
                        dcc.Loading(
                            id="loading-tests",
                            type="default",
                            children=dcc.Graph(id='testing-graph', config={'displayModeBar': False})
                        )
                    ]
                )
            ]
        ),
    ]
)

# --- CALLBACKS ---

# 1. Update World Map Graph
@app.callback(
    Output('world-map-graph', 'figure'),
    [Input('map-metric-dropdown', 'value')]
)
def update_world_map(selected_metric):
    # Determine color scale label
    metric_label = [opt['label'] for opt in MAP_METRIC_OPTIONS if opt['value'] == selected_metric][0]

    # Create the choropleth map
    fig = px.choropleth(
        df_map, 
        locations='iso_code', 
        color=selected_metric,
        hover_name='location',
        color_continuous_scale=px.colors.sequential.Plasma,
        labels={selected_metric: metric_label},
        projection='natural earth'
    ).update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_colorbar=dict(title=metric_label),
    )
    
    return fig


# 2. Update Time Series Graph (MODIFIED FOR COMPARISON)
@app.callback(
    [Output('timeseries-graph', 'figure'),
     Output('timeseries-title', 'children')],
    [Input('location-dropdown', 'value'),
     Input('compare-dropdown', 'value'), # ADDED COMPARISON DROPDOWN
     Input('metric-selector', 'value')]
)
def update_timeseries_graph(selected_location, compare_location, selected_metric):
    
    # Concatenate the data for the two selected countries
    combined_df = df[df['location'].isin([selected_location, compare_location])]
    
    # Determine titles and labels
    metric_map = {
        'new_cases_smoothed': ('New COVID-19 Cases (7-Day Average)', 'Daily Cases'),
        'new_deaths_smoothed': ('New COVID-19 Deaths (7-Day Average)', 'Daily Deaths')
    }
    title, y_label = metric_map.get(selected_metric, ('Data Trend', 'Value'))
    
    # Use Plotly Express 'line' to plot multiple lines based on 'location'
    fig = px.line(
        combined_df,
        x='date',
        y=selected_metric,
        color='location', # CRITICAL: use 'location' to separate lines
        title=None, 
        labels={'date': 'Date', selected_metric: y_label, 'location': 'Country'},
        color_discrete_sequence=['#4c51bf', '#f59e0b'] # Different colors for comparison
    ).update_layout(
        margin={"r": 10, "t": 10, "l": 10, "b": 10},
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_title=None,
        yaxis_tickformat='.2s',
        legend_title_text='Country'
    )
    
    return fig, f"Comparison: {selected_location} vs. {compare_location} ({title})"


# 3. Update Key Metrics and Side Graphs (Existing - Only relies on primary location)
@app.callback(
    [Output('key-metrics', 'children'),
     Output('vaccination-graph', 'figure'),
     Output('testing-graph', 'figure')],
    [Input('location-dropdown', 'value')]
)
def update_key_metrics(selected_location):
    filtered_df = df[df['location'] == selected_location]
    
    # --- 2.1 Key Metrics ---
    latest_data = filtered_df.iloc[-1]
    
    # Use .get() for safe access in case a column is missing
    total_cases = latest_data.get('total_cases', 0)
    total_deaths = latest_data.get('total_deaths', 0)
    fully_vaccinated = latest_data.get('people_fully_vaccinated', 0)
    population = latest_data.get('population', 1)
    
    # Calculate Ratios
    vax_percentage = (fully_vaccinated / population) * 100 if fully_vaccinated else 0
    
    # Function to format large numbers
    def format_number(n):
        if pd.isna(n):
            return "N/A"
        return f"{n:,.0f}"

    metrics_html = [
        html.Div(f"Total Cases: {format_number(total_cases)}", className='text-lg p-2 bg-indigo-50 border-l-4 border-indigo-500'),
        html.Div(f"Total Deaths: {format_number(total_deaths)}", className='text-lg p-2 bg-red-50 border-l-4 border-red-500'),
        html.Div(f"Fully Vaccinated: {format_number(fully_vaccinated)}", className='text-lg p-2 bg-green-50 border-l-4 border-green-500'),
        html.Div(f"Fully Vax Rate: {vax_percentage:.2f}%", className='text-xl font-bold p-2 bg-yellow-50 border-l-4 border-yellow-500'),
    ]

    # --- 2.2 Vaccination Graph ---
    vax_fig = px.line(
        filtered_df,
        x='date',
        y='people_fully_vaccinated_per_hundred',
        labels={'people_fully_vaccinated_per_hundred': 'Fully Vaccinated (%)', 'date': 'Date'},
        color_discrete_sequence=['#10b981'] 
    ).update_layout(
        margin={"r": 10, "t": 10, "l": 10, "b": 10},
        plot_bgcolor='white', paper_bgcolor='white', xaxis_title=None
    )

    # --- 2.3 Testing Graph ---
    testing_fig = px.line(
        filtered_df,
        x='date',
        y='new_tests_smoothed_per_thousand',
        labels={'new_tests_smoothed_per_thousand': 'New Tests (per 1k)', 'date': 'Date'},
        color_discrete_sequence=['#f97316'] 
    ).update_layout(
        margin={"r": 10, "t": 10, "l": 10, "b": 10},
        plot_bgcolor='white', paper_bgcolor='white', xaxis_title=None
    )

    return metrics_html, vax_fig, testing_fig

# --- RUN SERVER ---

if __name__ == '__main__':
    app.run(debug=True)
