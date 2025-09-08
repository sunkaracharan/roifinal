from django import forms

class QuickEstimateForm(forms.Form):
    annual_revenue = forms.IntegerField(
        label="Annual Revenue",
        min_value=1_000_000,
        max_value=1_000_000_000,
        initial=100_000_000,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    annual_cloud_spend = forms.IntegerField(
        label="Annual Cloud Spend",
        min_value=100_000,
        max_value=100_000_000,
        initial=10_000_000,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    num_engineers = forms.IntegerField(
        label="Number of Engineers",
        min_value=1,
        max_value=1000,
        initial=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

def range_widget(min_, max_, step, cls="form-range"):
    return forms.NumberInput(attrs={
        "type": "range", "min": min_, "max": max_, "step": step,
        "class": cls, "oninput": "updateRangeValue(this)"
    })

class FullCalculatorForm(forms.Form):
    # Business & Tech
    annual_revenue = forms.IntegerField(
        label="Annual Revenue",
        initial=100_000_000, min_value=1_000_000, max_value=1_000_000_000,
        widget=range_widget(1_000_000, 1_000_000_000, 1_000_000)
    )
    gross_margin = forms.IntegerField(
        label="Gross Margin (%)",
        initial=80, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )
    container_app_fraction = forms.IntegerField(
        label="Container App Fraction (%)",
        initial=90, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )
    annual_cloud_spend = forms.IntegerField(
        label="Annual Cloud Spend",
        initial=10_000_000, min_value=100_000, max_value=100_000_000,
        widget=range_widget(100_000, 100_000_000, 100_000)
    )
    compute_spend_fraction = forms.IntegerField(
        label="Compute Spend Fraction (%)",
        initial=60, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )
    cost_sensitive_fraction = forms.IntegerField(
        label="Cost Sensitive Fraction (%)",
        initial=50, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )

    # Productivity
    num_engineers = forms.IntegerField(
        label="Number of Engineers",
        initial=100, min_value=1, max_value=1000,
        widget=range_widget(1, 1000, 1)
    )
    engineer_cost_per_year = forms.IntegerField(
        label="Engineer Cost Per Year",
        initial=150_000, min_value=50_000, max_value=500_000,
        widget=range_widget(50_000, 500_000, 5_000)
    )
    ops_time_fraction = forms.IntegerField(
        label="Ops Time Fraction (%)",
        initial=15, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )
    ops_toil_fraction = forms.IntegerField(
        label="Ops Toil Fraction (%)",
        initial=50, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )

    # Performance
    avg_response_time_sec = forms.FloatField(
        label="Average Response Time (seconds)",
        initial=2.0, min_value=0.1, max_value=10.0,
        widget=range_widget(0.1, 10, 0.1)
    )
    revenue_lift_per_100ms = forms.FloatField(
        label="Revenue Lift per 100ms (%)",
        initial=1.0, min_value=0.0, max_value=10.0,
        widget=range_widget(0, 10, 0.1)
    )

    # Additional Performance fields (currently hardcoded in JS)
    toil_reduction_fraction = forms.IntegerField(
        label="Toil Reduction Fraction (%)",
        initial=45, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )
    exec_time_influence_fraction = forms.IntegerField(
        label="Execution Time Influence Fraction (%)",
        initial=33, min_value=0, max_value=100,
        widget=range_widget(0, 100, 1)
    )
    lat_red_container = forms.FloatField(
        label="Latency Reduction Container (%)",
        initial=28.0, min_value=0.0, max_value=100.0,
        widget=range_widget(0, 100, 0.1)
    )
    lat_red_serverless = forms.FloatField(
        label="Latency Reduction Serverless (%)",
        initial=50.0, min_value=0.0, max_value=100.0,
        widget=range_widget(0, 100, 0.1)
    )

    # Availability
    current_fci_fraction = forms.FloatField(
        label="Current FCI Fraction (%)",
        initial=2.0, min_value=0.0, max_value=10.0,
        widget=range_widget(0, 10, 0.1)
    )
    cost_per_1pct_fci = forms.FloatField(
        label="Cost per 1% FCI (%) of revenue",
        initial=1.0, min_value=0.0, max_value=10.0,
        widget=range_widget(0, 10, 0.1)
    )
    fci_reduction_fraction = forms.FloatField(
        label="FCI Reduction Fraction (%)",
        initial=75.0, min_value=0.0, max_value=100.0,
        widget=range_widget(0, 100, 0.1)
    )

