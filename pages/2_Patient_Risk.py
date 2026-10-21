import streamlit as st

from src1.predict import load_model, predict_risk


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Ebola Risk Predictor",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------
@st.cache_resource
def get_model():
    return load_model()


try:
    model = get_model()
except Exception as exc:
    st.error(f"Could not load the prediction model: {exc}")
    st.stop()


# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.title("Ebola Risk Predictor")
st.caption("AI-based risk estimation | Educational research prototype")

st.info(
    "This tool is for educational research only. "
    "It is not a validated medical diagnostic system and must not "
    "be used to make medical decisions."
)

st.divider()


# --------------------------------------------------
# PATIENT INFORMATION
# --------------------------------------------------
st.header("Patient Information")

col1, col2, col3 = st.columns(3)

with col1:
    age = st.number_input(
        "Age",
        min_value=0,
        max_value=120,
        value=25,
        help="Age in years.",
    )

with col2:
    gender = st.selectbox(
        "Gender",
        ["Male", "Female", "Transgender", "Prefer not to say"],
        help=(
            "Choose the option that best describes the person. "
            "The model's training encoder must support these categories."
        ),
    )

with col3:
    weight = st.number_input(
        "Weight (kg)",
        min_value=1.0,
        max_value=200.0,
        value=60.0,
        help="Body weight in kilograms.",
    )


col1, col2, col3 = st.columns(3)

with col1:
    occupation = st.selectbox(
        "Industry / Occupation",
        [
            "Healthcare",
            "Education",
            "Agriculture",
            "Transportation and Logistics",
            "Trade and Commerce",
            "Student",
            "Public Services",
            "Other",
            "Unknown",
        ],
        help=(
            "Choose a broad industry category. "
            "The model must be trained to handle these category values."
        ),
    )

with col2:
    region = st.selectbox(
        "Outbreak Region",
        [
            "West Africa",
            "North Kivu / Ituri (DRC)",
            "Central Africa",
            "Other / Unknown",
        ],
        help=(
            "Choose the broad geographical region. "
            "These categories must match the model's training data."
        ),
    )

with col3:
    urban_rural = st.selectbox(
        "Area",
        ["Urban", "Rural"],
        help="Whether the location is classified as urban or rural.",
    )


# --------------------------------------------------
# SYMPTOMS
# --------------------------------------------------
st.header("Symptoms")
st.caption("Select the symptoms reported by the person.")

col1, col2, col3 = st.columns(3)

with col1:
    fever = st.checkbox("Fever")
    headache = st.checkbox("Headache")
    fatigue = st.checkbox("Fatigue")
    muscle_pain = st.checkbox("Muscle Pain")
    weakness = st.checkbox("Weakness")
    sore_throat = st.checkbox("Sore Throat")

with col2:
    chills = st.checkbox("Chills")
    loss_of_appetite = st.checkbox("Loss of Appetite")
    vomiting = st.checkbox("Vomiting")
    diarrhea = st.checkbox("Diarrhea")
    nausea = st.checkbox("Nausea")
    abdominal_pain = st.checkbox("Abdominal Pain")

with col3:
    bleeding = st.checkbox("Bleeding Symptoms")
    skin_rash = st.checkbox("Skin Rash")
    eye_redness = st.checkbox("Eye Redness")
    respiratory_difficulty = st.checkbox(
        "Respiratory Difficulty"
    )

    dehydration = st.slider(
        "Dehydration Level",
        min_value=0,
        max_value=10,
        value=1,
        help="Use the scale defined by your project's dataset.",
    )


# --------------------------------------------------
# VITAL SIGNS
# --------------------------------------------------
st.header("Vital Signs")

col1, col2, col3 = st.columns(3)

with col1:
    temperature = st.number_input(
        "Body Temperature (°C)",
        min_value=30.0,
        max_value=45.0,
        value=36.7,
        step=0.1,
        help="Body temperature in degrees Celsius.",
    )

with col2:
    blood_pressure = st.number_input(
        "Blood Pressure",
        min_value=50,
        max_value=250,
        value=120,
        help="Enter the measurement in the same format used in training.",
    )

with col3:
    heart_rate = st.number_input(
        "Heart Rate",
        min_value=30,
        max_value=200,
        value=72,
        help="Heart beats per minute.",
    )

oxygen = st.number_input(
    "Oxygen Saturation (%)",
    min_value=50.0,
    max_value=100.0,
    value=99.0,
    step=0.1,
    help="Enter the measured oxygen saturation percentage.",
)


# --------------------------------------------------
# EXPOSURE HISTORY
# --------------------------------------------------
st.header("Exposure History")
st.caption("Record relevant exposure history where known.")

col1, col2, col3 = st.columns(3)

with col1:
    contact = st.checkbox("Contact With Ebola Patient")
    travel = st.checkbox("Travel History")
    outbreak_region = st.checkbox("Visited Outbreak Region")

with col2:
    animal_exposure = st.checkbox("Animal Exposure")
    healthcare_worker = st.checkbox("Healthcare Worker")
    funeral_attendance = st.checkbox("Funeral Attendance")

with col3:
    household_exposure = st.checkbox("Household Exposure")

    days_exposure = st.number_input(
        "Days Since Exposure",
        min_value=0,
        max_value=100,
        value=0,
        help="Enter the number of days, if known.",
    )

other_exposure = st.checkbox("Other Exposure")

other_exposure_details = ""

if other_exposure:
    other_exposure_details = st.text_area(
        "Describe Other Exposure (optional)",
        placeholder="Enter any additional exposure details...",
        help=(
            "For contextual information only. This text is not "
            "sent to the prediction model."
        ),
    )


# --------------------------------------------------
# MEDICAL / LABORATORY INFORMATION
# --------------------------------------------------
st.header("Medical & Laboratory Information")

# ROW 1: Vaccination Status | WBC Count | Hemoglobin
medical_col1, medical_col2, medical_col3 = st.columns(3)

with medical_col1:
    vaccination = st.checkbox(
        "Vaccination Status",
        help="Check this if the recorded vaccination status is positive.",
    )

with medical_col2:
    wbc = st.number_input(
        "WBC Count",
        min_value=0.0,
        max_value=30.0,
        value=7.5,
        step=0.1,
        help=(
            "Enter the white blood cell count in "
            "the training dataset's units."
        ),
    )

with medical_col3:
    hemoglobin = st.number_input(
        "Hemoglobin",
        min_value=0.0,
        max_value=25.0,
        value=13.5,
        step=0.1,
    )


# ROW 2: Immune Condition | Platelet Count | Viral Load Score
medical_col1, medical_col2, medical_col3 = st.columns(3)

with medical_col1:
    immune_condition = st.selectbox(
        "Immune Condition",
        ["Normal", "Compromised", "Unknown"],
        help="Use the same categories as the model's training data.",
    )

with medical_col2:
    platelet = st.number_input(
        "Platelet Count",
        min_value=0,
        max_value=600000,
        value=270000,
    )

with medical_col3:
    viral_load = st.slider(
        "Viral Load Score",
        min_value=0,
        max_value=10,
        value=2,
        help="Use the scale defined in your training dataset.",
    )


# ROW 3: Symptom Duration | Time Since First Symptom
time_col1, time_col2 = st.columns(2)

with time_col1:
    symptom_duration = st.number_input(
        "Symptom Duration (days)",
        min_value=0,
        max_value=100,
        value=1,
    )

with time_col2:
    first_symptom = st.number_input(
        "Time Since First Symptom (days)",
        min_value=0,
        max_value=100,
        value=1,
    )


# --------------------------------------------------
# ENVIRONMENTAL / REGIONAL INFORMATION
# --------------------------------------------------
st.header("Environmental & Regional Factors")

# Three equally sized columns.
# The region selectbox has been removed from this section.
environment_col1, environment_col2, environment_col3 = st.columns(3)

with environment_col1:
    population_density = st.slider(
        "Population Density Score",
        min_value=0,
        max_value=10,
        value=5,
        help="Use the scoring method defined in your dataset.",
    )

with environment_col2:
    outbreak_severity = st.slider(
        "Local Outbreak Severity",
        min_value=0,
        max_value=10,
        value=5,
        help="Use the scoring method defined in your dataset.",
    )

with environment_col3:
    healthcare_access = st.slider(
        "Healthcare Access Score",
        min_value=0,
        max_value=10,
        value=8,
        help="Use the scoring method defined in your dataset.",
    )


# --------------------------------------------------
# CREATE MODEL INPUT
# Keep feature names consistent with training.
# --------------------------------------------------
patient = {
    "Age": age,
    "Gender": gender,
    "Weight_kg": weight,
    "Occupation": occupation,
    "Region": region,
    "Urban_Rural": urban_rural,

    "Fever": int(fever),
    "Body_Temperature": temperature,
    "Headache": int(headache),
    "Fatigue": int(fatigue),
    "Muscle_Pain": int(muscle_pain),
    "Weakness": int(weakness),
    "Sore_Throat": int(sore_throat),
    "Chills": int(chills),
    "Loss_of_Appetite": int(loss_of_appetite),
    "Vomiting": int(vomiting),
    "Diarrhea": int(diarrhea),
    "Nausea": int(nausea),
    "Abdominal_Pain": int(abdominal_pain),
    "Bleeding_Symptoms": int(bleeding),
    "Skin_Rash": int(skin_rash),
    "Eye_Redness": int(eye_redness),
    "Respiratory_Difficulty": int(respiratory_difficulty),
    "Dehydration_Level": dehydration,

    "Blood_Pressure": blood_pressure,
    "Heart_Rate": heart_rate,
    "Oxygen_Saturation": oxygen,

    "Contact_With_Patient": int(contact),
    "Travel_History": int(travel),
    "Visited_Outbreak_Region": int(outbreak_region),
    "Animal_Exposure": int(animal_exposure),
    "Healthcare_Worker": int(healthcare_worker),
    "Funeral_Attendance": int(funeral_attendance),
    "Household_Exposure": int(household_exposure),
    "Days_Since_Exposure": days_exposure,

    "Vaccination_Status": int(vaccination),
    "Immune_Condition": immune_condition,

    "WBC_Count": wbc,
    "Platelet_Count": platelet,
    "Hemoglobin": hemoglobin,

    "Viral_Load_Score": viral_load,
    "Symptom_Duration_Days": symptom_duration,
    "Time_Since_First_Symptom": first_symptom,

    "Population_Density_Score": population_density,
    "Local_Outbreak_Severity": outbreak_severity,
    "Healthcare_Access_Score": healthcare_access,
}


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------
st.divider()
st.header("Risk Estimation")

st.caption(
    "Enter the available information above, then run the model. "
    "The output is experimental and is not a clinical assessment."
)

if st.button(
    "Predict Risk",
    type="primary",
    use_container_width=True,
):
    try:
        risk = predict_risk(model, patient)

        st.subheader("Model Output")

        st.metric(
            label="Model Risk Score",
            value=f"{float(risk) * 100:.2f}%",
        )

        st.warning(
            "This value is an educational machine-learning output. "
            "It is not a medically validated probability or diagnosis. "
            "Do not use it to make medical decisions."
        )

        if other_exposure and other_exposure_details.strip():
            with st.expander("Other exposure details entered"):
                st.write(other_exposure_details.strip())

    except Exception as exc:
        st.error(f"Prediction failed: {exc}")

        st.caption(
            "If the error mentions unknown categories or feature names, "
            "check the model's training columns and preprocessing. "
            "The form's options must match the trained model."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()

st.caption(
    "Ebola Risk Predictor | Educational research prototype | "
    "Not for diagnosis, treatment, or clinical decision-making."
)