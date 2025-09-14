import streamlit as st
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import io

# Import your existing agent
try:
    from agent import ask_agent
    AGENT_AVAILABLE = True
except ImportError as e:
    st.error(f"Could not import agent.py: {e}")
    AGENT_AVAILABLE = False

# Lead Generation Bot Configuration
BOT_CONFIG = {
    "engagement_thresholds": {
        "lead_capture_score": 80,  # Score threshold to trigger lead capture
        "high_intent_score": 50,   # Score for showing interest nudges
        "scroll_threshold": 40,    # Percentage scrolled
        "time_threshold": 45,      # Seconds on page
        "question_threshold": 4,   # Number of questions asked
        "page_variety_threshold": 3 # Different pages visited
    },
    "lead_fields": [
        {"name": "full_name", "label": "Full Name", "required": True, "type": "text"},
        {"name": "work_email", "label": "Work Email", "required": True, "type": "email"},
        {"name": "company", "label": "Company", "required": True, "type": "text"},
        {"name": "job_title", "label": "Job Title", "required": False, "type": "text"},
        {"name": "company_size", "label": "Company Size", "required": False, "type": "select",
         "options": ["1-10", "11-50", "51-200", "201-1000", "1000+"]},
        {"name": "phone", "label": "Phone Number", "required": False, "type": "text"},
        {"name": "use_case", "label": "Primary Use Case", "required": False, "type": "textarea"}
    ],
    "nudge_messages": {
        "/pricing": "I see you're interested in pricing! Want a personalized quote for your specific needs?",
        "/security": "Security is crucial! Would you like to discuss how we meet your compliance requirements?",
        "/integrations": "Looking at integrations? Let me help you find the perfect fit for your tech stack!",
        "/api-docs": "Exploring our API? Want to try it with a free developer account?",
        "default": "You seem interested! Ready to learn how this could work for your specific use case?"
    },
    "page_contexts": {
        "/home": "Homepage - General Information",
        "/pricing": "Pricing Information", 
        "/security": "Security & Compliance",
        "/integrations": "Integrations & API",
        "/api-docs": "API Documentation",
        "/features": "Product Features",
        "/support": "Support & Help"
    },
    "page_values": {
        "/pricing": 25,
        "/security": 20, 
        "/integrations": 15,
        "/api-docs": 15,
        "/features": 10,
        "/home": 5,
        "/support": 5
    },
    "page_content": {
        "/home": {
            "title": "🏠 Welcome to FlipKraft",
            "content": """
**Transform Your Business with Smart Automation**

FlipKraft is your all-in-one platform for business automation and API integration. 
Whether you're a startup or enterprise, we help streamline your workflows and boost productivity.

🚀 **Key Benefits:**
• Reduce manual work by 80%
• Scale operations seamlessly  
• Enterprise-grade security
• 500+ pre-built integrations
• 24/7 expert support

*Ready to see FlipKraft in action? Explore our features or check out our pricing plans!*
"""
        },
        "/pricing": {
            "title": "💰 Flexible Pricing Plans",
            "content": """
**Choose the perfect plan for your business needs**

🚀 **Basic Plan - $99/month**
• Up to 1M API calls
• Standard integrations
• Email support
• 14-day free trial

⭐ **Pro Plan - $199/month**
• Up to 5M API calls
• Advanced integrations
• Priority support
• Custom workflows

🏢 **Enterprise - Custom Pricing**
• Unlimited API calls
• White-label solutions
• Dedicated account manager
• SLA guarantees

*All plans include free setup and migration assistance!*
"""
        },
        "/security": {
            "title": "🔒 Enterprise-Grade Security",
            "content": """
**Your data security is our top priority**

🛡️ **Compliance & Certifications:**
• SOC 2 Type II certified
• GDPR compliant
• ISO 27001 certified
• HIPAA ready

🔐 **Security Features:**
• End-to-end encryption
• Multi-factor authentication
• Role-based access control
• Audit logs and monitoring
• Data residency options

*Need a security assessment? Our compliance team is ready to help!*
"""
        },
        "/integrations": {
            "title": "🔗 Powerful Integrations",
            "content": """
**Connect with 500+ apps and services**

⚡ **Popular Integrations:**
• Salesforce, HubSpot, Pipedrive
• Slack, Microsoft Teams, Discord
• AWS, Google Cloud, Azure
• Stripe, PayPal, QuickBooks
• Zapier, Make, n8n

🛠️ **Integration Features:**
• No-code integration builder
• Real-time data sync
• Custom API endpoints
• Webhook support
• Bulk data operations

*Can't find your app? We build custom integrations in 48 hours!*
"""
        },
        "/api-docs": {
            "title": "📚 Developer Resources",
            "content": """
**Comprehensive API documentation and tools**

🔧 **Developer Tools:**
• Interactive API explorer
• Code samples in 8 languages
• Postman collections
• SDKs and libraries
• Sandbox environment

📖 **Documentation:**
• Getting started guides
• API reference
• Webhooks documentation
• Rate limiting guide
• Best practices

*Need help? Join our developer community with 10,000+ active members!*
"""
        },
        "/features": {
            "title": "⚙️ Platform Features",
            "content": """
**Everything you need to automate your business**

🎯 **Core Features:**
• Visual workflow builder
• Real-time data processing
• Advanced analytics dashboard
• Custom field mapping
• Conditional logic

📊 **Analytics & Monitoring:**
• Performance metrics
• Error tracking
• Usage analytics
• Custom reports
• Alerts and notifications

*Discover how our features can transform your operations!*
"""
        },
        "/support": {
            "title": "📞 FlipKraft Customer Support",
            "content": """
**We're here to help you succeed**

**Contact Information:**
📧 Email: support@flipkraft.com
📱 Phone: +91-8000-123-456
⏰ Support Hours: Mon–Sat, 10 AM – 8 PM IST

**Self-Service Resources:**
🔍 Knowledge Base: https://flipkraft.com/help
💬 Live Chat: Available on the website
🎥 Video Tutorials: Step-by-step guides
📝 Community Forum: Connect with other users

*Average response time: < 30 minutes during business hours*
"""
        }
    }
}

class LeadCapture:
    """Handles lead capture and persistent Excel storage"""
    
    def __init__(self):
        self.leads_file = "leads.xlsx"
        # Always refresh from file - don't cache in session state
        
    def load_leads_from_file(self) -> list:
        """Load existing leads from Excel file - always fresh"""
        try:
            if os.path.exists(self.leads_file):
                df = pd.read_excel(self.leads_file)
                return df.to_dict('records')
            else:
                return []
        except Exception as e:
            st.error(f"Error loading leads file: {e}")
            return []
    
    def get_fresh_lead_count(self) -> int:
        """Get current lead count directly from file"""
        try:
            if os.path.exists(self.leads_file):
                df = pd.read_excel(self.leads_file)
                return len(df)
            return 0
        except Exception as e:
            st.error(f"Error reading lead count: {e}")
            return 0
    
    def save_lead(self, lead_data: dict, session_data: dict) -> bool:
        """Save lead to both session state and Excel file"""
        try:
            lead_record = {
                'capture_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'session_id': session_data.get('session_id'),
                'qualification_score': session_data.get('engagement_score', 0),
                'lead_quality': session_data.get('lead_qualification', 'unknown'),
                'pages_visited': ', '.join(session_data.get('pages_visited', [])),
                'questions_asked': session_data.get('questions_asked', 0),
                'time_to_capture': (datetime.now() - session_data.get('start_time', datetime.now())).seconds,
                'scroll_percentage': session_data.get('scroll_percentage', 0),
                **lead_data
            }
            
            # Save to Excel file
            self._save_to_excel_file(lead_record)
            
            st.success(f"Lead saved to {self.leads_file}")
            return True
            
        except Exception as e:
            st.error(f"Error saving lead: {e}")
            return False
    
    def _save_to_excel_file(self, new_lead: dict):
        """Append lead to Excel file on disk"""
        try:
            # Load existing data or create new DataFrame
            if os.path.exists(self.leads_file):
                existing_df = pd.read_excel(self.leads_file)
                new_df = pd.concat([existing_df, pd.DataFrame([new_lead])], ignore_index=True)
            else:
                new_df = pd.DataFrame([new_lead])
            
            # Reorder columns for better readability
            col_order = ['capture_timestamp', 'full_name', 'work_email', 'company', 'job_title', 
                        'company_size', 'phone', 'qualification_score', 'lead_quality', 
                        'pages_visited', 'questions_asked', 'time_to_capture', 'scroll_percentage', 
                        'use_case', 'session_id']
            
            existing_cols = [col for col in col_order if col in new_df.columns]
            new_df = new_df[existing_cols]
            
            # Save to Excel
            with pd.ExcelWriter(self.leads_file, engine='openpyxl', mode='w') as writer:
                new_df.to_excel(writer, index=False)
                
                # Add summary sheet
                summary_data = self._generate_summary_data(new_df)
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
        except Exception as e:
            st.error(f"Error writing to Excel file: {e}")
    
    def _generate_summary_data(self, df: pd.DataFrame) -> dict:
        """Generate summary statistics"""
        total_leads = len(df)
        hot_leads = len(df[df['lead_quality'].isin(['hot', 'very_hot'])]) if total_leads > 0 else 0
        avg_score = round(df['qualification_score'].mean(), 1) if total_leads > 0 else 0
        
        return {
            'Metric': ['Total Leads', 'High Quality Leads', 'Average Score', 'Most Recent'],
            'Value': [
                total_leads,
                f"{hot_leads} ({round(hot_leads/total_leads*100, 1)}%)" if total_leads > 0 else "0",
                avg_score,
                df['capture_timestamp'].max() if total_leads > 0 else "N/A"
            ]
        }
    
    def get_leads_df(self) -> pd.DataFrame:
        """Get leads as DataFrame - always fresh from file"""
        fresh_leads = self.load_leads_from_file()
        if not fresh_leads:
            return pd.DataFrame()
        
        df = pd.DataFrame(fresh_leads)
        col_order = ['capture_timestamp', 'full_name', 'work_email', 'company', 'job_title', 
                    'company_size', 'phone', 'qualification_score', 'lead_quality', 
                    'pages_visited', 'questions_asked', 'time_to_capture', 'use_case']
        
        existing_cols = [col for col in col_order if col in df.columns]
        return df[existing_cols]
    
    def export_to_excel(self) -> bytes:
        """Export current Excel file as download"""
        try:
            if os.path.exists(self.leads_file):
                with open(self.leads_file, 'rb') as f:
                    return f.read()
            else:
                # Fallback: create from fresh file data
                leads = self.load_leads_from_file()
                df = pd.DataFrame(leads)
                if df.empty:
                    return None
                    
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                    
                    summary_data = {
                        'Metric': ['Total Leads', 'High Quality Leads', 'Average Score'],
                        'Value': [
                            len(df),
                            len(df[df['lead_quality'].isin(['hot', 'very_hot'])]),
                            round(df['qualification_score'].mean(), 1) if len(df) > 0 else 0
                        ]
                    }
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
                
                output.seek(0)
                return output.getvalue()
        except Exception as e:
            st.error(f"Error exporting file: {e}")
            return None
    
    def get_file_info(self) -> dict:
        """Get file information - always fresh"""
        try:
            if os.path.exists(self.leads_file):
                file_size = os.path.getsize(self.leads_file)
                file_modified = datetime.fromtimestamp(os.path.getmtime(self.leads_file))
                
                return {
                    'exists': True,
                    'size_kb': round(file_size / 1024, 2),
                    'last_modified': file_modified.strftime("%Y-%m-%d %H:%M:%S"),
                    'total_leads': self.get_fresh_lead_count(),
                    'path': os.path.abspath(self.leads_file)
                }
            else:
                return {
                    'exists': False,
                    'size_kb': 0,
                    'last_modified': "Never",
                    'total_leads': 0,
                    'path': os.path.abspath(self.leads_file)
                }
        except Exception as e:
            return {'exists': False, 'error': str(e)}

class VisitorSession:
    """Enhanced visitor session with lead generation focus"""
    
    def __init__(self):
        if 'visitor_session' not in st.session_state:
            st.session_state.visitor_session = {
                'session_id': f"session_{int(time.time())}",
                'start_time': datetime.now(),
                'pages_visited': ['/home'],
                'current_page': '/home',
                'scroll_percentage': 0,
                'questions_asked': 0,
                'messages': [],
                'lead_captured': False,
                'lead_data': {},
                'engagement_score': 0,
                'lead_qualification': 'cold',
                'nudge_shown': False,
                'nudge_accepted': False,
                'nudge_declined': False,
                'lead_form_triggered': False,
                'show_lead_form': False,
                'high_intent_signals': [],
                'last_activity': datetime.now(),
                'form_should_show': False  # NEW: Explicit form display flag
            }
    
    @property
    def session(self):
        return st.session_state.visitor_session
    
    def trigger_lead_form(self):
        """Explicitly trigger lead form display"""
        self.session['show_lead_form'] = True
        self.session['form_should_show'] = True
        self.session['lead_form_triggered'] = True
        st.rerun()  # Force immediate rerun
    
    def update_page(self, page: str):
        """Update current page and recalculate engagement"""
        if page != self.session['current_page']:
            self.session['current_page'] = page
            if page not in self.session['pages_visited']:
                self.session['pages_visited'].append(page)
                self.add_intent_signal(f"Visited high-value page: {page}", BOT_CONFIG['page_values'].get(page, 5))
            self._recalculate_engagement()
    
    def update_scroll(self, percentage: int):
        """Update scroll and check for engagement triggers"""
        old_percentage = self.session['scroll_percentage']
        self.session['scroll_percentage'] = max(old_percentage, percentage)
        
        # High engagement scroll milestones
        if old_percentage < 70 <= percentage:
            self.add_intent_signal("Deep scroll engagement", 15)
        elif old_percentage < 90 <= percentage:
            self.add_intent_signal("Complete page read", 10)
            
        self._recalculate_engagement()
    
    def add_question(self, question: str):
        """Add question and boost engagement"""
        self.session['questions_asked'] += 1
        self.add_intent_signal(f"Asked question: {question[:50]}...", 10)
        self._recalculate_engagement()
    
    def add_intent_signal(self, signal: str, score_boost: int):
        """Add high-intent signal"""
        self.session['high_intent_signals'].append({
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'score_boost': score_boost,
            'page': self.session['current_page']
        })
    
    def _recalculate_engagement(self):
        """Recalculate engagement score and trigger lead capture if needed"""
        score = 0
        
        # Page visit scoring
        for page in self.session['pages_visited']:
            score += BOT_CONFIG['page_values'].get(page, 5)
        
        # Question engagement (higher weight for multiple questions)
        questions = self.session['questions_asked']
        if questions > 0:
            score += questions * 12 + (questions - 1) * 5  # Bonus for multiple questions
        
        # Time spent scoring (diminishing returns)
        time_spent = (datetime.now() - self.session['start_time']).seconds
        time_score = min(time_spent / 6, 30)  # Max 30 points for time
        score += time_score
        
        # Scroll engagement
        scroll_score = self.session['scroll_percentage'] * 0.3
        score += scroll_score
        
        # High-intent signals
        for signal in self.session['high_intent_signals']:
            score += signal['score_boost']
        
        # Page variety bonus
        if len(set(self.session['pages_visited'])) >= 3:
            score += 15
        
        self.session['engagement_score'] = int(score)
        self.session['lead_qualification'] = self._get_qualification()
        
        # AUTO-TRIGGER lead form if score threshold is met and not already captured
        if (self.should_trigger_lead_capture() and 
            not self.session['lead_captured'] and 
            not self.session['nudge_declined']):
            self.session['show_lead_form'] = True
            self.session['form_should_show'] = True
    
    def _get_qualification(self) -> str:
        """Determine lead qualification"""
        score = self.session['engagement_score']
        
        if score >= 100:
            return "very_hot"
        elif score >= 75:
            return "hot"  
        elif score >= 50:
            return "warm"
        else:
            return "cold"
    
    def should_trigger_lead_capture(self) -> bool:
        """Check if lead capture should be triggered"""
        if self.session['lead_captured'] or self.session['lead_form_triggered']:
            return False
        
        thresholds = BOT_CONFIG['engagement_thresholds']
        score = self.session['engagement_score']
        
        # Primary trigger: engagement score
        if score >= thresholds['lead_capture_score']:
            return True
        
        # Secondary triggers for high-intent behavior
        scroll_trigger = self.session['scroll_percentage'] >= thresholds['scroll_threshold']
        time_trigger = (datetime.now() - self.session['start_time']).seconds >= thresholds['time_threshold']
        question_trigger = self.session['questions_asked'] >= thresholds['question_threshold']
        page_trigger = len(self.session['pages_visited']) >= thresholds['page_variety_threshold']
        
        # Need at least 2 secondary triggers + minimum score
        secondary_triggers = sum([scroll_trigger, time_trigger, question_trigger, page_trigger])
        return secondary_triggers >= 2 and score >= thresholds['high_intent_score']
    
    def should_show_nudge(self) -> bool:
        """Check if nudge should be shown"""
        if (self.session['lead_captured'] or 
            self.session.get('nudge_declined', False) or
            self.session['nudge_shown'] or
            self.session['show_lead_form'] or
            self.session['form_should_show']):
            return False
        
        score = self.session['engagement_score']
        return score >= BOT_CONFIG['engagement_thresholds']['high_intent_score']

def show_page_info(visitor):
    """Display page-specific content based on current page"""
    current_page = visitor.session['current_page']
    page_info = BOT_CONFIG['page_content'].get(current_page)
    
    if page_info:
        # Create an attractive info box
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h3 style="margin: 0 0 15px 0; color: white;">{page_info['title']}</h3>
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 10px;
                backdrop-filter: blur(10px);
                line-height: 1.6;
            ">
                {page_info['content'].replace('•', '<br>•').replace('*', '<em>').replace('*', '</em>')}
        """, unsafe_allow_html=True)

def init_app():
    """Initialize the application"""
    st.set_page_config(
        page_title="🤖 Sales Lead Generation Bot",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize components
    VisitorSession()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

def simulate_visitor_behavior():
    """Enhanced visitor simulation with refresh functionality"""
    st.sidebar.title("🌐 Visitor Behavior Simulator")
    
    visitor = VisitorSession()
    lead_capture = LeadCapture()  # Create fresh instance each time
    
    # Add refresh button at the top
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", help="Refresh lead count and file info"):
            st.rerun()
    
    with col2:
        # Show fresh lead count
        fresh_count = lead_capture.get_fresh_lead_count()
        st.metric("Lead Count", fresh_count)
    
    # Current engagement display
    st.sidebar.markdown("### 📊 Current Engagement")
    score = visitor.session['engagement_score']
    qualification = visitor.session['lead_qualification']
    
    color_map = {"cold": "🔵", "warm": "🟡", "hot": "🟠", "very_hot": "🔴"}
    st.sidebar.metric("Engagement Score", score)
    st.sidebar.metric("Qualification", f"{color_map.get(qualification, '⚪')} {qualification.title()}")
    
    # DEBUG INFO
    # st.sidebar.markdown("### 🔍 Debug Info")
    # st.sidebar.write(f"Should trigger: {visitor.should_trigger_lead_capture()}")
    # st.sidebar.write(f"Show form: {visitor.session['show_lead_form']}")
    # st.sidebar.write(f"Form should show: {visitor.session['form_should_show']}")
    # st.sidebar.write(f"Lead captured: {visitor.session['lead_captured']}")
    # st.sidebar.write(f"Nudge declined: {visitor.session['nudge_declined']}")
    
    # Page simulation
    st.sidebar.markdown("### 📄 Page Navigation")
    pages = list(BOT_CONFIG['page_contexts'].keys())
    current_idx = pages.index(visitor.session['current_page']) if visitor.session['current_page'] in pages else 0
    
    selected_page = st.sidebar.selectbox(
        "Current Page",
        pages,
        index=current_idx,
        format_func=lambda x: f"{x} ({BOT_CONFIG['page_values'].get(x, 0)} pts)"
    )
    
    if selected_page != visitor.session['current_page']:
        visitor.update_page(selected_page)
        st.rerun()
    
    # Scroll simulation
    st.sidebar.markdown("### 📏 Scroll Behavior")
    scroll_percent = st.sidebar.slider("Scroll Percentage", 0, 100, visitor.session['scroll_percentage'])
    
    if scroll_percent != visitor.session['scroll_percentage']:
        visitor.update_scroll(scroll_percent)
        st.rerun()
    
    # Quick scenarios
    st.sidebar.markdown("### ⚡ Quick Scenarios")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔥 High Intent", help="Simulate high-intent visitor"):
            visitor.update_page("/pricing")
            visitor.update_scroll(85)
            visitor.add_intent_signal("Pricing focus behavior", 20)
            st.rerun()
    
    with col2:
        if st.button("🔒 Security Focus", help="Security-focused visitor"):
            visitor.update_page("/security")
            visitor.update_scroll(75)
            visitor.add_intent_signal("Security compliance interest", 15)
            st.rerun()
    
    # Manual trigger for testing
    st.sidebar.markdown("### 🧪 Testing Controls")
    if st.sidebar.button("🎯 Force Lead Form", help="Manually trigger lead form"):
        visitor.trigger_lead_form()
    
    if st.sidebar.button("🔄 Reset Session", help="Reset visitor session"):
        for key in list(st.session_state.keys()):
            if 'visitor_session' in key:
                del st.session_state[key]
        st.rerun()
    
    # Lead capture status
    st.sidebar.markdown("### 🎯 Lead Capture Status")
    should_capture = visitor.should_trigger_lead_capture()
    threshold = BOT_CONFIG['engagement_thresholds']['lead_capture_score']
    
    if visitor.session['lead_captured']:
        st.sidebar.success("✅ Lead Captured!")
    elif visitor.session.get('nudge_declined'):
        st.sidebar.info("😊 User preferred to continue browsing")
    elif visitor.session['show_lead_form'] or visitor.session['form_should_show']:
        st.sidebar.warning("🎯 Lead form is showing!")
    elif should_capture:
        st.sidebar.warning(f"🎯 Ready to capture! (Score: {score})")
    else:
        remaining = max(0, threshold - score)
        st.sidebar.info(f"📈 Building engagement... {remaining} points to go")

def get_agent_response(query: str, context: dict) -> dict:
    """Get contextual response from agent"""
    if not AGENT_AVAILABLE:
        return {
            'content': "Agent not available. Please check your agent.py file.",
            'source': "System Error",
            'success': False
        }
    
    try:
        # Add rich context for the agent
        contextual_query = f"""
        CONTEXT:
        - Page: {context.get('current_page', 'unknown')}
        - Pages visited: {', '.join(context.get('pages_visited', []))}
        - Questions asked: {context.get('questions_asked', 0)}
        - Engagement level: {context.get('lead_qualification', 'unknown')}
        - Scroll depth: {context.get('scroll_percentage', 0)}%
        
        QUESTION: {query}
        
        Please provide a helpful answer with source attribution.
        """
        
        response = ask_agent(contextual_query)
        
        return {
            'content': response,
            'source': f"Knowledge Base • {context.get('current_page', 'General')} Context",
            'success': True
        }
        
    except Exception as e:
        return {
            'content': "I apologize, but I'm having trouble accessing that information right now. Could you please try rephrasing your question?",
            'source': "System Fallback",
            'success': False
        }

def show_lead_capture_form():
    """Enhanced lead capture form - now with better visibility and immediate display"""
    st.markdown("---")
    
    # Make it more prominent
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4;">
        <h2 style="color: #1f77b4; margin-top: 0;">🚀 Great! You seem really interested!</h2>
        <p style="font-size: 16px; margin-bottom: 0;">Let me get a few quick details so I can provide you with personalized information and pricing.</p>
    </div>
    """, unsafe_allow_html=True)
    
    visitor = VisitorSession()
    lead_capture = LeadCapture()
    
    # Show why we're asking (builds trust)
    st.info("💡 **Why we ask:** This helps us provide you with the most relevant pricing, features, and integration options for your specific needs.")
    
    with st.form("lead_capture_form", clear_on_submit=False):
        st.markdown("**Just a few details to get you the right information:**")
        
        lead_data = {}
        
        # Create responsive layout
        col1, col2 = st.columns(2)
        
        with col1:
            lead_data['full_name'] = st.text_input(
                "Full Name *", 
                placeholder="John Smith",
                key="lead_full_name"
            )
            
            lead_data['company'] = st.text_input(
                "Company *",
                placeholder="Acme Corp",
                key="lead_company"
            )
            
            lead_data['company_size'] = st.selectbox(
                "Company Size",
                [''] + BOT_CONFIG['lead_fields'][4]['options'],
                key="lead_company_size"
            )
        
        with col2:
            lead_data['work_email'] = st.text_input(
                "Work Email *",
                placeholder="john@acme.com",
                key="lead_work_email"
            )
            
            lead_data['job_title'] = st.text_input(
                "Job Title",
                placeholder="CTO, Developer, etc.",
                key="lead_job_title"
            )
            
            lead_data['phone'] = st.text_input(
                "Phone Number",
                placeholder="+1 (555) 123-4567",
                key="lead_phone"
            )
        
        # Use case
        lead_data['use_case'] = st.text_area(
            "What's your primary use case?",
            placeholder="Tell us briefly about what you're looking to accomplish...",
            height=80,
            key="lead_use_case"
        )
        
        # Submit with better UX
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "🎯 Get My Personalized Information", 
                type="primary",
                use_container_width=True
            )
        
        # Skip option
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.form_submit_button("⏩ Skip for now", help="Continue without providing details"):
                visitor.session['nudge_declined'] = True
                visitor.session['show_lead_form'] = False
                visitor.session['form_should_show'] = False
                st.info("No problem! Feel free to keep asking questions.")
                time.sleep(1)
                st.rerun()
        
        if submitted:
            # Validation
            errors = []
            required_fields = ['full_name', 'work_email', 'company']
            
            for field in required_fields:
                if not lead_data.get(field, '').strip():
                    field_label = field.replace('_', ' ').title()
                    errors.append(f"{field_label} is required")
            
            # Email validation
            email = lead_data.get('work_email', '').strip()
            if email and ('@' not in email or '.' not in email.split('@')[-1]):
                errors.append("Please enter a valid work email address")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Clean data
                clean_data = {k: v.strip() if isinstance(v, str) else v 
                             for k, v in lead_data.items() if v}
                
                # Update session state
                visitor.session['lead_captured'] = True
                visitor.session['show_lead_form'] = False
                visitor.session['form_should_show'] = False
                visitor.session['lead_data'] = clean_data
                
                # Save to database and Excel file
                lead_capture.save_lead(clean_data, visitor.session)
                
                # Success feedback
                st.success("✅ Perfect! Your information has been captured.")
                st.balloons()
                
                # Continue conversation
                st.info("💬 Feel free to keep asking questions - I can now give you more targeted answers!")
                
                time.sleep(2)
                st.rerun()

def display_chat_interface():
    """Enhanced chat interface with improved lead capture logic"""
    visitor = VisitorSession()
    
    # CRITICAL: Check for immediate form display first
    if (visitor.session.get('form_should_show', False) or 
        (visitor.session.get('show_lead_form', False) and 
         not visitor.session.get('lead_captured', False) and 
         not visitor.session.get('nudge_declined', False))):
        
        # Show form immediately - no other content
        show_lead_capture_form()
        return
    
    # Show page-specific information above chat
    show_page_info(visitor)
    
    st.markdown("### 💬 Ask About Our Platform")
    st.markdown("*Get instant answers about pricing, security, integrations, and more!*")
    
    # Show nudge only if form is not being shown
    if visitor.should_show_nudge():
        visitor.session['nudge_shown'] = True
        current_page = visitor.session['current_page']
        nudge_message = BOT_CONFIG['nudge_messages'].get(current_page, BOT_CONFIG['nudge_messages']['default'])
        
        # Enhanced nudge message with context
        engagement_context = ""
        if visitor.session['questions_asked'] >= 2:
            engagement_context = "I see you've been asking great questions! "
        elif visitor.session['scroll_percentage'] >= 70:
            engagement_context = "I noticed you've been exploring the page thoroughly! "
        elif len(visitor.session['pages_visited']) >= 3:
            engagement_context = "You've been checking out different sections - that's great! "
        
        full_message = f"{engagement_context}{nudge_message}"
        
        # Show the nudge
        st.info(f"🤖 {full_message}")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Yes, I'm interested!", key="nudge_accept", type="primary"):
                visitor.session['nudge_accepted'] = True
                visitor.session['show_lead_form'] = True
                visitor.session['form_should_show'] = True  # Explicit trigger
                visitor.add_intent_signal("Accepted lead capture nudge", 25)
                st.rerun()  # Force immediate rerun
        
        with col2:
            if st.button("⏰ Maybe later", key="nudge_decline"):
                visitor.session['nudge_declined'] = True
                visitor.session['show_lead_form'] = False
                visitor.session['form_should_show'] = False
                visitor.add_intent_signal("Declined lead capture nudge", 5)
                st.success("No problem! Feel free to keep asking questions.")
                st.rerun()
        
        # Add some spacing
        st.markdown("---")
    
    # Regular chat interface
    # Chat history display
    for message in st.session_state.chat_history:
        with st.chat_message(message['role']):
            st.write(message['content'])
            
            if message['role'] == 'assistant' and message.get('source'):
                st.caption(f"📚 {message['source']}")
    
    # Chat input
    prompt = st.chat_input("Ask about pricing, security, API limits, integrations...")
    
    if prompt:
        # Add user message
        user_message = {
            'role': 'user',
            'content': prompt,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.chat_history.append(user_message)
        
        # Update visitor engagement
        visitor.add_question(prompt)
        
        # Get AI response
        with st.spinner("Getting your answer..."):
            response_data = get_agent_response(prompt, visitor.session)
        
        # Add assistant response
        assistant_message = {
            'role': 'assistant',
            'content': response_data['content'],
            'source': response_data['source'],
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.chat_history.append(assistant_message)
        
        st.rerun()

def show_leads_dashboard():
    """Display leads dashboard with real-time file information"""
    lead_capture = LeadCapture()
    
    st.markdown("### 📊 Leads Dashboard")
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("**Real-time lead data from Excel file**")
    with col2:
        if st.button("🔄 Refresh Now", type="primary"):
            st.rerun()
    
    # File information - always fresh
    file_info = lead_capture.get_file_info()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if file_info['exists']:
            st.success("📁 File Exists")
        else:
            st.info("📁 No File Yet")
    
    with col2:
        st.metric("File Size", f"{file_info['size_kb']} KB")
    
    with col3:
        st.metric("Total in File", file_info['total_leads'])
    
    with col4:
        st.metric("Last Modified", file_info['last_modified'])
    
    # Show file path
    if 'path' in file_info:
        st.info(f"💡 **File Location:** `{file_info['path']}`")
    
    # Auto-refresh indicator
    st.markdown("*📡 Data refreshes automatically when external APIs update the Excel file*")
    
    # Summary metrics - always fresh
    leads_df = lead_capture.get_leads_df()
    
    if leads_df.empty:
        st.info("No leads captured yet. Start engaging with visitors!")
        return
    
    # Performance metrics
    st.markdown("### 📈 Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(leads_df))
    
    with col2:
        hot_leads = len(leads_df[leads_df['lead_quality'].isin(['hot', 'very_hot'])])
        st.metric("Hot Leads", hot_leads)
    
    with col3:
        avg_score = leads_df['qualification_score'].mean()
        st.metric("Avg Score", f"{avg_score:.1f}")
    
    with col4:
        avg_time = leads_df['time_to_capture'].mean()
        st.metric("Avg Time to Capture", f"{avg_time:.0f}s")
    
    # Recent leads table
    st.markdown("**Recent Leads:**")
    display_cols = ['capture_timestamp', 'full_name', 'company', 'work_email', 
                   'lead_quality', 'qualification_score', 'questions_asked']
    
    available_cols = [col for col in display_cols if col in leads_df.columns]
    recent_leads = leads_df[available_cols].tail(10).sort_values('capture_timestamp', ascending=False)
    
    st.dataframe(recent_leads, use_container_width=True)
    
    # Export functionality
    st.markdown("### 📥 Export Leads")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Download Excel Report", type="primary"):
            excel_data = lead_capture.export_to_excel()
            if excel_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                st.download_button(
                    label="💾 Download Excel File",
                    data=excel_data,
                    file_name=f"leads_report_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col2:
        if st.button("📋 View Full Data"):
            st.json(leads_df.to_dict('records'))

def main():
    """Enhanced main application with immediate state handling"""
    init_app()
    
    # Initialize visitor session
    visitor = VisitorSession()
    lead_capture = LeadCapture()
    
    # Header
    st.title("🎯 Sales Lead Generation Bot")
    st.markdown("**Engage → Inform → Capture** | *Smart lead generation through natural conversation*")
    
    # Status indicators with fresh data
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if AGENT_AVAILABLE:
            st.success("🟢 Agent Ready")
        else:
            st.error("🔴 Agent Offline")
    
    with col2:
        score = visitor.session['engagement_score']
        threshold = BOT_CONFIG['engagement_thresholds']['lead_capture_score']
        if score >= threshold:
            st.success(f"🔥 Lead Ready ({score})")
        else:
            st.info(f"📈 Engaging ({score}/{threshold})")
    
    with col3:
        # Always get fresh lead count
        total_leads = lead_capture.get_fresh_lead_count()
        # st.metric("Leads Captured", total_leads)
    
    # PRIORITY 1: Show lead form immediately if triggered
    if (visitor.session.get('form_should_show', False) or 
        (visitor.session.get('show_lead_form', False) and 
         not visitor.session.get('lead_captured', False) and
         not visitor.session.get('nudge_declined', False))):
        
        st.markdown("---")
        st.markdown("### 🎯 Let's Get You Set Up!")
        show_lead_capture_form()
        
        # Still show sidebar for testing
        with st.sidebar:
            simulate_visitor_behavior()
        
        return  # Don't show the rest of the interface
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tabbed interface
        tab1, tab2 = st.tabs(["💬 Chat Interface", "📊 Leads Dashboard"])
        
        with tab1:
            display_chat_interface()
        
        with tab2:
            show_leads_dashboard()
    
    with col2:
        # Visitor simulation
        simulate_visitor_behavior()
        

if __name__ == "__main__":
    main()