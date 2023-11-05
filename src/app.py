import dash
from dash import html, dash_table, dcc
from dash.dependencies import Input, Output
import numpy as np
import plotly.express as px
import pandas as pd

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server
# Define the app layout
app.layout = html.Div([
    html.H1("Payout Calculator for 1 Year Battery Warranty "),
    html.Label("Price Per kWh"),
    dcc.Input(id='price-per-kwh', type='number', value=576 ),
    html.Div(id='result-text'),
    html.P("Battery replacements modeled off Recurrent auto's 15,000 EVs users. Link below."),
    html.A("Recurrent Auto: How Long Do Electric Car Batteries Last?", href="https://www.recurrentauto.com/research/how-long-do-ev-batteries-last"),
    html.P("Second use battery availability estimates modeled on EV batteries in CA. Link below."),
    html.A("CA Energy Commision", href="https://www.energy.ca.gov/data-reports/energy-almanac/zero-emission-vehicle-and-infrastructure-statistics/light-duty-vehicle")
])



# Create a callback function
@app.callback(
    Output('result-text', 'children'),
    [Input('price-per-kwh', 'value')]
)
def update_results( price_per_kwh):
    # Perform your calculations here

    # df_by_year = pd.read_csv("/Users/dianaransomhall/Dropbox/Documents/Software/batteryze/batteryze_app/data/df_by_year_unformatted.csv")
    github_csv_url = "https://raw.githubusercontent.com/dianaransomhall/render_feasibility_study/main/data/df_by_year_unformatted.csv"
    df_by_year = pd.read_csv(github_csv_url)
    def calculate_payout(df_by_year,
                         price_per_kwh=576,
                         warranty_period=1):

        if "batteries_replaced_weighted" in df_by_year.columns:
            df_by_year['price_per_kwh'] = [price_per_kwh] * 13
            df_by_year['cost_bat_replacement_kwh'] = round((df_by_year["batteries_replaced_weighted"] * price_per_kwh),
                                                           2)
        else:
            df_by_year['price_per_kwh'] = [price_per_kwh] * 13
            df_by_year['Price of Battery Replacement /kWh'] = round(
                (df_by_year["Number Batteries Replaced"] * price_per_kwh), 2)

        warranty_period = 1
        chunk_size = 1
        sums = {}
        count = 1

        # get price per kwh
        if 'cost_bat_replacement_kwh' in df_by_year.columns:
            for i in range(0, len(df_by_year) - warranty_period):
                chunk = df_by_year['cost_bat_replacement_kwh'][i:i + chunk_size]
                total = round(chunk.sum(), 2)
                sums[str(df_by_year['year'][count - 1])] = total
                count += 1
            sums_df = pd.DataFrame({"year": sums.keys(), "payout_per_kwh": sums.values()})
            a = list(sums_df['payout_per_kwh'])
            a.append(np.nan)

            df_by_year["payout_per_kwh_1yr"] = a
        else:
            for i in range(0, len(df_by_year) - warranty_period):
                chunk = df_by_year['Price of Battery Replacement /kWh'][i:i + chunk_size]
                total = round(chunk.sum(), 2)
                sums[str(df_by_year['year'][count - 1])] = total
                count += 1
            sums_df = pd.DataFrame({"year": sums.keys(), "payout_per_kwh": sums.values()})
            a = list(sums_df['payout_per_kwh'])
            a.append(np.nan)

            df_by_year["Insurance Payout Total /kWh"] = a

        return df_by_year


    def format_currency(value):
        if pd.isna(value) or np.isnan(value):
            return "N/A"  # Return a placeholder for np.nan
        return "${:,.2f}".format(round(value))

    def convert_to_int(formatted_str):
        return int(formatted_str.replace(',', ''))

    # df_by_year["Number Batteries Replaced"] = df_by_year["Number Batteries Replaced"].apply(convert_to_int)
    # df_by_year['Price of Battery Replacement /kWh'] = [price_per_kwh] * df_by_year.shape[0]
    df_by_year = calculate_payout(df_by_year, price_per_kwh=price_per_kwh, warranty_period=1)

    # format data
    def format_data(df_by_year):
        column_mapping = {'perc_EV_replacements': "All Batteries Replaced %",
                          'perc_EV_nonrecall_replacements': "Batteries Replace, Non-Recall % ) ",
                          'perc_EV_recall': "Batteries Replaced, Recall % ",
                          'vehicle_ca_added': "2nd Use Batteries Made Available by Year in CA",
                          'vehicle_ca_cum': "2nd Use Batteries Available in CA",
                          'batteries_replaced_weighted': 'Number Batteries Replaced',
                          'batteries_replaced_weighted_cum': "Cummulative Batteries Replaced",
                          'price_per_kwh': "Price of Battery Replacement /kWh",
                          'payout_per_kwh_1yr': 'Insurance Payout Total /kWh'}

        # Define a custom formatting function
        def format_currency(value):
            return "${:,.2f}".format(value)

        def format_percent(value):
            return "{:.1f}%".format(value * 1)

        def format_whole_number(value):
            return "{:,}".format(round(value))

        # Apply formatting and rename columns
        for col in df_by_year.columns:
            if col in column_mapping:
                df_by_year[column_mapping[col]] = df_by_year[col]
                if col in ["price_per_kwh", 'payout_per_kwh_1yr', 'cost_bat_replacement_kwh']:
                    df_by_year[column_mapping[col]] = df_by_year[col].apply(format_currency)
                if col in ["perc_EV_recall", 'perc_EV_replacements', 'perc_EV_nonrecall_replacements']:
                    df_by_year[column_mapping[col]] = df_by_year[col].apply(format_percent)
                df_by_year = df_by_year.drop(columns=[col])

        for col in df_by_year.columns:
            print(col)
            if col in ["Number Batteries Replaced",
                       'Cummulative Batteries Replaced',
                       'batteries_replaced_unweighted',
                       '2nd Use Batteries Available in CA',
                       '2nd Use Batteries Made Available by Year in CA']:
                df_by_year[col] = df_by_year[col].apply(format_whole_number)
            print(df_by_year[col][:2])
        return df_by_year

    df_by_year=format_data(df_by_year)

    multi_line_text = f"""
        Expected payout over warranty period of 1 year. Data reflects real numbers of EVs in CA,
        and warranty initiated in year listed for EVs. Calculations use a rate of battery replacement 
        that changes between 0.6%-11.2% depending on the year. """
    result_text = [
        html.Br(),
        html.Br(),
        html.P(multi_line_text),
        dash_table.DataTable(data=df_by_year[["year",
                                              'All Batteries Replaced %',
                                              'Number Batteries Replaced',
                                              'Price of Battery Replacement /kWh',
                                              '2nd Use Batteries Available in CA',
                                              'Insurance Payout Total /kWh',
                                              ]].to_dict('records'), page_size=10) # records is the orientation
    ]



    return result_text


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)