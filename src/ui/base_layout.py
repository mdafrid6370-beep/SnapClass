import streamlit as st



def style_background_home():

    st.markdown("""
        <style>

                .stApp {
                    background: #5865F2 !important;
                }

                .stApp div[data-testid="stColumn"]{
                    background-color:#E0E3FF !important;
                    padding:2.5rem !important;
                    border-radius: 5rem !important;
                    }
        </style>  

                """
            ,unsafe_allow_html=True)
    

def style_background_dashboard():

    st.markdown("""
        <style>

                .stApp {
                    background: #E0E3FF !important;
                }

        </style>  

                """
            ,unsafe_allow_html=True)
    

    

def style_base_layout():
# asdasd
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Climate+Crisis:YEAR@1979&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@100..900&display=swap');

                
         /* Hide Top Bar of streamlit */
                
            #MainMenu, footer, header {
                visibility: hidden;
            }
                
            .block-container {
                padding-top:1.5rem !important;    
            }

            h1 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 3.5rem !important;
                line-height:1.1 !important;
                margin-bottom:0rem !important;
            }
                

            h2 {
                font-family: 'Climate Crisis', sans-serif !important;
                font-size: 2rem !important;
                line-height:0.9 !important;
                margin-bottom:0rem !important;
                color: #2E1065 !important;
            }
                
            h3, h4, h5, h6, p, label, .stCaption, [data-testid="stCaptionContainer"], div[data-testid="stMarkdownContainer"] p, div[data-testid="stWidgetLabel"] p, div[data-testid="stWidgetLabel"] label {
                font-family: 'Outfit', sans-serif !important;    
                color: #000000 !important;
            }

            button[data-baseweb="tab"] p, button[data-baseweb="tab"] div, button[data-baseweb="tab"] span {
                color: #000000 !important;
                font-family: 'Outfit', sans-serif !important;
            }

            button[data-baseweb="tab"][aria-selected="true"] p, button[data-baseweb="tab"][aria-selected="true"] span {
                color: #EB459E !important;
            }

            /* Toast popup notification text styling */
            div[data-testid="stToast"], div[data-testid="stToast"] *, div[data-testid="stToast"] p, div[data-testid="stToast"] span, div[data-testid="stToast"] div {
                color: #E0E3FF !important;
                font-family: 'Outfit', sans-serif !important;
            }

            /* Dialog modal text styling */
            div[data-testid="stDialog"] *,
            div[role="dialog"] *,
            div[data-baseweb="modal"] * {
                color: #E0E3FF !important;
                font-family: 'Outfit', sans-serif !important;
            }

            div[data-testid="stDialog"] button *,
            div[role="dialog"] button * {
                color: white !important;
            }

            div[data-testid="stDialog"] button[kind="tertiary"] *,
            div[role="dialog"] button[kind="tertiary"] * {
                color: #E0E3FF !important;
            }
                

            button, button *, button p, button span, button div {
                border-radius: 1.5rem !important;
                background-color: #5865F2;
                color: white !important;
            }

            button {
                border-radius: 1.5rem !important;
                background-color: #5865F2 !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
            }

            button[kind="secondary"], button[kind="secondary"] *, button[kind="secondary"] p, button[kind="secondary"] span {
                background-color: #EB459E;
                color: white !important;
            }

            button[kind="secondary"] {
                border-radius: 1.5rem !important;
                background-color: #EB459E !important;
                color: white !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
            }

            button[kind="tertiary"], button[kind="tertiary"] *, button[kind="tertiary"] p, button[kind="tertiary"] span, button[kind="tertiary"] div {
                background-color: black;
                color: #E0E3FF !important;
            }

            button[kind="tertiary"] {
                border-radius: 1.5rem !important;
                background-color: black !important;
                color: #E0E3FF !important;
                padding: 10px 20px !important;
                border: none !important;
                transition: transform 0.25s ease-in-out !important;
            }

            button:hover{
                transform :scale(1.05)}
        </style>  

                """
            ,unsafe_allow_html=True)