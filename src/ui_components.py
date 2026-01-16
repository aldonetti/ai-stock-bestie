"""UI components and styling for the stock analysis application."""

import streamlit as st

import constants


def inject_custom_css() -> None:
    """Inject custom CSS styles for the application."""
    st.markdown(
        f"""
    <style>
        /* Color Palette */
        :root {{
            --primary: {constants.PRIMARY};
            --primary-hover: {constants.PRIMARY_HOVER};
            --primary-light: {constants.PRIMARY_LIGHT};
            --secondary: {constants.SECONDARY};
            --secondary-light: {constants.SECONDARY_LIGHT};
            --secondary-dark: {constants.SECONDARY_DARK};
            --success: {constants.SUCCESS};
            --success-light: {constants.SUCCESS_LIGHT};
            --danger: {constants.DANGER};
            --danger-light: {constants.DANGER_LIGHT};
            --warning: {constants.WARNING};
            --info: {constants.INFO};
            --background: {constants.BACKGROUND};
            --surface: {constants.SURFACE};
            --surface-elevated: {constants.SURFACE_ELEVATED};
            --text-primary: {constants.TEXT_PRIMARY};
            --text-secondary: {constants.TEXT_SECONDARY};
            --text-muted: {constants.TEXT_MUTED};
            --text-inverse: {constants.TEXT_INVERSE};
            --border: {constants.BORDER};
            --border-light: {constants.BORDER_LIGHT};
            --shadow-sm: {constants.SHADOW_SM};
            --shadow-md: {constants.SHADOW_MD};
            --shadow-lg: {constants.SHADOW_LG};
            --radius: {constants.RADIUS};
            --radius-sm: {constants.RADIUS_SM};
            --radius-lg: {constants.RADIUS_LG};
        }}

        /* Global Reset & Base Styles */
        .stApp {{
            background: var(--background);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', 'Helvetica Neue', sans-serif;
        }}

        /* Consistent Typography Throughout */
        body, html {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', 'Helvetica Neue', sans-serif;
        }}

        /* Force all text to be visible on white background */
        .stApp * {{
            color: var(--text-primary) !important;
        }}

        /* Main content area text */
        .main .block-container *,
        .main .block-container p,
        .main .block-container span,
        .main .block-container div,
        .main .block-container h1,
        .main .block-container h2,
        .main .block-container h3,
        .main .block-container h4,
        .main .block-container h5,
        .main .block-container h6 {{
            color: var(--text-primary) !important;
        }}

        /* Streamlit default text elements */
        p, span, div, label, h1, h2, h3, h4, h5, h6 {{
            color: var(--text-primary) !important;
        }}

        /* Application Header */
        .app-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: var(--text-inverse);
            padding: 3rem 0;
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 var(--radius) var(--radius);
            box-shadow: var(--shadow-md);
            text-align: center;
        }}

        .app-header > div {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}

        .app-header h1 {{
            font-size: 2.75rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.02em;
            text-align: center;
            color: var(--text-inverse) !important;
        }}

        .app-header p {{
            font-size: 1.125rem;
            margin: 0.75rem 0 0 0;
            opacity: 0.95;
            text-align: center;
            max-width: 600px;
            color: var(--text-inverse) !important;
        }}

        /* Modern Cards - Trading Platform Style with Alignment */
        .metric-card {{
            background: var(--surface);
            border: 1px solid var(--border-light);
            border-radius: var(--radius-sm);
            padding: 1.5rem;
            margin-bottom: 1.25rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif;
            min-height: 180px;
            display: flex;
            flex-direction: column;
            width: 100%;
            box-sizing: border-box;
        }}

        /* Ensure cards in columns are aligned */
        [data-testid="column"] .metric-card {{
            height: 100%;
        }}

        .metric-card:hover {{
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
            border-color: var(--primary);
            border-width: 1.5px;
        }}

        /* Responsive Design for Cards */
        @media (max-width: 768px) {{
            .metric-card {{
                padding: 1.25rem;
                min-height: 160px;
                margin-bottom: 1rem;
            }}
        }}

        @media (max-width: 480px) {{
            .metric-card {{
                padding: 1rem;
                min-height: 140px;
                margin-bottom: 0.875rem;
            }}

            /* Responsive typography for cards on mobile */
            .metric-card .metric-explanation {{
                font-size: 0.75rem !important;
            }}
        }}

        /* Responsive column layout */
        @media (max-width: 768px) {{
            [data-testid="column"] {{
                margin-bottom: 1rem;
            }}
        }}

        /* Metric explanation text styling */
        .metric-explanation {{
            color: var(--text-secondary);
            font-size: 0.8125rem;
            line-height: 1.5;
            margin-top: auto;
        }}

        .metric-card-primary {{
            border-left: 4px solid var(--primary);
        }}

        .metric-card-success {{
            border-left: 4px solid var(--success);
        }}

        .metric-card-danger {{
            border-left: 4px solid var(--danger);
        }}

        .metric-card-info {{
            border-left: 4px solid var(--info);
        }}

        /* Status Badges */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.375rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .status-active {{
            background: {constants.STATUS_ACTIVE};
            color: {constants.STATUS_ACTIVE_TEXT};
        }}

        .status-neutral {{
            background: {constants.STATUS_NEUTRAL};
            color: {constants.STATUS_NEUTRAL_TEXT};
        }}

        .status-overbought {{
            background: {constants.STATUS_OVERBOUGHT};
            color: {constants.STATUS_OVERBOUGHT_TEXT};
        }}

        .status-oversold {{
            background: {constants.STATUS_OVERSOLD};
            color: {constants.STATUS_OVERSOLD_TEXT};
        }}

        /* AI Analysis Card - Unified Text Style */
        .ai-analysis-card {{
            background: var(--surface);
            border: 2px solid var(--primary);
            border-radius: var(--radius);
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: var(--shadow-lg);
        }}

        .ai-analysis-container {{
            background: var(--surface) !important;
            border: 2px solid var(--primary) !important;
            border-radius: var(--radius) !important;
            padding: 2rem !important;
            margin: 1.5rem 0 !important;
            box-shadow: var(--shadow-lg) !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif !important;
            overflow: visible !important;
            max-width: 100% !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            position: relative !important;
            z-index: 999 !important;
            min-height: 200px !important;
        }}

        /* Ensure parent Streamlit containers don't clip content */
        .element-container:has(.ai-analysis-container),
        [data-testid="stVerticalBlock"]:has(.ai-analysis-container),
        [data-testid="stHorizontalBlock"]:has(.ai-analysis-container) {{
            overflow: visible !important;
            max-height: none !important;
        }}

        /* Unified text style for ALL elements in AI Analysis */
        .ai-analysis-container *,
        .ai-analysis-container h3,
        .ai-analysis-container p,
        .ai-analysis-container div,
        .ai-analysis-container span {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif !important;
            font-size: 1rem !important;
            line-height: 1.75 !important;
            font-weight: 400 !important;
            letter-spacing: 0 !important;
            overflow: visible !important;
            text-overflow: clip !important;
            background: transparent !important;
            visibility: visible !important;
            opacity: 1 !important;
        }}

        .ai-analysis-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-light);
        }}

        .ai-analysis-title {{
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            color: var(--primary) !important;
            margin: 0 !important;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif !important;
            line-height: 1.5 !important;
            letter-spacing: -0.01em !important;
        }}

        .ai-analysis-content {{
            font-size: 1rem !important;
            line-height: 1.75 !important;
            color: var(--text-primary) !important;
            margin: 0 !important;
            padding: 0 !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif !important;
            font-weight: 400 !important;
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            overflow: visible !important;
            text-overflow: clip !important;
            max-width: 100% !important;
            display: block !important;
            position: relative !important;
            z-index: 1000 !important;
            background: transparent !important;
            visibility: visible !important;
            opacity: 1 !important;
        }}

        .ai-analysis-timestamp {{
            background: var(--background);
            padding: 0.5rem 1rem;
            border-radius: var(--radius-sm);
            font-size: 0.875rem !important;
            color: var(--text-secondary);
            border: 1px solid var(--border);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif !important;
            font-weight: 400 !important;
            line-height: 1.5 !important;
        }}

        /* Explanation Cards */
        .explanation-card {{
            background: var(--background);
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            border-radius: var(--radius-sm);
            padding: 1rem;
            margin: 0.75rem 0;
            font-size: 0.875rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        .metric-explanation {{
            font-size: 0.8125rem;
            color: var(--text-muted);
            margin-top: 0.75rem;
            line-height: 1.5;
        }}

        /* Status Bar */
        .status-bar {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
            color: var(--text-inverse);
            padding: 1.25rem 1.5rem;
            border-radius: var(--radius-sm);
            margin-bottom: 2rem;
            box-shadow: var(--shadow-md);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif;
        }}

        .status-bar * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        /* Buttons - Trading Platform Style */
        .stButton > button {{
            background: var(--primary);
            color: var(--text-inverse);
            border: none;
            border-radius: var(--radius-sm);
            padding: 0.75rem 1.75rem;
            font-weight: 600;
            font-size: 0.9375rem;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif;
            letter-spacing: 0.01em;
        }}

        .stButton > button:hover {{
            background: var(--primary-hover);
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
        }}

        .stButton > button:active {{
            transform: translateY(0);
            box-shadow: var(--shadow-sm);
        }}

        /* Input Fields */
        .stTextInput > div > div > input {{
            background: var(--surface) !important;
            border: 2px solid var(--border) !important;
            color: var(--text-primary) !important;
            border-radius: var(--radius-sm) !important;
            padding: 0.75rem 1rem !important;
            font-size: 0.9375rem !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: var(--text-muted) !important;
            opacity: 0.7 !important;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15) !important;
            outline: none !important;
        }}

        /* Input Labels - Visible and Well Positioned */
        .stTextInput label {{
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 0.9375rem !important;
            margin-bottom: 0.5rem !important;
            display: block !important;
        }}

        /* Slider Labels */
        .stSlider label {{
            color: var(--text-primary) !important;
            font-weight: 600 !important;
            font-size: 0.9375rem !important;
            margin-bottom: 0.5rem !important;
            display: block !important;
        }}

        /* Sidebar - Enhanced Visibility */
        section[data-testid="stSidebar"] {{
            background-color: var(--surface) !important;
        }}

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] div,
        section[data-testid="stSidebar"] span {{
            color: var(--text-primary) !important;
        }}

        /* Explanation Cards */
        .explanation-card {{
            background: var(--background) !important;
            border: 1px solid var(--border) !important;
            border-left: 4px solid var(--primary) !important;
            border-radius: var(--radius-sm) !important;
            padding: 1rem 1.25rem !important;
            margin: 0.75rem 0 1rem 0 !important;
            font-size: 0.875rem !important;
            color: var(--text-primary) !important;
            line-height: 1.6 !important;
        }}

        .explanation-card strong {{
            color: var(--text-primary) !important;
            font-weight: 600 !important;
        }}

        .explanation-card span {{
            color: var(--text-secondary) !important;
        }}

        /* Section Headers - Trading Platform Style */
        h3 {{
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            font-size: 1.25rem !important;
            margin-bottom: 1.25rem !important;
            margin-top: 0.5rem !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
            letter-spacing: -0.01em;
        }}

        h2 {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        h1 {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        /* Disclaimer */
        .disclaimer {{
            background: var(--background);
            border: 1px solid var(--border);
            border-left: 4px solid {constants.WARNING};
            padding: 1rem 1.25rem;
            border-radius: var(--radius-sm);
            margin: 2rem 0;
            color: var(--text-primary);
            font-size: 0.875rem;
            line-height: 1.6;
        }}

        /* Metric Values */
        [data-testid="stMetricValue"] {{
            color: var(--text-primary) !important;
            font-weight: 700 !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--text-secondary) !important;
        }}

        /* Streamlit Markdown Text - Consistent Typography */
        .stMarkdown {{
            color: var(--text-primary) !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        .stMarkdown p {{
            color: var(--text-primary) !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6 {{
            color: var(--text-primary) !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        /* Streamlit Text Elements */
        .element-container {{
            color: var(--text-primary) !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', 'SF Pro Display', sans-serif !important;
        }}

        /* Improved Spacing and Layout */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}

        /* Better Section Spacing */
        .main .block-container > div {{
            margin-bottom: 2rem;
        }}

        /* Smooth Transitions */
        * {{
            transition: background-color 0.2s ease, border-color 0.2s ease;
        }}

        /* Prevent layout shifts from progress bar and loading messages */
        [data-testid="stProgress"] {{
            min-height: 24px !important;
            margin-bottom: 1rem !important;
        }}

        /* Reserve space for info messages to prevent layout shifts */
        .stAlert {{
            min-height: 60px !important;
            margin-bottom: 1rem !important;
        }}

        /* Ensure progress container always takes space */
        .element-container:has([data-testid="stProgress"]) {{
            min-height: 40px !important;
        }}

        /* Reserve space for loading message container */
        .element-container:has(.stAlert) {{
            min-height: 60px !important;
        }}

        /* Loading label animation with pulsing dots */
        @keyframes loading-pulse {{
            0%, 100% {{
                opacity: 1;
            }}
            50% {{
                opacity: 0.3;
            }}
        }}

        .loading-dots {{
            display: inline-block;
            width: 1.2em;
        }}

        .loading-dots::after {{
            content: '...';
            animation: loading-pulse 1.5s ease-in-out infinite;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render application header."""
    st.markdown(
        """
    <div class="app-header">
        <div style="width: 100%; padding: 0 2rem;">
            <h1 style="text-align: center; margin: 0 auto;">AI Stock Bestie</h1>
            <p style="text-align: center; margin: 0.75rem auto 0 auto; max-width: 600px;">Professional Real-Time Stock Analysis Platform</p>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_status_bar(ticker: str, interval: int, llm_freq: int, data_points: int) -> None:
    """Render modern status bar."""
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(
            f"""
        <div class="status-bar">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <div style="width: 12px; height: 12px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);"></div>
                <div>
                    <h3 style="margin: 0; color: white; font-size: 1.25rem; font-weight: 700;">Live Analysis: {ticker}</h3>
                    <p style="margin: 0.5rem 0 0 0; color: rgba(255, 255, 255, 0.9); font-size: 0.9rem;">
                        Update: {interval}s • AI Insights: Every {llm_freq} min
                    </p>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.metric("Data Points", f"{data_points:,}")
    with col3:
        if st.session_state.get("last_analysis_time") is not None:
            st.metric("Runtime", f"{st.session_state.last_analysis_time:.1f}m")


def render_welcome_screen() -> None:
    """Render welcome screen."""
    st.markdown(
        """
    <div style="display: flex; justify-content: center; align-items: center; padding: 2rem 0;">
        <div class="metric-card" style="text-align: center; padding: 2rem 1.5rem; max-width: 700px; width: 100%;">
            <h2 style="color: #111827; margin-bottom: 0.75rem; font-size: 1.75rem; font-weight: 700;">Welcome to AI Stock Bestie</h2>
            <p style="font-size: 1rem; color: #6b7280; margin-bottom: 1.5rem; max-width: 600px; margin-left: auto; margin-right: auto;">
                Professional real-time stock analysis with AI-powered insights and advanced technical indicators
            </p>
            <div style="display: block; margin: 0 auto; padding: 1rem 1.5rem; border: 2px solid #e5e7eb; border-radius: 8px; background: #f9fafb; max-width: 500px; text-align: center;">
                <p style="margin: 0; font-size: 0.9375rem; color: #111827; text-align: center;">
                    👈 Enter a ticker symbol in the sidebar and click <strong style="color: #0066ff;">Start Analysis</strong>
                </p>
            </div>
        </div>
    </div>
        """,
        unsafe_allow_html=True,
    )


def render_disclaimer() -> None:
    """Render disclaimer."""
    st.markdown(
        """
    <div class="disclaimer">
        <strong>⚠️ Disclaimer:</strong> This is an educational project for demonstration purposes only.
        The analysis and insights provided should not be considered as financial advice.
        Always consult with a qualified financial advisor before making any investment decisions.
        Past performance does not guarantee future results.
    </div>
    """,
        unsafe_allow_html=True,
    )
