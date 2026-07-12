import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

st.set_page_config(
    page_title="Dashboard",
    layout="wide"
)

st.markdown("""
<style>

/* Selectbox border */
div[data-baseweb="select"] > div {
    border: 2px solid #4CAF50 !important;
    border-radius: 10px !important;
}

/* Hover effect */
div[data-baseweb="select"]:hover > div {
    border: 2px solid #00FFAA !important;
    box-shadow: 0 0 10px #00FFAA !important;
}

/* Arrow */
div[data-baseweb="select"] svg {
    color: white !important;
    transform: scale(1.3);
}

</style>
""", unsafe_allow_html=True)

st.title("Blast Furnace Digital Twin & Forecast Dashboard")


sheet_id = "1DkPGV9pDQzs91eLD2B6yOCI3iSs0S_AA1SxNohYiYao"

url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"

file = url

try:
    excel_file = pd.ExcelFile(file)
except:
    st.error("Unable to connect to Google Sheets.")
    st.stop()

sheets = excel_file.sheet_names

records = []

for sheet in sheets:

    df = pd.read_excel(
    excel_file,
    sheet_name=sheet,
    header=None
    )

    month_data = {
        "Month": sheet
    }

    for i in range(len(df)):

        row_name = " ".join(
            [str(x) for x in df.iloc[i].tolist()]
        )

        row = pd.to_numeric(
            df.iloc[i],
            errors="coerce"
        )

        row = row.dropna()

        if len(row) == 0:
            continue

        value = row.iloc[-1]

        if "Hot Metal to SMS" in row_name:
            month_data["Hot Metal"] = value

        elif "Theoretical Production" in row_name:
            month_data["Theoretical"] = value

        elif "Declared Production" in row_name:
            month_data["Declared"] = value

        elif "Fe Balance" in row_name:
            month_data["Fe Balance"] = value

        elif "Total Slag Generation" in row_name:
            month_data["Slag"] = value

    records.append(month_data)

monthly_df = pd.DataFrame(records)

monthly_df = monthly_df.dropna(
    subset=["Hot Metal"]
).reset_index(drop=True)

daily_kpis = [
    "Hot Metal",
    "Fe Balance"
]

monthly_kpis = [
    "Theoretical",
    "Declared",
    "Slag"
]


# ==================================
# CLEAN DATA
# ==================================

monthly_df = monthly_df.replace(
    [None, "None", "nan"],
    np.nan
)

for col in monthly_df.columns[1:]:

    monthly_df[col] = pd.to_numeric(
        monthly_df[col],
        errors="coerce"
    )

#-------------------------------------------------------------------------------------------------------
st.markdown("---")
st.header("Digital Twin Simulation")
st.write("Adjust important blast furnace operating parameters and observe the estimated process outputs.")


st.sidebar.header("Blast Furnace Inputs")

coke = st.sidebar.slider(
    "Coke Rate (kg/thm)",
    250.0,500.0,380.0)

pci = st.sidebar.slider("PCI Rate (kg/thm)",
    50.0,250.0,170.0)

blast_temp = st.sidebar.slider(
    "Hot Blast Temperature (°C)",
    900,
    1300,
    1150)

oxygen = st.sidebar.slider(
    "Oxygen Enrichment (%)",
    3.0,
    15.0,
    9.0
    )



blast_volume = st.sidebar.slider(
    "Blast Volume (Nm³/min)",
    5000,
    6000,
    5501
    )

humidity = st.sidebar.slider(
    "Blast Humidity (g/Nm³)",
    20,
    50,
    35
    )

sp_ratio = st.sidebar.slider(
    "Sinter / Pellet Ratio",
    0.60,
    1.50,
    0.89,
    0.01
)

total_burden = 1590.0      # 750 + 840

pellets = total_burden / (1 + sp_ratio)
sinter = total_burden - pellets

nut_coke = st.sidebar.slider(
    "Nut Coke Rate (kg/thm)",
    40.0,
    60.0,
    54.0
)

fuel_rate = coke + pci + nut_coke


fe_input = (
    sinter*0.58 +
    pellets*0.66
)

fe_hotmetal = fe_input*0.94

fe_slag = fe_input*0.02

fe_loss = fe_input-fe_hotmetal-fe_slag

fe_recovery = (
    fe_hotmetal/fe_input
)*100

heat_from_fuel = fuel_rate * 2450

blast_heat = 0.345*blast_temp*blast_volume

moisture_heat = (
    0.411*
    blast_temp*
    blast_volume*
    humidity*
    (22.4/18)
)

total_heat = (
    heat_from_fuel +
    blast_heat +
    moisture_heat
)

st.subheader("Simulation Results")

a,b,c = st.columns(3)

a.metric(
    "Fuel Rate",
    f"{fuel_rate:.1f} kg/thm"
)


b.metric(
    "Fe Input",
    f"{fe_input:.1f} kg/thm"
)

c.metric(
    "Fe Recovery",
    f"{fe_recovery:.2f}%"
)


c1,c2,c3 = st.columns(3)


c1.metric(
    "Fe in Hot Metal",
    f"{fe_hotmetal:.1f}"
)

c2.metric(
    "Fe Loss",
    f"{fe_loss:.1f}"
)

c3.metric(
    "Total Heat",
    f"{total_heat/1e6:.2f} M kcal/thm"
)

fig = go.Figure()

fig.add_bar(
    name="Values",
    x=[
    "Fe Input",
    "Fe in HM",
    "Fe in Slag",
    "Fe Loss"
    ],

    y=[
    fe_input,
    fe_hotmetal,
    fe_slag,
    fe_loss
    ]
)

fig.update_layout(
    title="Digital Twin Output",
    xaxis_title="Parameter",
    yaxis_title="kg/thm",
    height=450
)

st.plotly_chart(
    fig,
    use_container_width=True
)


st.subheader("Operator Remarks")

issues = []

if blast_temp < 1050:
    issues.append("Low Blast Temperature")

elif blast_temp > 1200:
    issues.append("High Blast Temperature")

if fuel_rate > 600:
    issues.append("High Fuel Rate")

elif fuel_rate < 450:
    issues.append("Low Fuel Rate")

if fe_recovery < 93:
    issues.append("Low Iron Recovery")

if oxygen < 4:
    issues.append("Increase Oxygen Enrichment")

elif oxygen > 10:
    issues.append("Reduce Oxygen Enrichment")

if humidity > 40:
    st.info("High Blast Humidity")

if total_heat < 14000000:
    issues.append("Low Heat Availability")

if sp_ratio < 0.75:
    st.info("Higher Pellet Burden")

elif sp_ratio > 1.20:
    st.info("Higher Sinter Burden")

if len(issues)==0:
    st.success("Blast Furnace Operating Normally")

else:
    for item in issues:
        st.warning(item)

#------------------------------------------------------------------------------------------------------
st.markdown("---")



st.markdown("""
### Forecast Interpretation

- Historical data: Oct-25 to Mar-26
- Validation month: Mar-26
- Forecast months: Apr-26 to Sep-26
- Random Forest is used for comparison.
- Polynomial Regression is used for future forecasting because it captures trend continuation.
- Random Forest achieved the lowest training MAE but produced constant forecasts due to limited historical data and inability to extrapolate beyond the training range. Therefore Polynomial Regression was selected for future forecasting.
- Due to limited historical data (6 months), forecast accuracy should improve when more monthly observations become available.
""")

st.subheader("Historical Data")

st.dataframe(monthly_df)


kpis = [
    "Hot Metal",
    "Theoretical",
    "Declared",
    "Fe Balance",
    "Slag"
]


st.markdown("""
<style>

div[data-baseweb="select"] {
    cursor: pointer !important;
    transition: all 0.2s ease;
}

div[data-baseweb="select"]:hover {
    transform: scale(1.01);
}

div[data-baseweb="select"] * {
    cursor: pointer !important;
}

</style>
""", unsafe_allow_html=True)


st.subheader("▼ Select KPI")
selected = st.selectbox(
    "",
    kpis,
    label_visibility="collapsed"

)


actual_df = monthly_df[
    ["Month", selected]
].dropna()

actual = actual_df[selected]

actual = actual.astype(float)

X = np.arange(len(actual)).reshape(-1,1)


models = {
    "Linear Regression":
        LinearRegression(),

    "Polynomial Regression":
        Pipeline([
            ("poly", PolynomialFeatures(degree=2)),
            ("linear", LinearRegression())
        ]),

    "Random Forest":
        RandomForestRegressor(
            n_estimators=100,
            random_state=42
        )
}

results = []

for name, model in models.items():

    model.fit(X, actual)

    train_pred = model.predict(X)

    mae = mean_absolute_error(
        actual,
        train_pred
    )

    r2 = r2_score(
    actual,
    train_pred
    )

    results.append({
    "Model": name,
    "MAE": round(mae,2),
    "R²": round(r2,4)
    })

result_df = pd.DataFrame(results)

st.subheader("Model Comparison")

st.dataframe(result_df)

best_model_name = result_df.sort_values(
    "MAE"
).iloc[0]["Model"]

# Use Polynomial for forecasting
forecast_model = models["Polynomial Regression"]


forecast_model.fit(X, actual)

st.success(
    f"Best Fit on Historical Data = {best_model_name}"
)

st.info(
    "Polynomial Regression used for future forecasting because Random Forest cannot extrapolate."
)

forecast_model.fit(X,actual)


# =====================================
# VALIDATION
# Train Oct-Feb
# Predict Mar-26
# =====================================

train_df = monthly_df.iloc[:5]
test_df = monthly_df.iloc[5:6]

X_train = np.arange(len(train_df)).reshape(-1,1)

y_train = train_df[selected].astype(float)

validation_model = forecast_model

validation_model.fit(
    X_train,
    y_train
)

pred_mar = validation_model.predict(
    [[len(train_df)]]
)[0]

actual_mar = float(
    test_df[selected].values[0]
)

error = abs(
    actual_mar - pred_mar
)

validation_df = pd.DataFrame({
    "Month": ["Mar-26"],
    "Actual": [round(actual_mar,2)],
    "Predicted": [round(pred_mar,2)],
    "Error": [round(error,2)]
})

st.subheader("Model Validation")

st.dataframe(validation_df)

validation_fig = go.Figure()

validation_fig.add_trace(
    go.Bar(
        x=["Actual Mar-26"],
        y=[actual_mar],
        name="Actual"
    )
)

validation_fig.add_trace(
    go.Bar(
        x=["Predicted Mar-26"],
        y=[pred_mar],
        name="Predicted"
    )
)

st.plotly_chart(
    validation_fig,
    use_container_width=True
)

train_pred = forecast_model.predict(X)

comparison_fig = go.Figure()

comparison_fig.add_trace(
    go.Scatter(
        x=actual_df["Month"],
        y=actual,
        mode="lines+markers",
        name="Actual Values"
    )
)

comparison_fig.add_trace(
    go.Scatter(
        x=actual_df["Month"],
        y=train_pred,
        mode="lines+markers",
        name="Predicted Values"
    )
)

# Dynamic heading
st.markdown(
    f"<h2 style='text-align:center; color:#1f4e79;'>Actual vs Forecast - {selected}</h2>",
    unsafe_allow_html=True
)

comparison_fig.update_layout(
    title="Actual vs Predicted Values",
    xaxis_title="Month",
    yaxis_title=selected
)

st.plotly_chart(
    comparison_fig,
    use_container_width=True
)


def get_daily_values(sheet_name, keyword):

    df = pd.read_excel(
    excel_file,
    sheet_name=sheet_name,
    header=None
)

    for i in range(len(df)):

        row_name = " ".join(
            [str(x) for x in df.iloc[i]]
        )

        if keyword in row_name:

            row = pd.to_numeric(
                df.iloc[i][3:34],
                errors="coerce"
            )

            return row.values

    return None

kpi_mapping = {
    "Hot Metal":"Hot Metal to SMS",
    "Theoretical":"Theoretical Production",
    "Declared":"Declared Production",
    "Slag":"Total Slag Generation",
    "Fe Balance":"Fe Balance"
}

latest_month = monthly_df["Month"].iloc[-1]

daily_values = get_daily_values(
    latest_month,
    kpi_mapping[selected]
)


if daily_values is not None:

    days = list(range(1, len(daily_values)+1))

    actual_daily = np.array(daily_values, dtype=float)

    actual_daily = np.array(daily_values, dtype=float)

    predicted_daily = []

    window = 3

    for i in range(len(actual_daily)):

        start = max(0, i-window)

        pred = np.mean(
            actual_daily[start:i+1]
        )

        predicted_daily.append(pred)

    daily_fig = go.Figure()

    daily_fig.add_trace(
        go.Scatter(
            x=days,
            y=actual_daily,
            mode="lines+markers",
            name="Actual"
        )
    )

    daily_fig.add_trace(
        go.Scatter(
            x=days,
            y=predicted_daily,
            mode="lines+markers",
            name="Predicted"
        )
    )

    daily_fig.update_layout(
        title=f"{latest_month} Daily {selected} Validation",
        xaxis_title="Day",
        yaxis_title=selected
    )

    st.plotly_chart(
        daily_fig,
        use_container_width=True
    )



actual_df = monthly_df[
    ["Month", selected]
].dropna()

actual = actual_df[selected].astype(float)

X = np.arange(len(actual)).reshape(-1,1)

forecast_model.fit(X, actual)


monthly_accuracy = (
    100 - (error / actual_mar * 100)
)


st.metric(
    "Prediction Accuracy",
    f"{monthly_accuracy:.2f}%"
)

if monthly_accuracy > 95:
    st.success("Excellent Prediction")

elif monthly_accuracy > 90:
    st.success("Very Good Prediction")

elif monthly_accuracy > 80:
    st.warning("Acceptable Prediction")

else:
    st.error("Prediction Needs Improvement")


st.metric(
    "Validation Error (t/day)",
    f"{error:.2f}"
)



st.success(
    f"Best Training Model = {best_model_name}"
)

st.info(
    "Forecast Model = Polynomial Regression"
)



last_month = monthly_df["Month"].iloc[-1]

# remove "Copy of "
last_month = last_month.replace("Copy of ", "")

# remove apostrophe if present
last_month = last_month.replace("'", "")

last_date = datetime.strptime(last_month, "%b-%y")

future_months = []

for i in range(1, 7):

    next_month = last_date + relativedelta(months=i)

    future_months.append(
        next_month.strftime("%b-%y")
    )

future_values = []

for i in range(1,7):

    pred = forecast_model.predict(
        [[len(actual)+i-1]]
    )[0]

    future_values.append(pred)

forecast_display = pd.DataFrame({
    "Month": future_months,
    "Prediction": np.round(future_values,2)
})

st.subheader(f"{selected} Forecast")

st.dataframe(forecast_display)


std_dev = np.std(actual)

upper = [
    x + std_dev
    for x in future_values
]

lower = [
    x - std_dev
    for x in future_values
]


fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=actual_df["Month"],
        y=actual,
        mode="lines+markers",
        name="Actual"
    )
)

fig.add_trace(
    go.Scatter(
        x=future_months,
        y=future_values,
        mode="lines+markers",
        name="Forecast"
    )
)

fig.add_trace(
    go.Scatter(
        x=future_months,
        y=upper,
        mode="lines",
        name="Upper Limit"
    )
)

fig.add_trace(
    go.Scatter(
        x=future_months,
        y=lower,
        mode="lines",
        name="Lower Limit"
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)
