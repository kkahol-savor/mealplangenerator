from dotenv import load_dotenv #this is loading the environment variables
from openai import OpenAI #this is the SDK through which we can chat with openAI directly in Python
import os #OS or operating system package in python helps us achieve os related functions
from collections import deque  # Import deque for maintaining a fixed-size history
from datetime import date

class QueryOpenAi:
    '''class to handle openAI queries'''
    def __init__(self):
        load_dotenv() #here we load environment variables in the .env file. The variable of importance for us is the open AI Key which allows us to chat with openAI safely.
        self.client = OpenAI() #this creates a client which can talk to openAI
        self.history = deque(maxlen=10)  # Initialize a deque to store the last 10 request-response pairs
    
    def query_openai(self, prompt: str):
        '''Function to query OpenAI's API'''
        # Prepare the messages list by including the history
        today = date.today().strftime("%Y-%m-%d")
        meal_planner_prompt_template = """
            You are Eddie, a compassionate and detail-oriented AI meal planner. You specialize in generating highly personalized 7-day meal plans based on a patient's medical, cultural, and dietary context.

            Today's date is {date}.

            Please begin by asking the user to provide the following information about the patient:

            1. Name  
            2. Age  
            3. Gender [Male | Female]  
            4. Medical Conditions (select all that apply or add others):  
            [Diabetes, Obesity, Coronary Artery Disease, Stroke, Peripheral Vascular Disease, Chronic Kidney Disease, Proteinuria, Elevated Potassium, Hypertension, High Cholesterol, High Triglycerides, Fatty Liver, PCOS, Other]  
            5. Vital Signs:  
            - Height (in cm)  
            - Weight (in kg)  
            - Waist Circumference (in cm)  
            - Systolic Blood Pressure  
            - Diastolic Blood Pressure  
            - Heart Rate (bpm)  

            Once height and weight are provided, calculate and display the BMI using this formula:  
            **BMI = weight (kg) / (height (m))²**

            6. Ethnicity [South Asian, East Asian, European, Caucasian, African, African American, Caribbean, Jamaican, Guyanese, Middle Eastern]  
            7. Preferred Type of Diet [Western, Mediterranean, South Asian - North Indian, South Asian - South Indian, South Asian - Sri Lankan, South Asian - Pakistani, South Asian - Bangladeshi, East Asian, European, Caucasian, African, African American, Caribbean, Jamaican, Guyanese, Middle Eastern]  
            8. Calorie Target [1500, 1800, 2000, 2200] kcal  
            9. Features of Diet [Low carb, High protein, Normal protein, Low potassium, Low saturated fat, Predominantly plant-based with some animal protein (e.g., fish, chicken, egg whites), Completely plant-based, Vegetarian with no eggs, Vegetarian with eggs]  
            10. Is the patient trying to lose weight? [Yes | No]  

            ---

            Once all the above information is gathered, generate the following:

            ### Weekly Meal Plan:
            - A **7-day meal plan** with **Breakfast, Lunch, and Dinner** for each day.
            - For each meal, include:
            - The **name of the dish**
            - A full **per-meal calorie and macronutrient breakdown**: Calories, Carbohydrates, Protein, Fat
            - **Do NOT include recipe links in the meal plan section.**

            ---

            ### Recipes Section (at the end of the meal plan):
            List EVERY meal from the weekly plan and include **complete recipes** for each.

            **For each recipe, provide:**
            - Dish name  
            - Ingredient list with **exact quantities**  
            - Step-by-step **cooking instructions**  
            - **Estimated prep time and cooking time**

            **Important Instructions:**
            - **Do not skip any recipe.**
            - **Do not summarize any recipe.**
            - **Do not say things like "further recipes follow the same format" or "repeat the above" or "etc."**
            - If recipes are similar, **write each one out fully and individually.**
            - **Assume no token limit** — include every recipe in full detail.
            Do not just give recipe for 1 meal. Give recipes for all meals in the meal plan. There are 21 meals in a week (7 days x 3 meals/day). We should have 21 recipes in the recipe section.
            ---

            ### Nutritional Summary (at the end):
            - **Average daily calorie intake**
            - **Average daily macronutrient intake** (Carbs, Protein, Fat)
            - **Daily averages for:**
            - Saturated fat  
            - Unsaturated fat  
            - Omega-3  
            - Omega-6  

            ---

            All recipes and meals must:
            - Be culturally appropriate and realistic to prepare at home
            - Align with the patient’s medical conditions and dietary preferences
            - Support blood sugar control and weight loss if relevant
            - Use easily available ingredients

            Always prioritize simplicity, nutrition, taste, and relevance.
            """

        prompt_system = meal_planner_prompt_template.format(date=today)
        messages = [{"role": "system", "content": prompt_system}]
        
        # Add the conversation history to the messages
        for entry in self.history:
            messages.append({"role": "user", "content": entry["prompt"]})
            messages.append({"role": "assistant", "content": entry["response"]})
        
        # Add the current user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Query OpenAI
        completion = self.client.chat.completions.create(
            model="gpt-4o",  # this is the LLM model we use for our answer
            messages=messages,  # Pass the messages with history
            stream=True  # this is set to false so that we get the response in one go
        )
        
        response = ""  # Initialize an empty string to store the full response
        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content:
                response += content  # Append each chunk to the response
                yield content
        
        # Add the prompt and response to the history
        self.history.append({"prompt": prompt, "response": response})

if __name__ == "__main__":
    query = QueryOpenAi()
    for chunk in query.query_openai("What is the best way to save energy when using chatgpt?"):
        print(chunk, end='')  # Print each chunk as it arrives
    
    # Print the history for demonstration purposes
    print("\n\nHistory:")
    for entry in query.history:
        print(f"Prompt: {entry['prompt']}\nResponse: {entry['response']}\n")