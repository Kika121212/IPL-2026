import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Cricket Stats & Viz", layout="wide")

st.title("Cricket Performance Analytics Dashboard")

# File Upload
uploaded_file = st.sidebar.file_uploader("Upload your CSV data", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Pre-processing
    # Define phases
    def get_phase(over):
        if over <= 6: return "Powerplay"
        elif over <= 15: return "Middle"
        else: return "Death"
    
    df['Phase'] = df['Over Number'].apply(get_phase)
    
    # Sidebar Menu
    menu = st.sidebar.selectbox("Select Menu", ["Batter Stats", "Bowler Stats", "Visualization"])

    if menu == "Batter Stats":
        st.header("Batter Statistics")
        
        # Calculations per batter
        batter_stats = []
        for batter, group in df.groupby('Striker'):
            balls_faced = group[group['Wides'] == 0].shape[0]
            runs = group['Batter Runs'].sum()
            fours = group[group['Batter Runs'] == 4].shape[0]
            sixes = group[group['Batter Runs'] == 6].shape[0]
            
            # Dismissals (excluding run outs for average calculation)
            outs = group[group['Dismissal Type'].notna() & (group['Dismissal Type'] != 'run out')].shape[0]
            avg = runs / outs if outs > 0 else runs
            sr = (runs / balls_faced * 100) if balls_faced > 0 else 0
            bpb = balls_faced / (fours + sixes) if (fours + sixes) > 0 else balls_faced
            
            false_shot_pct = (group['False Shot'].sum() / len(group) * 100)
            ff_pct = (group[group['Feet Movement'] == 'Front Foot'].shape[0] / len(group) * 100)
            bf_pct = (group[group['Feet Movement'] == 'Back Foot'].shape[0] / len(group) * 100)
            
            batter_stats.append({
                "Batter": batter,
                "Batter Runs": runs,
                "Average": round(avg, 2),
                "Strike Rate": round(sr, 2),
                "Balls per Boundary": round(bpb, 2),
                "Fours": fours,
                "Sixes": sixes,
                "False Shot%": round(false_shot_pct, 2),
                "Front Foot Shot%": round(ff_pct, 2),
                "Back Foot Shot%": round(bf_pct, 2)
            })
            
        st.dataframe(pd.DataFrame(batter_stats), use_container_width=True)

    elif menu == "Bowler Stats":
        st.header("Bowler Statistics")
        
        bowler_stats = []
        for bowler, group in df.groupby('Bowler'):
            # Legal balls for SR and Wickets
            balls_bowled = group[group['Wides'] == 0].shape[0]
            # Runs conceded (Exclude Byes/Leg Byes)
            runs_conceded = group['Runs'].sum() - group['Byes'].sum() - group['Leg Byes'].sum()
            wickets = group[group['Dismissal Type'].notna() & (group['Dismissal Type'] != 'run out')].shape[0]
            
            eco = (runs_conceded / balls_bowled * 6) if balls_bowled > 0 else 0
            bowl_avg = runs_conceded / wickets if wickets > 0 else runs_conceded
            bowl_sr = balls_bowled / wickets if wickets > 0 else balls_bowled
            
            dots = group[(group['Runs'] == 0) & (group['Wides'] == 0) & (group['No Balls'] == 0)].shape[0]
            dot_pct = (dots / balls_bowled * 100) if balls_bowled > 0 else 0
            
            boundaries = group[group['Batter Runs'].isin([4, 6])].shape[0]
            bpb = balls_bowled / boundaries if boundaries > 0 else balls_bowled
            false_shot_pct = (group['False Shot'].sum() / len(group) * 100)

            bowler_stats.append({
                "Bowler": bowler,
                "Wickets": wickets,
                "Economy": round(eco, 2),
                "Bowl Avg": round(bowl_avg, 2),
                "Bowl SR": round(bowl_sr, 2),
                "Balls per Wickets": round(bowl_sr, 2),
                "Dots": dots,
                "Dots%": round(dot_pct, 2),
                "Ball per Boundary": round(bpb, 2),
                "False Shot%": round(false_shot_pct, 2)
            })
            
        st.dataframe(pd.DataFrame(bowler_stats), use_container_width=True)

    elif menu == "Visualization":
        st.header("Visual Analysis")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            all_batters = ["All"] + sorted(df['Striker'].unique().tolist())
            sel_batter = st.selectbox("Select Batter", all_batters)
        with col2:
            all_bowlers = ["All"] + sorted(df['Bowler'].unique().tolist())
            sel_bowler = st.selectbox("Select Bowler", all_bowlers)
        with col3:
            all_overs = ["All"] + sorted(df['Over Number'].unique().tolist())
            sel_over = st.selectbox("Select Over", all_overs)
        with col4:
            all_phases = ["All"] + sorted(df['Phase'].unique().tolist())
            sel_phase = st.selectbox("Select Phase", all_phases)
            
        # Apply Filters
        filt_df = df.copy()
        if sel_batter != "All": filt_df = filt_df[filt_df['Striker'] == sel_batter]
        if sel_bowler != "All": filt_df = filt_df[filt_df['Bowler'] == sel_bowler]
        if sel_over != "All": filt_df = filt_df[filt_df['Over Number'] == sel_over]
        if sel_phase != "All": filt_df = filt_df[filt_df['Phase'] == sel_phase]
        
        if filt_df.empty:
            st.warning("No data found for selected filters.")
        else:
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                st.subheader("Wagon Wheel")
                # Using Shot Angle and Shot Magnitude for a polar plot scatter
                fig_wagon = px.scatter_polar(filt_df, r="Shot Magnitude", theta="Shot Angle",
                                           color="Batter Runs", size="Batter Runs",
                                           hover_data=['Wagon Position'],
                                           title="Wagon Wheel (Angle vs Magnitude)")
                st.plotly_chart(fig_wagon, use_container_width=True)
                
                st.subheader("Wagon Position Distribution")
                wagon_counts = filt_df['Wagon Position'].value_counts().reset_index()
                fig_wagon_bar = px.bar(wagon_counts, x='Wagon Position', y='count', color='Wagon Position')
                st.plotly_chart(fig_wagon_bar, use_container_width=True)

            with viz_col2:
                st.subheader("Pitching Data")
                # Line and Length Plot
                fig_pitch = px.density_heatmap(filt_df, x="Pitching Line", y="Pitching Length",
                                             title="Pitching Heatmap",
                                             category_orders={"Pitching Length": ["Yorker", "Full Toss", "Half Volley", "Length Delivery", "Back of Length", "Short Length"]})
                st.plotly_chart(fig_pitch, use_container_width=True)
                
                st.subheader("Shot Connection/False Shots")
                fig_false = px.pie(filt_df, names='False Shot', title="False Shot vs Control (1=False, 0=Control)")
                st.plotly_chart(fig_false, use_container_width=True)

else:
    st.info("Please upload the CSV file to begin.")
