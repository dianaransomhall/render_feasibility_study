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
data = pd.DataFrame({
    'values': [1, 2, 2, 3, 3, 3, 4, 4, 5]
})
app.layout = html.Div([
    html.H1("Payout Calculator for 1 Year Battery Warranty "),
    html.Label("Price Per kWh"),
    dcc.Input(id='price-per-kwh', type='number', value=576 ),
    html.Label("Average Battery Pack Size (kWh)"),
    dcc.Input(id='battery-size-kwh', type='number', value=40),
    html.Label("Target Loss Ratio, %"),
    dcc.Input(id='target-loss-ratio', type='number', value=30, min=0, max=100),
    html.H1(""),
    dcc.Graph(id='histogram'),
    html.Div(id='result-text'),
    html.P("Battery replacements modeled off Recurrent auto's 15,000 EVs users. Link below."),
    html.A("Recurrent Auto: How Long Do Electric Car Batteries Last?", href="https://www.recurrentauto.com/research/how-long-do-ev-batteries-last"),
    html.P("Second use battery availability estimates modeled on EV batteries in CA. Link below."),
    html.A("CA Energy Commision", href="https://www.energy.ca.gov/data-reports/energy-almanac/zero-emission-vehicle-and-infrastructure-statistics/light-duty-vehicle")
])



# Create a callback function
@app.callback(
    [Output('histogram', 'figure'),
     Output('result-text', 'children')],
    [Input('price-per-kwh', 'value'),
     Input('battery-size-kwh', 'value'),
     Input('target-loss-ratio', 'value')]
)
def update_results( price_per_kwh, battery_size_kwh, target_loss_ratio ):
    # Perform your calculations here
    # make target loss ratio into a percent
    target_loss_ratio=target_loss_ratio/100
    # df_by_year = pd.read_csv("/Users/dianaransomhall/Dropbox/Documents/Software/batteryze/batteryze_app/data/df_by_year_unformatted.csv")
    github_csv_url = "https://raw.githubusercontent.com/dianaransomhall/render_feasibility_study/main/data/df_by_year_unformatted.csv"
    df_by_year = pd.read_csv(github_csv_url)
    def calculate_payout(df_by_year,
                         price_per_kwh=576,
                         battery_size_kwh=40,
                         target_loss_ratio=0.2,
                         warranty_period=1):
        df_by_year['price_per_kwh'] = [price_per_kwh] * 13
        df_by_year['battery_size_kwh'] = [battery_size_kwh] * 13
        if "batteries_replaced_weighted" in df_by_year.columns:
            df_by_year['cost_bat_replacement_kwh'] = round((df_by_year["batteries_replaced_weighted"] * price_per_kwh),
                                                           2)
        else:
            df_by_year['Price of Bat Replacement /kWh'] = round(
                (df_by_year["Number Bats Replaced"] * price_per_kwh), 2)

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
            df_by_year["insurance_payout_total"] = battery_size_kwh * df_by_year["payout_per_kwh_1yr"]
            # Target Loss ratio
            df_by_year["premiums_collected_total"]= df_by_year["insurance_payout_total"]/target_loss_ratio
            df_by_year["premium_price"]= df_by_year["premiums_collected_total"]/ df_by_year["vehicle_ca_added"]
        else:
            for i in range(0, len(df_by_year) - warranty_period):
                chunk = df_by_year['Price of Bat Replacement /kWh'][i:i + chunk_size]
                total = round(chunk.sum(), 2)
                sums[str(df_by_year['year'][count - 1])] = total
                count += 1

            sums_df = pd.DataFrame({"year": sums.keys(),
                                    "payout_per_kwh": sums.values()})
            a = list(sums_df['payout_per_kwh'])
            a.append(np.nan)

            df_by_year["Insurance Payout Total /kWh"] = a
            df_by_year["Insurance Payout Total"]= battery_size_kwh * df_by_year["Insurance Payout Total /kWh"]

            #Target Loss ratio
            df_by_year["Premiums Collected Total"]=df_by_year["Insurance Payout Total"]/target_loss_ratio
            df_by_year["Premium $"]= df_by_year["Premiums Collected Total"]/ df_by_year["Bats Under Warranty"]


        return df_by_year


    def format_currency(value):
        if pd.isna(value) or np.isnan(value):
            return "N/A"  # Return a placeholder for np.nan
        return "${:,.2f}".format(round(value))

    def convert_to_int(formatted_str):
        return int(formatted_str.replace(',', ''))


    df_by_year = calculate_payout(df_by_year,
                                  price_per_kwh=price_per_kwh,
                                  battery_size_kwh=battery_size_kwh,
                                  target_loss_ratio=target_loss_ratio,
                                  warranty_period=1)

    # create figure
    # histogram_figure = px.bar(df_by_year, x='premiums_collected_total',
    #                           y='year', orientation='h', title='Premiums Collected by Year')
    histogram_figure = px.bar(df_by_year, x='insurance_payout_total',
                              y='year', orientation='h', title='Insurance Payout')
    histogram_figure.update_xaxes(tickformat="$,.2f",title_text="Total Payout ($)")  # Format the x-axis labels as currency
    histogram_figure.update_yaxes(title_text="Year")
    histogram_figure.update_layout(
        title_text='Total Paid Out By Insurance Yearly',
        title_x=0.5,  # Center the title
        title_font_size=24  # Adjust the font size
    )
    # format data
    def format_data(df_by_year):
        column_mapping = {'perc_EV_replacements': "Bats Replaced %",
                          'perc_EV_nonrecall_replacements': "Bats Replaced, Non-Recall % ) ",
                          'perc_EV_recall': "Bats Replaced, Recall % ",
                          'vehicle_ca_added': "Bats Under Warranty",
                          'vehicle_ca_cum': "Bats Under Warranty Cummulative Sum",
                          'batteries_replaced_weighted': '# Bats Replaced',
                          'batteries_replaced_weighted_cum': "Cummulative Bats Replaced",
                          'price_per_kwh': "Price of Bat Replacement /kWh",
                          'payout_per_kwh_1yr': 'Insurance Payout Total /kWh',
                          'insurance_payout_total': 'Insurance Payout Total',
                          'battery_size_kwh': "Ave. Bat Size (kWh)",
                          "premiums_collected_total":"Premiums Collected Total",
                          "premium_price": "Premium $"
                          }

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
                if col in ["price_per_kwh", 'payout_per_kwh_1yr', 'cost_bat_replacement_kwh',
                           'insurance_payout_total', 'premium_price']:
                    df_by_year[column_mapping[col]] = df_by_year[col].apply(format_currency)
                if col in ["perc_EV_recall", 'perc_EV_replacements', 'perc_EV_nonrecall_replacements']:
                    df_by_year[column_mapping[col]] = df_by_year[col].apply(format_percent)
                df_by_year = df_by_year.drop(columns=[col])

        for col in df_by_year.columns:
            print(col)
            if col in ["# Bats Replaced",
                       'Cummulative Bats Replaced',
                       'batteries_replaced_unweighted',
                       'Bats Under Warranty',
                       'Bats Under Warranty Cummulative Sum']:
                df_by_year[col] = df_by_year[col].apply(format_whole_number)
            print(df_by_year[col][:2])
        return df_by_year

    df_by_year=format_data(df_by_year)

    multi_line_text = f"""
        Expected payout over warranty period of 1 year. Data reflects real numbers of EVs in CA, 
        and warranty initiated in year listed for EVs. Calculations use a rate of battery replacement \n
        that changes between 0.6%-11.2% depending on the year. \n
        ## Calculations
        * Premium:  
          Given a desired loss-ratio, the premium price is calculated as a function of yearly losses.
        For example, if 20% is the target loss-ratio: Premium $ = Insurance Payout Total / .2. 
        * Insurance Payout :
                     The calculation of Insurance Payout is as follows: 
        Insurance Payout Total = Insurance Payout /kWh * Price of Bat Replacement \/kWh \* Ave. Bat Size (kWh)
        """
    result_text = [
        html.Br(),
        html.Br(),
        html.P(dcc.Markdown(multi_line_text)),
        dash_table.DataTable(data=df_by_year[["year",
                                              'Bats Replaced %',
                                              '# Bats Replaced',
                                              'Ave. Bat Size (kWh)',
                                              'Price of Bat Replacement /kWh',
                                              'Bats Under Warranty',
                                              'Insurance Payout Total /kWh',
                                              'Insurance Payout Total',
                                              'Premium $',
                                              ]].to_dict('records'),
                                            page_size=14,
                             style_table={'width': '50%'})  # Set the table width) # records is the orientation
    ]


    return histogram_figure, result_text


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True) # note: , port=8071 port argument allows you to display