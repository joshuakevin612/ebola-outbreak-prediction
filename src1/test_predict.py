print("TEST SCRIPT STARTED")

from predict import load_model, predict_risk


# Load the trained model
model = load_model()

print("Model loaded successfully!")


# Relatively low-risk test patient
patient = {
    "Age": 22,
    "Gender": "Female",
    "Weight_kg": 58,
    "Occupation": "Student",
    "Region": "Urban Zone",
    "Urban_Rural": "Urban",

    "Fever": 0,
    "Body_Temperature": 36.7,
    "Headache": 0,
    "Fatigue": 0,
    "Muscle_Pain": 0,
    "Weakness": 0,
    "Sore_Throat": 0,
    "Chills": 0,
    "Loss_of_Appetite": 0,
    "Vomiting": 0,
    "Diarrhea": 0,
    "Nausea": 0,
    "Abdominal_Pain": 0,
    "Bleeding_Symptoms": 0,
    "Skin_Rash": 0,
    "Eye_Redness": 0,
    "Respiratory_Difficulty": 0,
    "Dehydration_Level": 1,

    "Blood_Pressure": 120,
    "Heart_Rate": 72,
    "Oxygen_Saturation": 99,

    "Contact_With_Patient": 0,
    "Travel_History": 0,
    "Visited_Outbreak_Region": 0,
    "Animal_Exposure": 0,
    "Healthcare_Worker": 0,
    "Funeral_Attendance": 0,
    "Household_Exposure": 0,
    "Days_Since_Exposure": 0,

    "Vaccination_Status": 1,
    "Immune_Condition": "Normal",

    "WBC_Count": 7.5,
    "Platelet_Count": 270000,
    "Hemoglobin": 13.5,

    "Viral_Load_Score": 2,
    "Symptom_Duration_Days": 1,
    "Time_Since_First_Symptom": 1,

    "Population_Density_Score": 5,
    "Local_Outbreak_Severity": 1,
    "Healthcare_Access_Score": 8
}


# Get prediction
risk = predict_risk(model, patient)


print()
print("==============================")
print("EBOLA RISK PREDICTION")
print("==============================")
print(f"Model risk score: {risk * 100:.2f}%")