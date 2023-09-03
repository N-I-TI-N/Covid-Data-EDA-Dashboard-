from database import MongoRepository, Experiment

import plotly.express as px
from statsmodels.stats.power import GofChisquarePower
import matplotlib.pyplot as plt
import scipy
import numpy as np
import io
import base64
from scipy.stats import chi2_contingency


class MakeVisualizations:
    
    def __init__(self, repo=MongoRepository()):
        """init
        This method intializes the MongoRepository class instance to be used by MakeVisualizations class
        """
        self.repo = repo
        
    def build_national_choropleth(self):
        df_nationality = self.repo.get_nationality_data()
        fig= px.choropleth(
            data_frame=df_nationality,
            locations="country_iso3",
            
            color="count",
            projection="natural earth",
            color_continuous_scale = px.colors.sequential.Oranges,
            title= "Job Applicants Nationality"
        )
        return fig

    def build_age_histogram(self):
        df_ages = self.repo.get_age_data()
        fig= px.histogram(
            x=df_ages,
            nbins=20,
            title="Distribution of Job Applicants Ages",
        ).update_layout(xaxis_title="Ages", yaxis_title="Frequency [count]")
        return fig
    
    def build_gender_bar_graph(self):
        df_gender = self.repo.get_gender_data()
        fig= px.bar(
            df_gender,
            x="gender",
            y="applicants_pct",
            title= "Distribution of Job Applicants Gender"
        ).update_layout(yaxis_title="Frequency [%]")
        return fig
    
    def build_edu_bar_graph(self):
        df_edu = self.repo.get_edu_data()
        fig = px.bar(
            df_edu,
            x="count",
            y="HighestDegreeEarned",
            title="Job Applicants : Education levels"
        ).update_layout(xaxis_title="Frequency [count]")
        return fig
    
    def build_quiz_status_graph(self):
        df_quiz_status = self.repo.get_quiz_completion_data()
        fig = px.bar(
            df_quiz_status,
            x="Quiz_Status",
            y="applicants_pct",
            title="Job Applicants : Screening Quiz Status"
        ).update_layout(yaxis_title="Frequency [%]")
        return fig
    
    def build_normal_pdf(self, days):
        df_no_quiz = self.repo.get_dailay_no_quiz_applicants()
        sum_mean = days * df_no_quiz.mean() 
        sum_std = days * df_no_quiz.std()
        # creating arrays
        x=np.linspace(sum_mean-300,sum_mean+300)                     # Defining plot range for x axis
        pdf= scipy.stats.norm.pdf(
            x, 
            loc = sum_mean,                    # loc refers to mean of normal distribution
            scale = sum_std                    # scale refers to standard deviation of normal distribution
        )
        # creating the figure   
        plt.figure()
        plt.plot(x,pdf)
        plt.title(f"Distribution of {days} -day total number of No-Quiz Applicants")
        plt.xlabel("No-Quiz Applicants")
        plt.ylabel("Frequency [%]")
        # Save the plot image in memory
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        # Encode the image data as base64 so that it can be used by HTML
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        return f"data:image/png;base64,{image_base64}"
    

class CalculateStatistics:
    
    def __init__(self, repo=MongoRepository()):
        """init
        This method intializes the MongoRepository class instance to be used by CalculateStatistics class
        """
        self.repo = repo
               
    def calculate_sample_size(self, effect_size):
        alpha = 0.05  # Significance level
        power = 0.80  # Statistical power
        # Calculate required sample size
        one_sample_size = GofChisquarePower().solve_power(effect_size=effect_size, alpha=alpha, power=power)
        Sample_Size = round(2*one_sample_size)
        return Sample_Size
       
    def calculate_probability(self, sample_size, days):
        df_no_quiz = self.repo.get_dailay_no_quiz_applicants()
        sum_mean = days * df_no_quiz.mean() 
        sum_std = days * df_no_quiz.std()
        prob_req_sample_size_or_fewer = scipy.stats.norm.cdf(
            sample_size,
            loc = sum_mean,                 
            scale = sum_std    
        )
        prob_req_sample_size_or_greater = 1-prob_req_sample_size_or_fewer
        return round(prob_req_sample_size_or_greater,4)
    

    
class ConductExperiment:
    def __init__(self, repo=Experiment()):
        self.repo=repo
     
    def run_experiment(self, days):
        self.repo.ETL(days=days)
        self.repo.run_synthetic_experiment()
        results = self.repo.get_experiment_results()
        self.repo.reset_data()
        return results
    
    def build_experiment_result_bar_graph(self, data):
        fig = px.bar(
            data,
            barmode="group",
            title = "Screening Test Completion by Group"
        )
        fig.update_layout(
            xaxis_title="Group",
            yaxis_title="Frequency [count]",
            legend={"title": "Quiz Status"}
        )
        return fig
    
    def run_chi_square(self, data):
        chi2_stat, p_val, dof, expected = chi2_contingency(data.values)
        return p_val, dof, chi2_stat
        
    
    
    
    
    
    
    
    
    
            
            
        
        
        
        
        
        
        
        
        
        
        
        
        