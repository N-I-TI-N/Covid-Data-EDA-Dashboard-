from pymongo import MongoClient
import pandas as pd
import random

# creating a class to read data from mongodb databse stored in mongodb atlas cloud
class MongoRepository:
    
    def __init__(
        self,
        client=MongoClient("mongodb+srv://guest_user:j5g8GMbg44zliBkv@mydatabase.wo9j7bt.mongodb.net/?retryWrites=true&w=majority"),
        db = "HR_db",
        collection = "applicants_data"
    ):
        """init
        This method establishes the connection to the database and "self.collection" attribute will be available throughout the 
        class instance and holds the data of "job-applicants"
        """
        self.collection = client[db][collection]
        
        
    def get_nationality_data(self):
        result=self.collection.aggregate(
            [
                {
                    "$group" : {"_id" : "$country",
                                "count": {"$count": {}} }
                }
            ]
        )
        df_nationality=pd.DataFrame(result).rename({"_id": "country_iso3"}, axis="columns")
        return df_nationality
    
    
    def get_age_data(self):
        result=self.collection.aggregate(
            [
                {
                    "$project" : {
                        "age" : {
                            "$dateDiff" : {
                                "startDate" : "$birthday",
                                "endDate" : "$$NOW",
                                "unit" : "year"
                            }
                        }
                    }
                }
            ]
        )
        df_ages=pd.DataFrame(result)["age"]
        return df_ages
    
   
    def get_gender_data(self):
        result=self.collection.aggregate(
            [
               {
                   "$group" : { "_id" : "$gender",
                               "count" : {"$count" : {}}
                   }
               } 
            ]
        )
        df_gender=pd.DataFrame(result).rename({"_id" : "gender"}, axis="columns")
        df_gender["applicants_pct"] = (df_gender["count"]/df_gender["count"].sum())*100
        return df_gender
    
    
    # Helper function for get_edu_data method
    def __custom_sort_key(self, data):
        degrees=["Bachelor's Degree","Master's Degree","Doctorate","Post Doctorate"]
        mapping = {i:j for j, i in enumerate(degrees)}
        sort_order= [mapping[i] for i in data]
        return sort_order
    
    
    def get_edu_data(self):
        result=self.collection.aggregate(
            [
                {
                    "$group" : { "_id" : "$highestDegree",
                                "count" : {"$count":{}}            
                    }
                }
            ]
        )
        df_edu=pd.DataFrame(result).rename({"_id": "HighestDegreeEarned"},axis="columns")
        df_edu.sort_values(by="HighestDegreeEarned", key=self.__custom_sort_key, inplace=True)
        return df_edu
    
    
    def get_quiz_completion_data(self):
        result=self.collection.aggregate(
            [
                {
                    "$group" : {"_id" : "$quizStatus",
                                "count" : {"$count":{}}
                    }
                }
            ]
        )
        df_quiz_status=pd.DataFrame(result).rename({"_id":"Quiz_Status"},axis="columns")
        df_quiz_status["applicants_pct"] = (df_quiz_status["count"]/df_quiz_status["count"].sum())*100
        return df_quiz_status
    
    
    def get_dailay_no_quiz_applicants(self):
        result = self.collection.aggregate(
            [
                {"$match" : {"quizStatus" : "incomplete"}},
                {
                    "$group" : {"_id" : {"$dateTrunc" : { "unit" : "day", "date" : "$createdAt" }},
                                "No_Quiz_Applicants" : {"$count" : {}}

                    }
                }
            ]
        )
        df_no_quiz = (
            pd.DataFrame(result)
            .rename({"_id" : "Date"},axis="columns")
            .set_index("Date")
            .sort_index()
            .squeeze()
        )
        return df_no_quiz
    
    

#-------------------------------------------------------------------------------------------------------------------------------------
class Experiment:
    def __init__(
        self,
        client=MongoClient("mongodb+srv://nitin:l3XrffJAQda52xrv@mydatabase.wo9j7bt.mongodb.net/?retryWrites=true&w=majority")
    ):
        self.collection=client["HR_db"]["applicants_data"]
        self.backup_collection=client["HR_db"]["data_backup"]
    
    
    def __extract_data(self, days):
        """Helper funtion for ETL process"""
        end_date = pd.to_datetime("2023-09-30")
        start_date= end_date - pd.DateOffset(days=days) 
        query = {
        "createdAt" : {"$gte" : start_date, "$lte" : end_date},
        "quizStatus" : "incomplete"
        }
        result=self.collection.find(query)
        obs = list(result)
        return obs
        
    
    def __update_applicants_data(self, updated_data):
        """Helper funtion for ETL process"""
        # Initializing counters
        documents_matched=0
        documents_updated=0

        for doc in updated_data:
            result=self.collection.update_one(
                filter = {"_id" : doc["_id"]},
                update = {"$set" : doc}
            )
            # updating counters
            documents_matched = documents_matched + result.matched_count
            documents_updated = documents_updated + result.modified_count
        return f"documents_matched: {documents_matched}, documents_updated: {documents_updated}" 
   

    def ETL(self, days):
        obs = self.__extract_data(days=days) 
        random.seed(42)                                 # To reproduce same results every time
        random.shuffle(obs)
        index = len(obs)//2                             # Get index position of doc at observations halfway point
        for doc in obs[:index]:
            doc["InExperiment"] = True
            doc["group"] = "no email (control)"
        for doc in obs[index:]:
            doc["InExperiment"] = True
            doc["group"] = "email (treatment)"
        result = self.__update_applicants_data(updated_data = obs)                
        return f"ETL Process Completed: {result}"
        
    
    def run_synthetic_experiment(self):   
        # get data for applicants present in the experiment
        query = {"InExperiment" : True}
        result = self.collection.find(query)
        data = list(result)
        # randomly modify the "quizStatus" of applicants
        status=["complete","incomplete"]
        w=[3,1]
        for doc in data:
            if doc["group"]=="email (treatment)":    
                doc["quizStatus"]=random.choices(status, weights=w)[0]
            else:
                doc["quizStatus"]=random.choice(status)    
        # update the results of experiment into the database
        new_result = self.__update_applicants_data(updated_data=data)     
        return new_result
    
    def get_experiment_results(self):
        query = {"InExperiment" : True}
        result = self.collection.find(query)
        df=pd.DataFrame(result)
        data = pd.crosstab(
            index = df["group"],
            columns = df["quizStatus"],
            normalize = False
        )
        return data
    
    
    def reset_data(self):
        """
        This function reset any changes made to database during experiment 
        """
        self.collection.delete_many({})
        data = self.backup_collection.find({})
        self.collection.insert_many(data)
        return "Data Reset Complete"
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    
    
    
    
    
    
    