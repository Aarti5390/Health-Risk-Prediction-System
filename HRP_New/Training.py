# Import necessary libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# ----- Step 1: Load Dataset -----
df = pd.read_csv('Health_Risk_Prediction_2000_Rows.csv')

# ----- Step 2: Preprocessing -----

# Categorical columns to encode
categorical_columns = [
    'Gender',
    'Family_History_CVD',
    'Family_History_Diabetes',
    'Family_History_Obesity',
    'Family_History_Respiratory',
    'Family_History_Mental',
    'Smoking',
    'Alcohol_Consumption',
    'Diet_Type',
    'Air_Pollution_Exposure',
    'Noise_Exposure',
    'Stress_Level'
]

# Encode categorical columns
le = LabelEncoder()
for col in categorical_columns:
    df[col] = le.fit_transform(df[col])

# Define target columns
target_columns = [
    'CVD_Risk_Percentage',
    'Diabetes_Risk_Percentage',
    'Obesity_Risk_Percentage',
    'Respiratory_Risk_Percentage',
    'Mental_Health_Risk_Percentage'
]

# Feature columns
feature_columns = [col for col in df.columns if col not in target_columns]

# Prepare X and y
X = df[feature_columns]
y = df[target_columns]

# ----- Step 3: Train/Test Split -----
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ----- Step 4: Initialize Model -----
rf_model = RandomForestRegressor(n_estimators=200, random_state=42)
multi_output_rf = MultiOutputRegressor(rf_model)

# ----- Step 5: Train Model -----
multi_output_rf.fit(X_train, y_train)

# ----- Step 6: Evaluate Model -----
y_pred = multi_output_rf.predict(X_test)
overall_r2 = multi_output_rf.score(X_test, y_test)
print(f"\n✅ Overall R² Score on Test Data: {overall_r2:.4f}\n")

for i, col in enumerate(target_columns):
    mae_col = mean_absolute_error(y_test[col], y_pred[:, i])
    print(f"MAE for {col}: {mae_col:.2f}")

# ----- Step 7: Save Trained Model -----
joblib.dump(multi_output_rf, 'health_risk_model.pkl')  # ✅ Save as required
print("\n✅ Model saved as 'health_risk_model.pkl'!\n")
