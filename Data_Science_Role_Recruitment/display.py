from dash import Dash, html, dcc, Input, Output, State
from business import MakeVisualizations, CalculateStatistics, ConductExperiment

# creating a MakeVisualizations instance
mv = MakeVisualizations()
# creating a CalculateStatistics instance
cs = CalculateStatistics()
# creating a CalculateStatistics instance
cx = ConductExperiment()

# Instantiaitng a dash application named "app"
app = Dash(__name__)
server = app.server

# Creating the layout of web application
app.layout = html.Div(
    [
        html.H1("Applicants Demographics"),
        dcc.Dropdown(
            options=["Nationality","Age","Gender","Education","Quiz-Completion"],
            value="Nationality",
            id="demographics-plots-dropdown"
        ),
        html.Div(id="demographics-plots-display"),    # used as a placeholder to put graphs later
        
        html.H1("Preparing Experiment"),
        html.H3("Expected Effect Size: "),
        dcc.Slider(
            id = "effect_size_slider",
            min=0.1,
            max=1,
            step=0.1,
            value=0.2
        ),
        html.Div(id="effect-size-slider-output"),
        
        html.H3("Select Number of Days: "),
        dcc.Slider(
            id = "days_slider",
            min=2,
            max=20,
            step=1,
            value=15
        ),
        html.Img(id="days-pdf-output", src="", style={"width": "35%"}),
        html.Div(id="days-prob-output"),
            
        html.H1("Conduct Experiment"),
        html.Div(
            style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',            
            },
            children=[html.Button("Run Experiment", id="experiment_button", n_clicks=0)]
        ),
        html.Div(id="experiment-result-display")        
    ]
)

# creating callback to serve applicants demographics
@app.callback(
    Output("demographics-plots-display", "children"),
    Input("demographics-plots-dropdown", "value")
)
def demographic_graph(graph_name):
    """
    Serves Applicants Demographics Visualization
    """
    fig=None
    if graph_name == "Nationality":
        fig = mv.build_national_choropleth()
    elif graph_name == "Age":
        fig = mv.build_age_histogram()
    elif graph_name == "Gender":   
        fig = mv.build_gender_bar_graph()
    elif graph_name == "Education":   
        fig = mv.build_edu_bar_graph()
    elif graph_name == "Quiz-Completion":   
        fig = mv.build_quiz_status_graph()        
    return dcc.Graph(figure=fig)
    
    
# creating callback to serve effect-size-slider-output
@app.callback(
    Output("effect-size-slider-output", "children"),
    Input("effect_size_slider", "value")
)
def display_sample_size(effect_size):
    sample_size = cs.calculate_sample_size(effect_size)
    text = f"To detect an effect size of {effect_size}, you would need {sample_size} observations"
    return html.Div(text)


# creating callback to serve days-pdf-output
@app.callback(
    Output("days-pdf-output", "src"),
    Input("days_slider", "value")
)
def diplay_pdf_graph(days):
    data_uri = mv.build_normal_pdf(days)
    return data_uri


# creating callback to serve days-prob-output
@app.callback(
    Output("days-prob-output", "children"),
    Input("effect_size_slider", "value"),
    Input("days_slider", "value")
)
def display_probability(effect_size, days):
    sample_size = cs.calculate_sample_size(effect_size)
    probability = cs.calculate_probability(sample_size, days)
    text = f"The Probability of getting {sample_size} Applicants in {days} days is : {probability}"
    return html.Div(text)
    
    
# creating callback to server experiment results
@app.callback(
    Output("experiment-result-display", "children"),
    Input("experiment_button", "n_clicks"),
    State("days_slider", "value")
)
def update_results(n_clicks, days):
    if n_clicks==0:
        return html.Div()
    else:
        # conduct experiment and get results
        result = cx.run_experiment(days=days)
        # make visualization
        fig = cx.build_experiment_result_bar_graph(data = result)
        # Run chi-square-test
        p_val, dof, chi2_stat = cx.run_chi_square(data = result)
        return html.Div(
            [
                html.H2("Observations:"),
                dcc.Graph(figure=fig),
                html.H2("Chi-Square Test for Independence:"),
                html.H3(f"p-value: {p_val}"),
                html.H3(f"Degrees of Freedom: {dof}"),
                html.H3(f"Chi-Square Statistics: {chi2_stat}")
            ]
        )
    

#if __name__ == '__main__':
#    app.run_server(debug=True)




    
    
    
    
    
    
    
    
    
    
    
    
    
    
