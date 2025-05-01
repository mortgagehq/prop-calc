# /home/ubuntu/property_calculator_app/app.py

import streamlit as st
import pandas as pd
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="NZ Property Analyzer",
    page_icon="🏠",
    layout="wide"
)

# --- Initialize Session State ---
if 'saved_deals' not in st.session_state:
    st.session_state.saved_deals = pd.DataFrame(columns=[
        'Deal Nickname', 'Property Link', 'Property Type', 'Deal Type', 'Purchase Price',
        'Capital Invested', 'Cash On Cash Return', 'Gross Yield',
        'Net Yield', 'Mortgage Coverage', 'Notes'
    ])

# --- Helper Functions ---
def calculate_metrics(inputs):
    results = {}
    try:
        # Basic Inputs
        purchase_price = inputs.get('purchase_price', 0)
        closing_costs_dollar = inputs.get('closing_costs_dollar', 0)
        down_payment_pct = inputs.get('down_payment_pct', 0.20)
        loan_interest_rate_pct = inputs.get('loan_interest_rate_pct', 0.06)
        loan_term_years = inputs.get('loan_term_years', 30)
        rent_amount = inputs.get('rent_amount', 0)
        rent_frequency = inputs.get('rent_frequency', 'Weekly')
        other_monthly_income = inputs.get('other_monthly_income', 0)
        vacancy_pct = inputs.get('vacancy_pct', 0.05)
        insurance_yearly = inputs.get('insurance_yearly', 0)
        repairs_maint_yearly = inputs.get('repairs_maint_yearly', 0)
        property_mgmt_pct = inputs.get('property_mgmt_pct', 0.08)
        other_expenses_yearly = inputs.get('other_expenses_yearly', 0)
        capital_gains_pct = inputs.get('capital_gains_pct', 0.04)
        capital_improvement_cost = inputs.get('capital_improvement_cost', 0)
        est_end_value_after_improvement = inputs.get('est_end_value_after_improvement', purchase_price + inputs.get('capital_improvement_value_add', 0))
        borrowed_deposit = inputs.get('borrowed_deposit', False)

        # --- Calculations ---

        # Investment
        closing_costs = closing_costs_dollar
        down_payment = purchase_price * down_payment_pct
        initial_investment = down_payment + closing_costs + capital_improvement_cost
        results['Capital Invested'] = initial_investment

        # Loan
        loan_amount = purchase_price - down_payment
        if loan_term_years > 0 and loan_interest_rate_pct > 0:
            monthly_interest_rate = loan_interest_rate_pct / 12
            num_payments = loan_term_years * 12
            if monthly_interest_rate > 0:
                 monthly_mortgage_payment = loan_amount * (monthly_interest_rate * (1 + monthly_interest_rate)**num_payments) / ((1 + monthly_interest_rate)**num_payments - 1)
            else: # Handle 0% interest case
                 monthly_mortgage_payment = loan_amount / num_payments if num_payments > 0 else 0
        else:
            monthly_mortgage_payment = 0
        yearly_mortgage_payment = monthly_mortgage_payment * 12

        # Income
        if rent_frequency == 'Weekly':
            gross_yearly_rent = rent_amount * 52
        elif rent_frequency == 'Fortnightly':
            gross_yearly_rent = rent_amount * 26
        elif rent_frequency == 'Monthly':
            gross_yearly_rent = rent_amount * 12
        else: # Default to yearly if frequency unknown
            gross_yearly_rent = rent_amount

        total_yearly_income = gross_yearly_rent + (other_monthly_income * 12)
        effective_gross_income = total_yearly_income * (1 - vacancy_pct)

        # Expenses (Property Tax Removed)
        property_mgmt_cost = effective_gross_income * property_mgmt_pct
        total_operating_expenses = insurance_yearly + repairs_maint_yearly + property_mgmt_cost + other_expenses_yearly

        # Cash Flow & NOI
        net_operating_income_noi = effective_gross_income - total_operating_expenses
        pre_tax_cash_flow = net_operating_income_noi - yearly_mortgage_payment
        results['Cash Flow (Yearly)'] = pre_tax_cash_flow

        # Key Metrics
        results['Cash On Cash Return'] = pre_tax_cash_flow / initial_investment if initial_investment > 0 else 0
        results['Gross Yield'] = effective_gross_income / purchase_price if purchase_price > 0 else 0
        results['Net Yield'] = net_operating_income_noi / purchase_price if purchase_price > 0 else 0 # Also known as Cap Rate
        results['Mortgage Coverage'] = net_operating_income_noi / yearly_mortgage_payment if yearly_mortgage_payment > 0 else np.inf # Debt Service Coverage Ratio (DSCR)

        # Store other useful info
        results['Purchase Price'] = purchase_price
        results['NOI'] = net_operating_income_noi
        results['Loan Interest Rate'] = loan_interest_rate_pct # Needed for benchmarking

    except Exception as e:
        st.error(f"Calculation Error: {e}")
        return {}
    return results

# --- Benchmarking Functions ---
def get_benchmark_indicator(metric_name, value, loan_interest_rate):
    indicator = "⚪"
    try:
        if metric_name == "Cash On Cash Return":
            if value >= (loan_interest_rate + 0.015):
                indicator = "🟢"
        elif metric_name == "Gross Yield":
            if value >= (loan_interest_rate + 0.015):
                indicator = "🟢"
        elif metric_name == "Net Yield":
            if value > 0:
                indicator = "🟢"
        elif metric_name == "Mortgage Coverage":
            # Handle infinite case for no debt
            if np.isinf(value) or value > 1.2:
                indicator = "🟢"
    except:
        pass # Keep default indicator if comparison fails
    return indicator

# --- App Layout ---

# Display Logo and Title
col_title1, col_title2 = st.columns([1, 4])
with col_title1:
    try:
        st.image("/home/ubuntu/property_calculator_app/logo.png", width=150)
    except Exception as e:
        st.error(f"Could not load logo: {e}")
with col_title2:
    st.title("NZ Property Analyzer")
    st.caption("Analyze individual deals and compare saved opportunities.")

st.divider()

# --- Dashboard Section ---
st.header("📊 Deal Comparison Dashboard")

if not st.session_state.saved_deals.empty:
    st.write("Saved Deals:")
    df_display = st.session_state.saved_deals.copy()

    # Define formatting
    format_dict = {
        "Purchase Price": st.column_config.NumberColumn(format="$ {:,.0f}"),
        "Capital Invested": st.column_config.NumberColumn(format="$ {:,.0f}"),
        "Cash On Cash Return": st.column_config.NumberColumn(format="%.2f%%"),
        "Gross Yield": st.column_config.NumberColumn(format="%.2f%%"),
        "Net Yield": st.column_config.NumberColumn(format="%.2f%%"),
        "Mortgage Coverage": st.column_config.NumberColumn(format="%.2f"),
        "Property Link": st.column_config.LinkColumn("Property Link", display_text="View Listing")
    }

    display_columns = [
        'Deal Nickname', 'Property Link', 'Property Type', 'Deal Type', 'Purchase Price',
        'Capital Invested', 'Cash On Cash Return', 'Gross Yield',
        'Net Yield', 'Mortgage Coverage', 'Notes'
    ]
    existing_display_columns = [col for col in display_columns if col in df_display.columns]
    df_display = df_display[existing_display_columns]

    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config=format_dict
    )
else:
    st.info("No deals saved yet. Analyze a deal below and save it to the dashboard.")

# --- Calculator Section ---
st.header("➕ Analyze a New Deal")

inputs = {}

# Row 1: Property, Financing, Income
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Property & Purchase")
    inputs['deal_nickname'] = st.text_input("Deal Nickname", "My New Deal")
    inputs['property_link'] = st.text_input("Property Link (URL)", "")
    inputs['property_type'] = st.selectbox("Property Type", ["Single Family", "Duplex", "Multi-Family", "Townhouse", "Apartment", "Other"])
    inputs['deal_type'] = st.selectbox("Deal Type", ["Buy & Hold", "Flip", "Development"])
    inputs['purchase_price'] = st.number_input("Purchase Price ($)", min_value=0.0, value=500000.0, step=1000.0, format="%.0f")
    inputs['closing_costs_dollar'] = st.number_input("Closing Costs ($) (e.g., Legal, Due Diligence)", min_value=0.0, value=5000.0, step=100.0, format="%.0f")

with col2:
    st.subheader("Financing")
    inputs['down_payment_pct'] = st.number_input("Down Payment (% of Purchase)", min_value=0.0, max_value=100.0, value=20.0, step=1.0, format="%.1f") / 100
    inputs['borrowed_deposit'] = st.checkbox("Is the deposit borrowed?", value=False)
    inputs['loan_interest_rate_pct'] = st.number_input("Loan Interest Rate (%)", min_value=0.0, value=6.0, step=0.1, format="%.2f") / 100
    inputs['loan_term_years'] = st.number_input("Loan Term (Years)", min_value=0, value=30, step=1)

with col3:
    st.subheader("Income")
    # Removed sub-columns for better alignment
    inputs['rent_amount'] = st.number_input("Rent Amount ($)", min_value=0.0, value=600.0, step=10.0, format="%.0f")
    inputs['rent_frequency'] = st.selectbox("Rent Frequency", ['Weekly', 'Fortnightly', 'Monthly', 'Yearly']) # Added label back
    inputs['other_monthly_income'] = st.number_input("Other Monthly Income ($)", min_value=0.0, value=0.0, step=10.0, format="%.0f")
    inputs['vacancy_pct'] = st.number_input("Vacancy Rate (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.5, format="%.1f") / 100

st.divider()

# Row 2: Expenses, Capital, Results
col4, col5, col6 = st.columns(3)

with col4:
    st.subheader("Operating Expenses (Yearly)")
    inputs['insurance_yearly'] = st.number_input("Insurance ($)", min_value=0.0, value=1200.0, step=50.0, format="%.0f")
    inputs['repairs_maint_yearly'] = st.number_input("Repairs & Maintenance ($)", min_value=0.0, value=1000.0, step=50.0, format="%.0f")
    inputs['property_mgmt_pct'] = st.number_input("Property Management (% of EGI)", min_value=0.0, max_value=100.0, value=8.0, step=0.5, format="%.1f") / 100
    inputs['other_expenses_yearly'] = st.number_input("Other Expenses ($) (e.g., Rates)", min_value=0.0, value=2000.0, step=50.0, format="%.0f")

with col5:
    st.subheader("Capital & Assumptions")
    inputs['capital_gains_pct'] = st.slider("Estimated Annual Capital Gains (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.5, format="%.1f%%") / 100
    inputs['capital_improvement_cost'] = st.number_input("Capital Improvement Cost ($)", min_value=0.0, value=0.0, step=100.0, format="%.0f")
    inputs['est_end_value_after_improvement'] = st.number_input("Est. End Value after Improvement ($)", min_value=inputs.get('purchase_price', 0), value=inputs.get('purchase_price', 0), step=1000.0, format="%.0f")
    inputs['notes'] = st.text_area("Notes")

with col6:
    st.subheader("📈 Calculated Results")
    results = calculate_metrics(inputs)

    # Get values for benchmarking
    coc_return = results.get('Cash On Cash Return', 0)
    gross_yield = results.get('Gross Yield', 0)
    net_yield = results.get('Net Yield', 0)
    mort_coverage = results.get('Mortgage Coverage', 0)
    loan_rate = results.get('Loan Interest Rate', 0)

    # Get indicators
    coc_indicator = get_benchmark_indicator("Cash On Cash Return", coc_return, loan_rate)
    gy_indicator = get_benchmark_indicator("Gross Yield", gross_yield, loan_rate)
    ny_indicator = get_benchmark_indicator("Net Yield", net_yield, loan_rate)
    mc_indicator = get_benchmark_indicator("Mortgage Coverage", mort_coverage, loan_rate)

    # Display Key Metrics with Indicators
    st.metric(f"Cash On Cash Return {coc_indicator}", f"{coc_return:.2%}")
    st.metric(f"Gross Yield {gy_indicator}", f"{gross_yield:.2%}")
    st.metric(f"Net Yield (Cap Rate) {ny_indicator}", f"{net_yield:.2%}")
    st.metric(f"Mortgage Coverage (DSCR) {mc_indicator}", f"{mort_coverage:.2f}" if np.isfinite(mort_coverage) else "N/A (No Debt)")
    st.metric("Yearly Cash Flow", f"$ {results.get('Cash Flow (Yearly)', 0):,.0f}")
    st.metric("Net Operating Income (NOI)", f"$ {results.get('NOI', 0):,.0f}")

    # Save Button
    if st.button("💾 Save Deal to Dashboard"):
        new_deal_data = {
            'Deal Nickname': inputs['deal_nickname'],
            'Property Link': inputs['property_link'],
            'Property Type': inputs['property_type'],
            'Deal Type': inputs['deal_type'],
            'Purchase Price': results.get('Purchase Price', 0),
            'Capital Invested': results.get('Capital Invested', 0),
            'Cash On Cash Return': coc_return,
            'Gross Yield': gross_yield,
            'Net Yield': net_yield,
            'Mortgage Coverage': mort_coverage,
            'Notes': inputs['notes']
        }
        new_deal_df = pd.DataFrame([new_deal_data])
        st.session_state.saved_deals = pd.concat([st.session_state.saved_deals, new_deal_df], ignore_index=True)
        st.success(f"Deal '{inputs['deal_nickname']}' saved!")
        st.rerun()

# --- Footer ---
st.markdown("---")
st.markdown("Created by mortgagehq")

