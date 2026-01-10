import streamlit as st
import pandas as pd
from guard import run_audit, exterior_scan, draw_manual_overlay
import os
import requests

# 1. SET PAGE CONFIG
st.set_page_config(page_title="Revenue Guard AI", page_icon="🛡️", layout="wide")

# 2. DEFINE RO NUMBER & FETCH JOB CARD FROM BACKEND
query_params = st.query_params
ro_num = query_params.get("ro", "RO-500")

# Backend API URL - configurable
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000/api")

# Fetch job card details from backend
@st.cache_data(ttl=60)
def fetch_job_card(job_card_id):
    """Fetch job card details from the Flask backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/job-card/{job_card_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.warning(f"Could not connect to backend: {e}")
        return None

job_card_data = fetch_job_card(ro_num)

INVENTORY = {
    "P101": {"name": "Oil Filter", "price": 85.00},
    "P102": {"name": "Brake Pads", "price": 120.00},
    "P103": {"name": "Plastic Clip", "price": 5.00},
    "P104": {"name": "Headlight Assembly", "price": 600.00},
    "P105": {"name": "Front Bumper", "price": 1200.00}
}

# 3. RECONCILIATION LOGIC
def check_billing_discrepancy(visual_finding, ro_id):
    try:
        invoice_df = pd.read_csv('final_invoice.csv')
        current_invoice = invoice_df[invoice_df['ro_id'].astype(str) == str(ro_id)]
        detected_part = visual_finding.split('|')[0].split('PART:')[-1].strip().lower()
        billed_items = " ".join(current_invoice['item_name'].astype(str).tolist()).lower()
        
        if detected_part not in billed_items:
            return f"🚨 Technician has not mentioned the {detected_part.upper()} in the final invoice. Please check again."
        return f"✅ Verified: {detected_part.upper()} is documented."
    except Exception as e:
        return f"Reconciliation Error: {e}"

# 4. INITIAL TECHNICIAN PORTAL
if 'billing_complete' not in st.session_state:
    st.session_state.billing_complete = False
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if not st.session_state.billing_complete:
    st.header(f"🔧 Technician Portal: Billing & Notes (RO: {ro_num})")

    # Display job card details if available from backend
    if job_card_data:
        with st.container(border=True):
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.markdown("### 📋 Job Card Details")
                st.markdown(f"**Job Card ID:** {job_card_data.get('id', ro_num)}")
                st.markdown(f"**Status:** {job_card_data.get('status', 'N/A')}")

                # Customer info
                customer = job_card_data.get('customer', {})
                if customer:
                    st.markdown(f"**Customer:** {customer.get('name', 'N/A')}")
                    vehicle = customer.get('vehicle', {})
                    if vehicle:
                        st.markdown(f"**Vehicle:** {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}")

            with col_info2:
                st.markdown("### 🔍 AI Diagnosis")
                st.markdown(f"**Issue:** {job_card_data.get('issue', 'N/A')}")

                # AI analysis
                ai_analysis = job_card_data.get('ai_analysis', {})
                if ai_analysis:
                    st.markdown(f"**Severity:** {ai_analysis.get('severity_category', 'N/A')}")
                    st.markdown(f"**Est. Time:** {ai_analysis.get('estimated_labor_time', 'N/A')}")
                    st.markdown(f"**Est. Cost:** {ai_analysis.get('estimated_cost_range', 'N/A')}")

            # Show customer complaint
            complaint = job_card_data.get('complaint_text', '')
            if complaint:
                st.markdown("### 💬 Customer Complaint")
                st.info(complaint)

            # Show recommended procedures
            procedures = job_card_data.get('ai_analysis', {}).get('recommended_actions', [])
            if procedures:
                st.markdown("### ✅ Recommended Procedures")
                for i, proc in enumerate(procedures, 1):
                    st.markdown(f"{i}. {proc}")

        st.divider()

    with st.form("billing_form"):
        selected_part_names = st.multiselect("Select Parts Used from Inventory", options=[v["name"] for v in INVENTORY.values()])
        input_note = st.text_area("Describe the work performed...", placeholder="e.g. Changed the oil and replaced bumper...")
        submit_btn = st.form_submit_button("Finish & Open Audit Dashboard")

        if submit_btn:
            invoice_data = []
            for name in selected_part_names:
                item_id = [k for k, v in INVENTORY.items() if v["name"] == name][0]
                price = INVENTORY[item_id]["price"]
                invoice_data.append({"ro_id": ro_num, "item_id": item_id, "item_name": name, "billed_price": price})
            pd.DataFrame(invoice_data).to_csv('final_invoice.csv', index=False)
            pd.DataFrame([{"ro_id": ro_num, "note_text": input_note}]).to_csv('mechanic_notes.csv', index=False)
            st.session_state.billing_complete = True
            st.rerun()
    st.stop()

# --- 5. AUDIT DASHBOARD ---
if 'errors' not in st.session_state: st.session_state.errors = None
if 'ai_diag' not in st.session_state: st.session_state.ai_diag = None
if 'visual_findings' not in st.session_state: st.session_state.visual_findings = None
if 'highlighted_img' not in st.session_state: st.session_state.highlighted_img = None

st.title("🛡️ AI Revenue Guard")
st.markdown(f"### Auditing Repair Order: **{ro_num}**")

# Show job card summary in sidebar
st.sidebar.header("📋 Job Card Info")
if job_card_data:
    customer = job_card_data.get('customer', {})
    vehicle = customer.get('vehicle', {})
    st.sidebar.markdown(f"**Customer:** {customer.get('name', 'N/A')}")
    if vehicle:
        st.sidebar.markdown(f"**Vehicle:** {vehicle.get('year', '')} {vehicle.get('make', '')} {vehicle.get('model', '')}")
    st.sidebar.markdown(f"**Issue:** {job_card_data.get('issue', 'N/A')[:50]}...")
    st.sidebar.divider()

st.sidebar.header("Evidence Upload")
before_img = st.sidebar.file_uploader("Before Photo", type=['jpg', 'png', 'jpeg'])
after_img = st.sidebar.file_uploader("After Photo", type=['jpg', 'png', 'jpeg'])
uploaded_audio = st.sidebar.file_uploader("Engine Sound", type=["mp3", "wav"])

col_pre1, col_pre2 = st.columns(2)
with col_pre1:
    if before_img: st.image(before_img, caption="Arrival", use_container_width=True)
with col_pre2:
    if after_img: st.image(after_img, caption="Departure", use_container_width=True)

st.divider()

btn1, btn2, btn3 = st.columns(3)
with btn1:
    if st.button("📄 Scan Invoice (Step 1)", use_container_width=True):
        errors, _ = run_audit(ro_num, audio_path=None)
        st.session_state.errors = errors
with btn3:
    if st.button("📸 Visual Audit (Step 2)", use_container_width=True):
        if before_img and after_img:
            b_path, af_path = "temp_before.jpg", "temp_after.jpg"
            with open(af_path, "wb") as f: f.write(after_img.getbuffer())
            findings, box = exterior_scan(b_path, af_path, after_img.name)
            st.session_state.visual_findings = findings
            if box: st.session_state.highlighted_img = draw_manual_overlay(af_path, box)
with btn2:
    if st.button("🔊 Engine Audio (Step 3)", use_container_width=True):
        if uploaded_audio:
            a_path = "temp_audio.mp3"
            with open(a_path, "wb") as f: f.write(uploaded_audio.getbuffer())
            _, diag = run_audit(ro_num, a_path)
            st.session_state.ai_diag = diag

st.divider()
left_report, right_details = st.columns([1, 1])

with left_report:
    st.subheader("📋 Final Audit & Revenue Report")
    if st.session_state.errors:
        st.write("**Digital Audit Results:**")
        for e in st.session_state.errors: st.error(e)
    if st.session_state.visual_findings:
        st.write("**Visual Audit Results:**")
        verdict = check_billing_discrepancy(st.session_state.visual_findings, ro_num)
        if "Technician" in verdict: st.error(verdict)
        else: st.success(verdict)

with right_details:
    with st.expander("🔍 Visual Evidence Detail", expanded=True):
        if st.session_state.highlighted_img:
            st.image(st.session_state.highlighted_img)
            st.info(st.session_state.visual_findings)
    with st.expander("🔊 Acoustic Diagnosis Detail", expanded=True):
        if st.session_state.ai_diag:
            raw_diag = st.session_state.ai_diag
            if "|" in raw_diag:
                diag_text = raw_diag.split("|")[0].replace("DIAGNOSIS:", "").strip()
                parts_text = raw_diag.split("|")[1].replace("PARTS:", "").strip()
                st.warning(f"**AI Sound Diagnosis:** {diag_text}")
                st.error(f"🛠️ **Responsible Parts:** {parts_text}")
            else: st.info(raw_diag)

# --- 6. FINAL SUBMISSION & BILLING ---
st.divider()

def submit_to_backend():
    """Submit the technician report to the Flask backend"""
    try:
        # Read the mechanic notes
        notes_text = ""
        if os.path.exists('mechanic_notes.csv'):
            notes_df = pd.read_csv('mechanic_notes.csv')
            notes_text = " ".join(notes_df['note_text'].astype(str).tolist())

        # Read the parts used
        parts_used = []
        if os.path.exists('final_invoice.csv'):
            invoice_df = pd.read_csv('final_invoice.csv')
            parts_used = invoice_df['item_name'].tolist()

        # Get procedures from job card if available
        procedures = []
        if job_card_data:
            procedures = job_card_data.get('ai_analysis', {}).get('recommended_actions', [])

        # Build the report payload
        report_data = {
            "procedures_performed": procedures if procedures else ["Work completed as described"],
            "tools_used": ["Standard tool set"],
            "labor_time": "2 hours",
            "parts_used": parts_used,
            "notes": notes_text,
            "audio_diagnosis": st.session_state.get('ai_diag', ''),
            "visual_findings": st.session_state.get('visual_findings', '')
        }

        # Submit to backend
        response = requests.post(
            f"{BACKEND_URL}/job-card/{ro_num}/technician-report",
            json=report_data,
            timeout=10
        )

        if response.status_code in [200, 201]:
            # Also trigger validation
            requests.post(f"{BACKEND_URL}/job-card/{ro_num}/validate", timeout=10)
            return True, "Report submitted successfully!"
        else:
            return False, f"Backend error: {response.text}"
    except Exception as e:
        return False, f"Could not submit to backend: {e}"

f1, f2 = st.columns(2)
with f1:
    if st.button("📤 Submit to Service Manager", type="primary", use_container_width=True):
        success, message = submit_to_backend()
        if success:
            st.session_state.submitted = True
            st.balloons()
            st.success(message)
        else:
            st.warning(message)
            st.session_state.submitted = True  # Still show invoice locally
with f2:
    if st.button("🗑️ Reset Application", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if st.session_state.submitted:
    st.divider()
    st.subheader("🧾 Final Customer Invoice")
    with st.container(border=True):
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown(f"**Shop:** Revenue Guard Garage")
            st.markdown(f"**RO ID:** {ro_num}")
        with b_col2:
            st.markdown(f"**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
            st.markdown(f"**Status:** PAID & VERIFIED")
        
        st.divider()
        if os.path.exists('final_invoice.csv'):
            invoice_df = pd.read_csv('final_invoice.csv')
            
            # --- LABOR LOGIC START ---
            labor_cost = 0.0
            if os.path.exists('mechanic_notes.csv'):
                notes_df = pd.read_csv('mechanic_notes.csv')
                # Check for "labor" keywords in the note
                full_note = " ".join(notes_df['note_text'].astype(str)).lower()
                keywords = ["labor", "worked", "replaced", "fixed", "installed", "removed"]
                
                if any(word in full_note for word in keywords):
                    labor_cost = 150.00 # Standard shop labor rate
            # --- LABOR LOGIC END ---

            st.table(invoice_df[['item_id', 'item_name', 'billed_price']].rename(columns={'item_id':'ID', 'item_name':'Part', 'billed_price':'Price ($)'}))
            
            if labor_cost > 0:
                st.write(f"🛠️ **Service Labor Charge Applied:** ${labor_cost:.2f}")
            
            total = invoice_df['billed_price'].sum() + labor_cost
            st.markdown(f"### Total Amount: ${total:.2f}")
            
            if st.button("📧 Send Invoice to Customer", use_container_width=True):
                st.balloons()
                st.snow() 
                st.success(f"Invoice for {ro_num} sent to customer's email!")