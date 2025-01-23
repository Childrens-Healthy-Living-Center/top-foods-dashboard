import streamlit as st
import pandas as pd
import plotly.express as px

# Load the main data
data_file = './data/processed/all_foods.csv'
all_foods = pd.read_csv(data_file)

# Load sample sizes
sample_sizes_file = './data/processed/sample_sizes.csv'
sample_sizes = pd.read_csv(sample_sizes_file)

# Replace specific jurisdiction names for consistency
all_foods['jurisdiction'] = all_foods['jurisdiction'].replace({
    'Am Samoa': 'American Samoa',
    'Marshall': 'Marshall Islands'
})
sample_sizes['Jurisdiction'] = sample_sizes['Jurisdiction'].replace({
    'Am Samoa': 'American Samoa',
    'Marshall': 'Marshall Islands'
})

# Merge sample sizes into the main dataset
all_foods = all_foods.merge(sample_sizes, left_on='jurisdiction', right_on='Jurisdiction', how='left')

# Calculate the percentage of children reporting each food
all_foods['percentage'] = (all_foods['count'] / all_foods['Frequency']) * 100

# Convert all food descriptions to lowercase
all_foods['food_description'] = all_foods['food_description'].str.lower()

# Remove "All" jurisdiction
all_foods = all_foods[all_foods['jurisdiction'] != 'All']

# Set up page configuration
st.set_page_config(page_title="Top Foods Dashboard", page_icon="🍽", layout="wide")

# App title
st.title("🌟 Top Foods Dashboard")
st.markdown("Explore top foods reported by children across CHL jurisdictions and food groups at time 1.")

# Get unique jurisdictions and food groups
jurisdictions = all_foods['jurisdiction'].unique()
food_groups = all_foods['food_group'].unique()

def multiselect_with_select_all(label, options, default):
    """Custom multiselect with a 'Select All' button."""
    cols = st.columns([4, 1])
    selected = cols[0].multiselect(label, options=options, default=default, key=label)
    
    with cols[1]:
        st.write("")  # Empty space to align button vertically
        if st.button("Select All", key=f"select_all_{label}"):
            selected = options  # Select all options

    return selected



# ---------- Chart 1: Heatmap ----------
st.subheader("Food Group Distribution Across Jurisdictions")
st.markdown("This heatmap visualizes the distribution of food groups across jurisdictions, helping to identify region-specific dietary patterns.")

selected_jurisdictions_heatmap = multiselect_with_select_all(
    "Select Jurisdiction(s) for Heatmap",
    jurisdictions,
    jurisdictions
)

cols_heatmap = st.columns([4, 1])
selected_food_groups_heatmap = cols_heatmap[0].multiselect(
    "Select Food Group(s)",
    options=food_groups,
    default=food_groups,
    key="food_group_heatmap"
)
with cols_heatmap[1]:
    st.write("")
    if st.button("Select All", key="select_all_food_group_heatmap"):
        selected_food_groups_heatmap = food_groups.tolist()
        st.experimental_rerun()

filtered_data_heatmap = all_foods[
    (all_foods['jurisdiction'].isin(selected_jurisdictions_heatmap)) &
    (all_foods['food_group'].isin(selected_food_groups_heatmap))
]

if not filtered_data_heatmap.empty:
    most_prevalent_food_group = (
        filtered_data_heatmap.groupby('food_group')['percentage'].mean().idxmax()
    )
    avg_percentage_heatmap = (
        filtered_data_heatmap.groupby('food_group')['percentage'].mean().max()
    )

    st.markdown(f"**Most Prevalent Food Group:** {most_prevalent_food_group} ({avg_percentage_heatmap:.2f}%)")

    heatmap_data_percentage = (
        filtered_data_heatmap.groupby(['jurisdiction', 'food_group'], observed=False)['percentage']
        .mean()
        .reset_index()
    )
    heatmap_fig_percentage = px.density_heatmap(
        heatmap_data_percentage,
        x='jurisdiction',
        y='food_group',
        z='percentage',
        color_continuous_scale='Blues',
        title="Heatmap of Food Group Distribution by Jurisdiction",
        labels={'percentage': 'Percentage (%)'}
    )
    st.plotly_chart(heatmap_fig_percentage, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

st.markdown("---")  # Final divider

# ---------- Chart 2: Top Foods by Percentage Across Jurisdictions ----------
st.subheader("Top Foods by Percentage Across Jurisdictions")
st.markdown("This chart shows the most commonly reported foods as a percentage of children surveyed in each jurisdiction, providing insights into relative food popularity.")

selected_jurisdictions_top3 = multiselect_with_select_all(
    "Select Jurisdiction(s) for Top Foods",
    jurisdictions,
    jurisdictions
)

cols = st.columns([4, 1])
selected_food_groups_top3 = cols[0].multiselect(
    "Select Food Group(s)",
    options=food_groups,
    default=food_groups,
    key="food_group_top3"
)
with cols[1]:
    st.write("")
    if st.button("Select All", key="select_all_food_group_top3"):
        selected_food_groups_top3 = food_groups.tolist()
        st.experimental_rerun()

filtered_data_top3 = all_foods[
    (all_foods['jurisdiction'].isin(selected_jurisdictions_top3)) &
    (all_foods['food_group'].isin(selected_food_groups_top3))
]

if not filtered_data_top3.empty:
    unique_foods_top3 = filtered_data_top3['food_description'].nunique()
    most_reported_percentage_food = (
        filtered_data_top3.groupby('food_description')['percentage'].mean().idxmax()
    )
    highest_average_percentage = (
        filtered_data_top3.groupby('food_description')['percentage'].mean().max()
    )

    st.markdown(f"**Unique Foods:** {unique_foods_top3}")
    st.markdown(f"**Most Reported Food by Percentage:** {most_reported_percentage_food} ({highest_average_percentage:.2f}%)")

    max_foods_top3 = st.slider(
        "Select the number of top foods to display:",
        min_value=2,
        max_value=20,
        value=3,
        key="top3_slider"
    )

    top_foods_per_jurisdiction = (
        filtered_data_top3.groupby(['food_description'], observed=False)['percentage']
        .mean()
        .reset_index()
        .sort_values(by='percentage', ascending=False)
        .head(max_foods_top3)
    )
    
    top_foods_with_jurisdiction = filtered_data_top3[
        filtered_data_top3['food_description'].isin(top_foods_per_jurisdiction['food_description'])
    ]
    
    fig_top3 = px.bar(
        top_foods_with_jurisdiction,
        x='food_description',
        y='percentage',
        color='jurisdiction',
        barmode='group',
        title=f"Top {max_foods_top3} Foods by Percentage Across Jurisdictions",
        labels={'food_description': 'Food', 'percentage': 'Percentage (%)'},
        text=top_foods_with_jurisdiction['percentage'].round(2),  # Rounded to 2 decimal places
    )
    st.plotly_chart(fig_top3, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

st.markdown("---")  # Divider for better readability

# ---------- Chart 3: Top Foods by Percentage of Children Reporting ----------
st.subheader("Top Foods by Percentage of Children Reporting")
st.markdown("This chart focuses on foods that have the highest reporting percentages relative to children surveyed, identifying key dietary trends across jurisdictions.")

selected_jurisdictions_percentage = multiselect_with_select_all(
    "Select Jurisdiction(s) for Top Foods by Percentage",
    jurisdictions,
    jurisdictions
)

cols_percentage = st.columns([4, 1])
selected_food_groups_percentage = cols_percentage[0].multiselect(
    "Select Food Group(s)",
    options=food_groups,
    default=food_groups,
    key="food_group_percentage"
)
with cols_percentage[1]:
    st.write("")
    if st.button("Select All", key="select_all_food_group_percentage"):
        selected_food_groups_percentage = food_groups.tolist()
        st.experimental_rerun()

filtered_data_percentage = all_foods[
    (all_foods['jurisdiction'].isin(selected_jurisdictions_percentage)) &
    (all_foods['food_group'].isin(selected_food_groups_percentage))
]

if not filtered_data_percentage.empty:
    most_reported_percentage_food = (
        filtered_data_percentage.groupby('food_description')['percentage'].mean().idxmax()
    )
    highest_average_percentage = (
        filtered_data_percentage.groupby('food_description')['percentage'].mean().max()
    )

    st.markdown(f"**Most Reported Food by Percentage:** {most_reported_percentage_food} ({highest_average_percentage:.2f}%)")

    max_foods_percentage = st.slider(
        "Select the number of top foods to display:",
        min_value=2,
        max_value=20,
        value=10,
        key="percentage_slider"
    )

    top_foods_percentage = (
        filtered_data_percentage.groupby('food_description', observed=False)['percentage']
        .mean()
        .reset_index()
        .sort_values(by='percentage', ascending=False)
        .head(max_foods_percentage)
    )
    fig_percentage = px.bar(
        top_foods_percentage,
        x='food_description',
        y='percentage',
        title=f"Top {max_foods_percentage} Foods by Percentage of Children Reporting",
        labels={'food_description': 'Food', 'percentage': 'Percentage (%)'},
        color='percentage',
        color_continuous_scale='viridis'
    )
    st.plotly_chart(fig_percentage, use_container_width=True)
else:
    st.warning("No data available for the selected filters.")

st.markdown("---")  # Divider for better readability

# Citation Section
st.markdown("### Cite This App")
citation_text = """
University of Hawaii at Manoa, Children’s Healthy Living Center (2025). Top Foods Dashboard: A Streamlit Application for Food Data Analysis. Version 1.0.
"""
st.text_area("Citation:", citation_text, height=100, help="Copy this citation for referencing this app.")