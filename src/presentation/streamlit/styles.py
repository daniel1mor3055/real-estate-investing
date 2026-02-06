"""CSS styles for Streamlit application."""

import streamlit as st


def apply_custom_styles():
    """Apply custom CSS styles to the Streamlit app."""
    st.markdown(
        """
<style>
    .metric-card {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 2px solid #e0e0e0;
    }
    .metric-card h4 {
        margin-top: 0;
        font-size: 14px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card h2 {
        margin: 10px 0;
        font-size: 32px;
        font-weight: bold;
    }
    .metric-card p {
        margin-bottom: 0;
        font-size: 12px;
        font-weight: 500;
    }
    
    /* Performance-based backgrounds */
    .metric-card.excellent {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-color: #059669;
        color: white;
    }
    .metric-card.excellent h4,
    .metric-card.excellent h2,
    .metric-card.excellent p {
        color: white;
    }
    
    .metric-card.good {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
        border-color: #10b981;
        color: white;
    }
    .metric-card.good h4,
    .metric-card.good h2,
    .metric-card.good p {
        color: white;
    }
    
    .metric-card.fair {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        border-color: #f59e0b;
        color: #78350f;
    }
    .metric-card.fair h4,
    .metric-card.fair h2,
    .metric-card.fair p {
        color: #78350f;
    }
    
    .metric-card.poor {
        background: linear-gradient(135deg, #f87171 0%, #ef4444 100%);
        border-color: #dc2626;
        color: white;
    }
    .metric-card.poor h4,
    .metric-card.poor h2,
    .metric-card.poor p {
        color: white;
    }
    
    .metric-card.unknown {
        background-color: #f0f2f6;
        border-color: #d1d5db;
        color: #374151;
    }
    .metric-card.unknown h4,
    .metric-card.unknown h2,
    .metric-card.unknown p {
        color: #374151;
    }
    
    /* Track container styles */
    .track-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: #f8f9fa;
    }
    
    .track-header {
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 10px;
        color: #1f2937;
    }
    
    /* Compliance status styles */
    .compliance-status {
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    
    .compliance-status.compliant {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 1px solid #10b981;
    }
    
    .compliance-status.non-compliant {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 1px solid #ef4444;
    }
</style>
""",
        unsafe_allow_html=True,
    )


# Rating emoji mapping
RATING_EMOJIS = {
    'excellent': '🌟',
    'good': '✓',
    'fair': '⚠️',
    'poor': '✗',
    'unknown': '?'
}
