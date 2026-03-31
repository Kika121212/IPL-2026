import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Cricket Analytics Pro", layout="wide")

st.title("Cricket Performance Analytics Dashboard")

uploaded_file = st.sidebar.file_uploader("Upload your CSV data", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Pre-processing
    def get_phase(over):
        if over <= 6: return "Powerplay"
        elif over <= 15: return "Middle"
        else: return "Death"
    
    df['Phase'] = df['Over Number'].apply(get_phase)
    
    # Sidebar Menu
    menu = st.sidebar.selectbox("Select Menu", ["Batter Stats", "Bowler Stats", "Visualization"])

    if menu == "Batter Stats":
        st.header("Batter Statistics")
        batter_stats = []
        for batter, group in df.groupby('Striker'):
            balls_faced = group[group['Wides'] == 0].shape[0]
            runs = group['Batter Runs'].sum()
            fours = group[group['Batter Runs'] == 4].shape[0]
            sixes = group[group['Batter Runs'] == 6].shape[0]
            outs = group[group['Dismissal Type'].notna() & (group['Dismissal Type'] != 'run out')].shape[0]
            avg = runs / outs if outs > 0 else runs
            sr = (runs / balls_faced * 100) if balls_faced > 0 else 0
            bpb = balls_faced / (fours + sixes) if (fours + sixes) > 0 else balls_faced
            false_shot_pct = (group['False Shot'].sum() / len(group) * 100)
            ff_pct = (group[group['Feet Movement'] == 'Front Foot'].shape[0] / len(group) * 100)
            bf_pct = (group[group['Feet Movement'] == 'Back Foot'].shape[0] / len(group) * 100)
            
            batter_stats.append({
                "Batter": batter, "Batter Runs": runs, "Average": round(avg, 2),
                "Strike Rate": round(sr, 2), "Balls per Boundary": round(bpb, 2),
                "Fours": fours, "Sixes": sixes, "False Shot%": round(false_shot_pct, 2),
                "Front Foot Shot%": round(ff_pct, 2), "Back Foot Shot%": round(bf_pct, 2)
            })
        st.dataframe(pd.DataFrame(batter_stats), use_container_width=True)

    elif menu == "Bowler Stats":
        st.header("Bowler Statistics")
        bowler_stats = []
        for bowler, group in df.groupby('Bowler'):
            balls_bowled = group[group['Wides'] == 0].shape[0]
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
                "Bowler": bowler, "Wickets": wickets, "Economy": round(eco, 2),
                "Bowl Avg": round(bowl_avg, 2), "Bowl SR": round(bowl_sr, 2),
                "Balls per Wickets": round(bowl_sr, 2), "Dots": dots, "Dots%": round(dot_pct, 2),
                "Ball per Boundary": round(bpb, 2), "False Shot%": round(false_shot_pct, 2)
            })
        st.dataframe(pd.DataFrame(bowler_stats), use_container_width=True)

    elif menu == "Visualization":
        st.header("Visual Analysis")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1: sel_batter = st.selectbox("Select Batter", ["All"] + sorted(df['Striker'].unique().tolist()))
        with col2: sel_bowler = st.selectbox("Select Bowler", ["All"] + sorted(df['Bowler'].unique().tolist()))
        with col3: sel_over = st.selectbox("Select Over", ["All"] + sorted(df['Over Number'].unique().tolist()))
        with col4: sel_phase = st.selectbox("Select Phase", ["All"] + sorted(df['Phase'].unique().tolist()))
            
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
                # Wagon Wheel with lines from center
                run_colors = {1: 'blue', 2: 'green', 3: 'yellow', 4: 'red', 6: 'black'}
                
                fig_wagon = go.Figure()
                for i, row in filt_df.iterrows():
                    r_val = row['Shot Magnitude']
                    theta_val = row['Shot Angle']
                    runs = row['Batter Runs']
                    color = run_colors.get(runs, 'grey')
                    
                    # Draw line from (0,0) to (Magnitude, Angle)
                    fig_wagon.add_trace(go.Scatterpolar(
                        r=[0, r_val],
                        theta=[0, theta_val],
                        mode='lines',
                        line=dict(color=color, width=2),
                        name=f"{runs} Runs",
                        hoverinfo='text',
                        text=f"Runs: {runs}<br>Pos: {row['Wagon Position']}",
                        showlegend=False
                    ))
                
                fig_wagon.update_layout(polar=dict(radialaxis=dict(visible=False), angularaxis=dict(direction="clockwise")))
                st.plotly_chart(fig_wagon, use_container_width=True)
                st.caption("Colors: 1=Blue, 2=Green, 3=Yellow, 4=Red, 6=Black")

            with viz_col2:
                st.subheader("Pitching Line and Length")
                
                # Sorting orders
                length_order = ['Yorker', 'Full Toss', 'Half Volley', 'Length Delivery', 'Back of Length', 'Short Length']
                line_order = ['Wide Off', 'Outside Off', 'Off stump', 'Middle stump', 'Leg stump', 'Outside Leg']
                
                # Calculate counts and wickets
                # Mapping user terms to data terms where necessary
                # Wicket logic: count non-null dismissal types
                pitch_data = []
                for length in length_order:
                    row_data = []
                    for line in line_order:
                        cell = filt_df[(filt_df['Pitching Length'] == length) & (df['Pitching Line'] == line)]
                        count = len(cell)
                        wickets = cell[cell['Dismissal Type'].notna() & (cell['Dismissal Type'] != 'run out')].shape[0]
                        
                        label = f"{count}"
                        if wickets > 0:
                            label += f" ({wickets}W)" if wickets > 1 else " (W)"
                        row_data.append(label)
                    pitch_data.append(row_data)

                fig_pitch = ff_create_annotated_heatmap(pitch_data, line_order, length_order)
                # Using standard Plotly Heatmap for better customization
                fig_pitch = go.Figure(data=go.Heatmap(
                    z=np.array([[len(filt_df[(filt_df['Pitching Length'] == l) & (filt_df['Pitching Line'] == ln)]) for ln in line_order] for l in length_order]),
                    x=line_order,
                    y=length_order,
                    colorscale='YlGnBu',
                    showscale=False
                ))
                
                # Add text annotations for Wickets
                for i, length in enumerate(length_order):
                    for j, line in enumerate(line_order):
                        cell = filt_df[(filt_df['Pitching Length'] == length) & (filt_df['Pitching Line'] == line)]
                        wickets = cell[cell['Dismissal Type'].notna() & (cell['Dismissal Type'] != 'run out')].shape[0]
                        text = ""
                        if wickets == 1: text = "W"
                        elif wickets > 1: text = f"{wickets}W"
                        
                        if text:
                            fig_pitch.add_annotation(x=line, y=length, text=text, showarrow=False, font=dict(color="red", size=14, family="Arial Black"))

                fig_pitch.update_layout(xaxis_title="Line", yaxis_title="Length")
                st.plotly_chart(fig_pitch, use_container_width=True)
                st.caption("Heatmap shows ball density. Red labels (W, 2W) indicate wickets.")

else:
    st.info("Please upload the CSV file to begin.")
