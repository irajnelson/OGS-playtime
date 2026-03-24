import streamlit as st

from calculate_ogs_playtime import calculate_ogs_playtime


# Cache the fetching logic to be nice to OGS API
@st.cache_data(show_spinner=False, ttl=600)
def fetch_ogs_data(username: str):
    return calculate_ogs_playtime(username)

def main():
    st.set_page_config(page_title="OGS Playtime Calculator")
    st.title("OGS Playtime Calculator")
    st.markdown("Calculate how much time you've spent playing live and blitz games on [Online-Go.com](https://online-go.com).")

    username = st.text_input("Enter OGS Username (Case Sensitive)", value="")
    
    if st.button("Calculate Playtime"):
        if username:
            try:
                with st.spinner(f"Fetching game history for {username}..."):
                    df = fetch_ogs_data(username)
                
                if not df.empty:
                    total_hours = df['duration_hours'].sum()
                    st.success(f"Successfully processed {len(df)} live/blitz games")
                    st.metric(label="Total Time Played (Hours)", value=f"{total_hours:.2f}")
                    
                    st.subheader("Game Details")
                    
                    # Make links to the OGS games
                    df['game_id'] = "https://online-go.com/game/" + df['game_id'].astype(str)
                    
                    st.dataframe(
                        df, 
                        width='stretch', 
                        column_config={
                            "game_id": st.column_config.LinkColumn(
                                "Game ID", 
                                # Display only game ID number in the table
                                display_text=r"https://online-go\.com/game/([0-9]+)"
                            )
                        }
                    )
                else:
                    st.warning("No live/blitz games found for this user.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please enter a username.")

if __name__ == "__main__":
    main()
