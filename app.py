import os
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.interview_engine import InterviewCoordinator
from core.parser import parse_resume_text, parse_job_description
from utils.storage import save_json_report
from core.extended_questions import INTERVIEW_QUESTIONS
from core.document_validator import validate_is_resume, calculate_resume_accuracy, get_document_type_warning

st.set_page_config(page_title="InterviewDNA AI", layout="wide", initial_sidebar_state="expanded")

DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* Main layout overrides */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #e2e8f0;
}
.stApp {
    background: radial-gradient(circle at 80% 10%, rgba(124, 58, 237, 0.08), transparent 40%),
                radial-gradient(circle at 10% 90%, rgba(6, 182, 212, 0.08), transparent 40%),
                #070a13;
}

/* Custom Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}

/* Glassmorphism Card Wrapper */
.glass-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    margin-bottom: 20px;
    transition: transform 0.3s ease, border-color 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(6, 182, 212, 0.25);
    transform: translateY(-2px);
}

/* Custom Status and Integrity Alert Boxes */
.integrity-warning {
    padding: 16px;
    border-left: 4px solid #f43f5e;
    background: rgba(244, 63, 94, 0.06);
    border-radius: 8px;
    margin: 14px 0;
    font-size: 14px;
    border: 1px solid rgba(244, 63, 94, 0.15);
    border-left-width: 4px;
    animation: fadeIn 0.4s ease;
}
.integrity-success {
    padding: 16px;
    border-left: 4px solid #10b981;
    background: rgba(16, 185, 129, 0.06);
    border-radius: 8px;
    margin: 14px 0;
    font-size: 14px;
    border: 1px solid rgba(16, 185, 129, 0.15);
    border-left-width: 4px;
    animation: fadeIn 0.4s ease;
}
.integrity-info {
    padding: 16px;
    border-left: 4px solid #06b6d4;
    background: rgba(6, 182, 212, 0.06);
    border-radius: 8px;
    margin: 14px 0;
    font-size: 14px;
    border: 1px solid rgba(6, 182, 212, 0.15);
    border-left-width: 4px;
    animation: fadeIn 0.4s ease;
}

/* Style metric blocks to look premium */
[data-testid="stMetricValue"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 28px !important;
    background: linear-gradient(135deg, #ffffff 40%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    color: #94a3b8 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Premium Buttons Styling */
div.stButton > button {
    background: linear-gradient(135deg, #06b6d4 0%, #7c3aed 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2) !important;
    transition: all 0.3s ease !important;
    width: 100%;
}
div.stButton > button:hover {
    transform: translateY(-1px) scale(1.01) !important;
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.35) !important;
    background: linear-gradient(135deg, #0891b2 0%, #6d28d9 100%) !important;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #04060b !important;
    border-right: 1px solid rgba(255, 255, 255, 0.03) !important;
}

/* Custom Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(255,255,255,0.01) !important;
    padding: 6px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.03) !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    padding: 10px 20px !important;
    color: #94a3b8 !important;
    transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(6, 182, 212, 0.12) !important;
    color: #06b6d4 !important;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
</style>
"""

st.markdown(DARK_CSS, unsafe_allow_html=True)

if "coordinator" not in st.session_state:
    st.session_state.coordinator = InterviewCoordinator()
    st.session_state.resume_text = ""
    st.session_state.jd_text = ""
    st.session_state.question_start = 0.0
    st.session_state.question_timer = 0.0
    st.session_state.last_question = None
    st.session_state.current_answer = ""
    st.session_state.state_cached = {}
    st.session_state.candidate_name = ""
    st.session_state.candidate_name_submitted = False


def render_header():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
            <div style='padding: 10px 0;'>
                <h1 style='margin:0; font-size: 38px; font-weight: 800; background: linear-gradient(135deg, #ffffff 30%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🧬 InterviewDNA AI</h1>
                <p style='color:#94a3b8; font-size: 15px; margin: 4px 0 0 0;'>Adaptive Mock Interviews powered by Gemini 2.5, Real-Time Integrity Auditing, & Explainable Performance Reports.</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div style='text-align:right; padding: 12px 16px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04); border-radius: 12px; backdrop-filter: blur(8px);'>
                <span style='color:#06b6d4; font-size: 13px; font-weight: 600; letter-spacing: 0.5px;'>✨ HACKATHON PROJECT</span>
                <br>
                <span style='color:#10b981; font-size: 12px; font-weight: 500;'>🛡️ Live Anti-Cheat</span>
                <br>
                <span style='color:#7c3aed; font-size: 12px; font-weight: 500;'>📈 Deep DNA Profiler</span>
            </div>
        """, unsafe_allow_html=True)


def sidebar_controls():
    st.sidebar.title("⚙️ Interview Settings")
    st.sidebar.markdown("### Session Configuration")
    
    # Display candidate name if collected, otherwise show status
    if st.session_state.candidate_name_submitted:
        st.sidebar.info(f"👤 **{st.session_state.candidate_name}**")
    else:
        st.sidebar.warning("⏳ Awaiting candidate name...")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Integrity Features")
    st.sidebar.write("✓ Plagiarism Detection")
    st.sidebar.write("✓ Time Anomaly Detection")
    st.sidebar.write("✓ Fake Resume/JD Detection")
    st.sidebar.write("✓ Behavioral Analysis")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### AI Integration")
    # Check Gemini API status
    from core.gemini_client import GeminiClient
    client = GeminiClient()
    if client.api_key and len(client.api_key) > 5:
        api_status = "🟢 Active"
        st.sidebar.success(f"Gemini API: {api_status}")
        if st.sidebar.button("⚡ Test AI Connection", key="test_ai_conn"):
            with st.sidebar.spinner("Testing API..."):
                response = client.generate("Say 'Connection Successful!' in 3 words.", temperature=0.1, max_output_tokens=10)
                if response:
                    st.sidebar.success(f"Response: {response}")
                else:
                    st.sidebar.error("❌ API call failed. Check key.")
    else:
        api_status = "🔴 Inactive"
        st.sidebar.error(f"Gemini API: {api_status}")
        st.sidebar.warning("Set GEMINI_API_KEY environment variable for AI features.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 📚 Question Library")
    st.sidebar.metric("Total Questions", len(INTERVIEW_QUESTIONS))
    st.sidebar.write("- 14 Technical")
    st.sidebar.write("- 7 Conceptual")
    st.sidebar.write("- 8 Behavioural")
    st.sidebar.write("- 8 Scenario-based")


def show_integrity_warnings(integrity_check: dict, type_label: str):
    if not integrity_check:
        return
    
    score = integrity_check.get("score", 0.0)
    reasons = integrity_check.get("reasons", [])
    is_suspicious = integrity_check.get("is_suspicious", False)
    
    if is_suspicious:
        st.markdown(f"""
            <div class='integrity-warning'>
                <strong>⚠️ Integrity Warning: {type_label}</strong><br>
                Authenticity Score: {int(score*100)}%
        """, unsafe_allow_html=True)
        for reason in reasons:
            st.markdown(f"  • {reason}", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class='integrity-success'>
                <strong>✓ Authenticity Verified: {type_label}</strong><br>
                Authenticity Score: {int((1-score)*100)}%
            </div>
        """, unsafe_allow_html=True)


def show_resume_analyzer():
    st.subheader("📄 Step 1: Resume Analysis")
    
    # Candidate name collection (mandatory)
    if not st.session_state.candidate_name_submitted:
        st.markdown("<div class='integrity-info'>", unsafe_allow_html=True)
        st.write("**👤 Candidate Information (Required)**")
        
        with st.form("candidate_form"):
            candidate_name = st.text_input(
                "Enter candidate name",
                placeholder="e.g., John Doe"
            )
            submitted = st.form_submit_button("✓ Confirm Candidate Name")
        
        if submitted:
            if candidate_name.strip():
                st.session_state.candidate_name = candidate_name.strip()
                st.session_state.candidate_name_submitted = True
                st.success(f"✓ Candidate recorded: {candidate_name.strip()}")
                st.rerun()
            else:
                st.error("❌ Please enter a candidate name")
        
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Show collected candidate info
    col_info, col_change = st.columns([3, 1])
    with col_info:
        st.info(f"👤 Candidate: **{st.session_state.candidate_name}**")
    with col_change:
        if st.button("🔄 Change", key="change_candidate"):
            st.session_state.candidate_name = ""
            st.session_state.candidate_name_submitted = False
            st.rerun()
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        resume_file = st.file_uploader("Upload candidate resume (PDF)", type=["pdf"], key="resume_upload")
    with col2:
        st.write("")
        st.write("")
        if st.button("📋 Paste Resume Text", key="paste_resume_btn"):
            st.session_state.show_paste_resume = True
    
    text_resume = st.session_state.resume_text
    if st.session_state.get("show_paste_resume"):
        text_resume = st.text_area("Paste resume text here", value=st.session_state.resume_text, height=220, key="resume_paste_area")
    
    if resume_file is not None:
        try:
            import pdfplumber
            with pdfplumber.open(resume_file) as pdf:
                text_resume = "\n".join(page.extract_text() or "" for page in pdf.pages)
            st.session_state.resume_text = text_resume
            st.success("✓ PDF resume extracted successfully.")
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return
    
    if st.button("🔍 Analyze Resume", key="analyze_resume") and text_resume.strip():
        with st.spinner("Analyzing resume..."):
            # Step 1: Validate if it's actually a resume
            validation = validate_is_resume(text_resume)
            st.session_state.resume_text = text_resume
            
            # Display warning for clear non-resumes (cover letters only)
            if not validation["is_valid"] and validation["document_type"] == "cover_letter":
                st.warning(f"⚠️ {get_document_type_warning(validation)}")
                st.info("Tip: Please upload your resume instead of a cover letter.")
                return
            
            # For other validation issues, show warning but continue
            if not validation["is_valid"]:
                st.warning(f"⚠️ Document type uncertainty: {validation['reason']}")
            
            # Step 2: Calculate resume accuracy
            accuracy = calculate_resume_accuracy(text_resume)
            st.session_state.resume_accuracy = accuracy
            
            st.success("✓ Resume analysis complete.")
            
            # Step 3: Display resume quality & accuracy
            st.markdown("---")
            st.subheader("📊 Resume Quality Assessment")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Accuracy Score", f"{accuracy['overall_accuracy']:.0f}%")
            col2.metric("Quality Level", accuracy['quality_level'])
            col3.metric("Document Length", f"{accuracy['text_length']} chars")
            col4.metric("Timeline Coverage", f"{accuracy['date_count']} dates")
            
            # Accuracy progress bar
            accuracy_pct = accuracy['overall_accuracy'] / 100.0
            st.progress(accuracy_pct, text=f"Resume Completeness: {accuracy['overall_accuracy']:.0f}%")
            
            # Display section scores
            st.write("**Section Coverage:**")
            col1, col2, col3, col4 = st.columns(4)
            sections = ["Experience", "Skills", "Education", "Contact"]
            section_names = ["experience", "skills", "education", "contact"]
            for idx, (section, section_name) in enumerate(zip(sections, section_names)):
                score = accuracy['section_scores'].get(section_name, 0)
                status = "✅" if score == 100 else "❌"
                [col1, col2, col3, col4][idx].write(f"{status} {section}")
            
            # Show recommendations if not perfect
            if accuracy['missing_sections']:
                st.markdown("<div class='integrity-info'>", unsafe_allow_html=True)
                st.write("**Recommendations for Improvement:**")
                for i, rec in enumerate(accuracy['recommendations'], 1):
                    st.write(f"{i}. {rec}")
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='integrity-success'>", unsafe_allow_html=True)
                st.write("**✓ Excellent resume with all sections included!**")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Step 4: Analyze with system
            result = st.session_state.coordinator.analyze_resume(text_resume)
            profile = result
            integrity = result.get("integrity_check", {})
            
            st.markdown("---")
            show_integrity_warnings(integrity, "Resume")
            
            with st.expander("📊 Candidate Profile", expanded=True):
                col1, col2, col3 = st.columns(3)
                col1.metric("Name", profile.get("name", "Candidate")[:30])
                col2.metric("Title", profile.get("title", "Professional")[:30])
                col3.metric("Detected Skills", len(profile.get("skills", [])))
                
                st.write("**Professional Summary**")
                summary_text = "\n".join(profile.get("summary", [])) if profile.get("summary") else "No summary detected."
                st.write(summary_text[:500])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**🛠️ Skills**")
                for skill in profile.get("skills", [])[:8]:
                    st.write(f"• {skill}")
            with col2:
                st.write("**💼 Experience**")
                for exp in profile.get("experience", [])[:5]:
                    st.write(f"• {exp[:40]}...")
            with col3:
                st.write("**🎓 Education**")
                for edu in profile.get("education", [])[:5]:
                    st.write(f"• {edu[:40]}...")


def show_jd_analyzer():
    st.subheader("💼 Step 2: Job Description Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        jd_file = st.file_uploader("Upload job description (TXT)", type=["txt"], key="jd_upload")
    with col2:
        st.write("")
        st.write("")
        if st.button("📋 Paste JD Text", key="paste_jd_btn"):
            st.session_state.show_paste_jd = True
    
    jd_text = st.session_state.jd_text
    if st.session_state.get("show_paste_jd"):
        jd_text = st.text_area("Paste job description here", value=st.session_state.jd_text, height=220, key="jd_paste_area")
    
    if jd_file is not None:
        jd_text = jd_file.getvalue().decode("utf-8")
        st.session_state.jd_text = jd_text
    
    if st.button("🔍 Analyze Job Description", key="analyze_jd") and jd_text.strip():
        with st.spinner("Analyzing job description..."):
            result = st.session_state.coordinator.analyze_job_description(jd_text)
            jd_profile = result
            integrity = result.get("integrity_check", {})
            st.session_state.jd_text = jd_text
            
            st.success("✓ Job description analysis complete.")
            
            show_integrity_warnings(integrity, "Job Description")
            
            with st.expander("📊 Role Requirements", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Experience Level", jd_profile.get("experience_level", "N/A"))
                with col2:
                    st.metric("Required Skills Count", len(jd_profile.get("required_skills", [])))
                
                st.write("**Required Skills**")
                st.write(", ".join(jd_profile.get("required_skills", [])))
                
                st.write("**Key Keywords**")
                st.write(", ".join(jd_profile.get("keywords", [])))


def show_interview_lab():
    st.subheader("🎤 Step 3: AI Interview Engine")
    
    if not st.session_state.coordinator.resume_profile or not st.session_state.coordinator.job_profile:
        st.warning("⚠️ Complete resume and job description analysis before launching the interview.")
        return
    
    # Show match score before starting
    if st.session_state.coordinator.state.status == "not_started":
        col1, col2, col3 = st.columns(3)
        match_score = st.session_state.coordinator.compute_match()
        alignment_score = st.session_state.coordinator.role_alignment_score()
        initial_difficulty = st.session_state.coordinator.initial_difficulty()
        
        col1.metric("Skill Match", f"{match_score:.1f}%")
        col2.metric("Role Alignment", f"{alignment_score:.1f}%")
        col3.metric("Starting Difficulty", initial_difficulty)
        
        if st.button("🚀 Start Interview", key="start_interview"):
            st.session_state.coordinator.start_interview()
            st.session_state.question_start = time.time()
            st.session_state.current_answer = ""
            st.session_state.last_question = st.session_state.coordinator.next_question()
            st.rerun()
    
    if st.session_state.coordinator.state.status == "running" and st.session_state.last_question:
        # Interview running - show question and timer
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Question", st.session_state.coordinator.state.question_number)
        col2.metric("Difficulty", st.session_state.coordinator.state.current_difficulty)
        col3.metric("Pressure Mode", "🔥 YES" if st.session_state.coordinator.state.pressure_mode else "❌ No")
        col4.metric("Average Score", f"{st.session_state.coordinator.state.current_average():.1f}")
        
        # Glassmorphism question container
        st.markdown(f"""
            <div class='glass-card' style='margin-top: 15px;'>
                <span style='color: #06b6d4; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>🎤 QUESTION {st.session_state.coordinator.state.question_number} ({st.session_state.last_question['category']})</span>
                <h3 style='margin: 8px 0; color: #ffffff; line-height: 1.4;'>{st.session_state.last_question['text']}</h3>
                <span style='color: #94a3b8; font-size: 13px;'>Level: <b>{st.session_state.last_question.get('skill_level', 'N/A')}</b> | Target Difficulty: <b>{st.session_state.last_question['difficulty']}</b></span>
            </div>
        """, unsafe_allow_html=True)
        
        # Render dynamic animated countdown timer
        import streamlit.components.v1 as components
        duration = 30 if st.session_state.coordinator.state.pressure_mode else 45
        timer_html = f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 12px; text-align: center; backdrop-filter: blur(12px); box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.4); font-family: 'Outfit', sans-serif;">
            <div style="font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 3px;">Time Remaining</div>
            <div id="countdown-clock" style="font-size: 28px; font-weight: 700; color: #06b6d4; transition: color 0.5s ease;">{duration}s</div>
            <div style="width: 100%; background: rgba(255,255,255,0.06); height: 5px; border-radius: 3px; margin-top: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.03);">
                <div id="countdown-bar" style="background: linear-gradient(90deg, #06b6d4, #7c3aed); height: 100%; width: 100%; transition: width 1s linear, background 0.5s ease; border-radius: 3px;"></div>
            </div>
        </div>
        <script>
            var duration = {duration};
            var start = Date.now();
            var clock = document.getElementById('countdown-clock');
            var bar = document.getElementById('countdown-bar');
            var interval = setInterval(function() {{
                var elapsed = Math.floor((Date.now() - start) / 1000);
                var remaining = duration - elapsed;
                if (remaining <= 0) {{
                    clock.innerHTML = "⏱️ Time's Up!";
                    clock.style.color = "#f43f5e";
                    bar.style.width = "0%";
                    bar.style.background = "#f43f5e";
                    clearInterval(interval);
                }} else {{
                    clock.innerHTML = remaining + "s";
                    var pct = (remaining / duration) * 100;
                    bar.style.width = pct + "%";
                    if (remaining <= 10) {{
                        clock.style.color = "#f43f5e";
                        bar.style.background = "#f43f5e";
                    }} else if (remaining <= 20) {{
                        clock.style.color = "#f59e0b";
                        bar.style.background = "#f59e0b";
                    }}
                }}
            }}, 1000);
        </script>
        """
        components.html(timer_html, height=95)
        
        st.text_area("Your answer (be original - plagiarism detection is active)", key="answer_text", height=180)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Submit Answer", key="submit_answer"):
                time_taken = time.time() - st.session_state.question_start
                result = st.session_state.coordinator.answer_question(st.session_state.answer_text, time_taken)
                
                # Show evaluation with warnings
                eval_data = result["evaluation"]
                
                col_a, col_b = st.columns(2)
                with col_a:
                    score_color = "🟢" if eval_data["score"] >= 70 else "🟡" if eval_data["score"] >= 50 else "🔴"
                    st.metric(f"{score_color} Score", eval_data["score"])
                
                with col_b:
                    st.metric("⏱️ Time", f"{time_taken:.1f}s")
                
                # Show metric breakdown
                metric_cols = st.columns(4)
                metric_cols[0].metric("Accuracy", f"{eval_data['accuracy']:.0f}%")
                metric_cols[1].metric("Clarity", f"{eval_data['clarity']:.0f}%")
                metric_cols[2].metric("Depth", f"{eval_data['depth']:.0f}%")
                metric_cols[3].metric("Relevance", f"{eval_data['relevance']:.0f}%")
                
                # Cheating detection warnings
                if eval_data.get("is_plagiarism_suspicious"):
                    st.markdown(f"""
                        <div class='integrity-warning'>
                            <strong>⚠️ Plagiarism Risk Detected</strong><br>
                            Risk Score: {int(eval_data.get('plagiarism_risk', 0)*100)}%<br>
                            Your answer may contain copied content or suspicious patterns.
                        </div>
                    """, unsafe_allow_html=True)
                
                if eval_data.get("is_time_anomaly_suspicious"):
                    st.markdown(f"""
                        <div class='integrity-warning'>
                            <strong>⏱️ Unusual Response Time</strong><br>
                            This response time is suspicious for this question type.
                        </div>
                    """, unsafe_allow_html=True)
                
                st.info(f"📝 {result['explanation']}")
                
                if result["termination_reason"]:
                    st.error(f"🛑 Interview Terminated: {result['termination_reason']}")
                    st.session_state.coordinator.finish_interview()
                elif st.session_state.coordinator.state.status == "finished":
                    st.success("✅ Interview Complete!")
                    st.session_state.coordinator.finish_interview()
                else:
                    st.session_state.last_question = st.session_state.coordinator.next_question()
                    st.session_state.question_start = time.time()
                    st.rerun()
        
        with col2:
            st.write("")
            st.write("")
            if st.button("⏹️ End Interview Early", key="end_interview_early"):
                st.session_state.coordinator.state.status = "finished"
                st.session_state.coordinator.finish_interview()
                st.rerun()
        
        # Show timeline so far
        if st.session_state.coordinator.state.question_history:
            with st.expander("📋 Interview Timeline (Expand to view)", expanded=False):
                df = pd.DataFrame([vars(x) for x in st.session_state.coordinator.state.question_history])
                df_display = df[["question_id", "category", "difficulty", "score", "time_taken", "accuracy", "clarity", "depth", "relevance"]]
                df_display.columns = ["Q#", "Category", "Difficulty", "Score", "Time", "Accuracy", "Clarity", "Depth", "Relevance"]
                st.dataframe(df_display, use_container_width=True)


def show_report():
    st.subheader("📊 Step 4: Interview DNA Report")
    
    if not st.session_state.coordinator.state.dna_profile:
        st.info("📋 Complete the interview to view the detailed DNA report.")
        return

    profile = st.session_state.coordinator.state.dna_profile
    
    # Display Resume Accuracy if available
    if st.session_state.get("resume_accuracy"):
        acc = st.session_state.resume_accuracy
        st.markdown("---")
        st.subheader("📄 Resume Quality Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Resume Accuracy", f"{acc['overall_accuracy']:.0f}%")
        col2.metric("Quality Level", acc['quality_level'])
        col3.metric("Email Present", "✅" if acc['has_email'] else "❌")
        col4.metric("Phone Present", "✅" if acc['has_phone'] else "❌")
        st.markdown("---")
    
    # Main metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("🧬 Final Readiness", f"{profile['final_readiness']:.1f}%")
    col2.metric("🎯 Recommendation", profile["recommendation"])
    col3.metric("🔒 Integrity Score", f"{profile.get('integrity_score', 100):.1f}%")
    
    # Cheating indicators
    if profile.get("plagiarism_flags", 0) > 0 or profile.get("time_anomaly_flags", 0) > 0:
        st.markdown(f"""
            <div class='integrity-warning'>
                <strong>⚠️ Interview Integrity Issues Detected</strong><br>
                Plagiarism Flags: {profile.get('plagiarism_flags', 0)} | Time Anomalies: {profile.get('time_anomaly_flags', 0)}
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class='integrity-success'>
                <strong>✓ High Interview Integrity</strong><br>
                No suspicious patterns or anomalies detected.
            </div>
        """, unsafe_allow_html=True)
    
    # DNA Indices
    st.markdown("### 🧬 Interview DNA Indices")
    col1, col2, col3 = st.columns(3)
    col1.metric("🧠 Knowledge", profile["knowledge_index"])
    col2.metric("💬 Communication", profile["communication_index"])
    col3.metric("🔄 Adaptability", profile["adaptability_index"])
    col4, col5, col6 = st.columns(3)
    col4.metric("💪 Confidence", profile["confidence_index"])
    col5.metric("📊 Consistency", profile["consistency_index"])
    col6.metric("🔥 Pressure Handling", profile["pressure_handling_index"])
    
    # Radar chart
    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(
        r=[profile["knowledge_index"], profile["communication_index"], profile["adaptability_index"], 
           profile["confidence_index"], profile["consistency_index"], profile["pressure_handling_index"], 
           profile["knowledge_index"]],
        theta=["Knowledge", "Communication", "Adaptability", "Confidence", "Consistency", "Pressure", "Knowledge"],
        fill='toself', name='DNA Profile', 
        line=dict(color='#06b6d4', width=2), fillcolor='rgba(6, 182, 212, 0.2)'
    ))
    radar.update_layout(
        polar=dict(
            bgcolor='rgba(15, 23, 42, 0.5)', 
            radialaxis=dict(range=[0, 100], visible=True, gridcolor='rgba(255,255,255,0.06)', linecolor='rgba(255,255,255,0.1)', tickfont=dict(color='#94a3b8')),
            angularaxis=dict(gridcolor='rgba(255,255,255,0.06)', linecolor='rgba(255,255,255,0.1)', tickfont=dict(color='#e2e8f0'))
        ), 
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0',
        height=500, margin=dict(t=40, b=40, l=40, r=40)
    )
    st.plotly_chart(radar, use_container_width=True)
    
    # Score timeline
    history = [vars(x) for x in st.session_state.coordinator.state.question_history]
    if history:
        timeline = [f"Q{entry['question_id']}" for entry in history]
        scores = [entry["score"] for entry in history]
        
        score_chart = go.Figure()
        score_chart.add_trace(go.Scatter(x=timeline, y=scores, mode='lines+markers', 
                                        name='Score', line=dict(color='#7c3aed', width=3),
                                        marker=dict(size=10, color='#06b6d4', line=dict(color='#7c3aed', width=2))))
        score_chart.update_layout(title='📈 Score Progression Timeline', 
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15, 23, 42, 0.4)', 
                                 font_color='#e2e8f0', height=400,
                                 xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                                 yaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.05)'))
        st.plotly_chart(score_chart, use_container_width=True)
    
    # Strengths & Weaknesses
    col1, col2 = st.columns(2)
    with col1:
        st.write("### ✅ Strengths")
        for strength in profile.get("strengths", []):
            st.write(f"• {strength}")
    
    with col2:
        st.write("### ⚠️ Weaknesses")
        for weakness in profile.get("weaknesses", []):
            st.write(f"• {weakness}")
    
    st.write("### 🎯 Improvement Areas")
    for area in profile.get("improvement_areas", []):
        st.write(f"• {area}")
    
    # Export and Print
    st.markdown("---")
    st.subheader("📥 Report Export & Print")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Export JSON Report", key="export_report"):
            candidate_name = st.session_state.candidate_name or "Unknown"
            resume_accuracy = st.session_state.get("resume_accuracy", {})
            save_path = save_json_report({
                "candidate_name": candidate_name,
                "timestamp": datetime.utcnow().isoformat(),
                "resume_profile": st.session_state.coordinator.resume_profile,
                "resume_accuracy": {
                    "overall_accuracy": resume_accuracy.get("overall_accuracy", 0),
                    "quality_level": resume_accuracy.get("quality_level", "Unknown"),
                    "section_scores": resume_accuracy.get("section_scores", {}),
                },
                "job_profile": st.session_state.coordinator.job_profile,
                "question_history": history,
                "dna_profile": profile,
            }, candidate_name=candidate_name)
            st.success(f"✅ Report saved to `{save_path}`")
    
    with col2:
        if st.button("🖨️ Print Report", key="print_report"):
            st.write("""
            <script>
            window.print();
            </script>
            """, unsafe_allow_html=True)
            st.info("🖨️ Click 'Print' in your browser to save/print the report")
    
    with col3:
        st.info("📊 All data stored in `storage/{candidate_name}/`")


def show_about():
    st.subheader("ℹ️ About InterviewDNA AI")
    st.write(
        "**InterviewDNA AI** is a production-ready mock interview platform combining resume-driven assessment, "
        "adaptive questioning, AI-powered evaluation, integrity monitoring, and comprehensive visual analytics."
    )
    st.write("**Key Innovations:**")
    st.write("- 🔐 **Integrity Detection:** Plagiarism, time anomalies, fake resume/JD detection")
    st.write("- 📊 **Interview DNA:** Dynamic index calculation across 6 dimensions")
    st.write("- 🎯 **Adaptive AI:** Difficulty adjusts based on real-time performance")
    st.write("- 🔥 **Pressure Mode:** Stress-test resilience under timed scenarios")
    st.write("- 📈 **Explainable Scoring:** Transparent reasoning for every evaluation")
    st.write("- 🧬 **Behavioral Analysis:** Tracks consistency, adaptability, and decision-making")


def main():
    render_header()
    sidebar_controls()
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Resume", "Job Description", "Interview", "Report", "About"])
    
    with tab1:
        show_resume_analyzer()
    with tab2:
        show_jd_analyzer()
    with tab3:
        show_interview_lab()
    with tab4:
        show_report()
    with tab5:
        show_about()
    
    st.markdown("---")
    st.markdown(f"**📚 Question Library:** {len(INTERVIEW_QUESTIONS)} comprehensive interview patterns | **🟢 Ready for Production**")


if __name__ == "__main__":
    main()
