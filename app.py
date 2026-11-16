"""
OmniSupport AI - Streamlit Chat Application
============================================
ChatGPT-style interface with follow-up support.
"""

import warnings
warnings.filterwarnings('ignore', message='.*torchvision.*')

import streamlit as st
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from config.settings import APP_TITLE, APP_ICON, PAGE_CONFIG
from src.ingestion.pipeline import get_pipeline
from src.guardrails import get_guarded_orchestrator


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(**PAGE_CONFIG)

# ============================================================
# CSS - Chat style like Claude/ChatGPT
# ============================================================
st.markdown("""
<style>
    /* Remove top padding, maximize chat area */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0 !important;
        max-width: 900px;
    }

    /* Header compact */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .app-header h1 {
        font-size: 1.5rem;
        margin: 0;
    }

    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .status-ready { background-color: #d4edda; color: #155724; }
    .status-empty { background-color: #fff3cd; color: #856404; }

    /* Chat container - scrollable */
    .chat-container {
        height: calc(100vh - 250px);
        overflow-y: auto;
        padding: 1rem 0;
    }

    /* Sidebar minimal */
    section[data-testid="stSidebar"] {
        width: 280px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 1rem;
    }

    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Context banner */
    .context-banner {
        background: linear-gradient(90deg, #e3f2fd 0%, #f5f5f5 100%);
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .context-banner code {
        background: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.8rem;
    }

    /* Clear button styling */
    button[kind="secondary"] {
        border: 1px solid #d0d0d0 !important;
        background: white !important;
    }
    button[kind="secondary"]:hover {
        background: #f5f5f5 !important;
        border-color: #999 !important;
    }
        background: white;
        padding: 2px 6px;
        border-radius: 4px;
    }

    /* Welcome box */
    .welcome-box {
        text-align: center;
        padding: 3rem 2rem;
        color: #666;
    }
    .welcome-box h2 {
        color: #333;
        margin-bottom: 1rem;
    }
    .example-queries {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: center;
        margin-top: 1.5rem;
    }
    .example-query {
        background: #f0f0f0;
        padding: 8px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: background 0.2s;
    }
    .example-query:hover {
        background: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================
def init_session_state():
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = get_pipeline()
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = get_guarded_orchestrator()  # Now with guardrails!
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_context" not in st.session_state:
        st.session_state.conversation_context = None
    if "last_result" not in st.session_state:
        st.session_state.last_result = None

init_session_state()


# ============================================================
# HELPERS
# ============================================================
def get_system_status():
    pipeline = st.session_state.pipeline
    try:
        policy_count = pipeline.vector_store.collection.count() if pipeline.vector_store else 0
    except:
        policy_count = 0
    order_count = len(pipeline.orders_df) if pipeline.orders_df is not None else 0
    return policy_count, order_count

def reset_conversation():
    st.session_state.messages = []
    st.session_state.conversation_context = None
    st.session_state.last_result = None


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(f"## {APP_ICON} {APP_TITLE}")

    policy_count, order_count = get_system_status()
    is_ready = policy_count > 0 and order_count > 0

    if is_ready:
        st.markdown('<span class="status-badge status-ready">✅ Ready</span>', unsafe_allow_html=True)
        st.caption(f"{policy_count} policies • {order_count} orders")
    else:
        st.markdown('<span class="status-badge status-empty">⚠️ Setup needed</span>', unsafe_allow_html=True)
        st.caption("👇 Admin: Upload sample data below")

    st.markdown("---")

    # Conversation info
    if st.session_state.conversation_context:
        ctx = st.session_state.conversation_context
        st.markdown("**Current Conversation**")
        st.caption(f"📦 {ctx.order_id or 'No order'}")
        st.caption(f"👤 {ctx.customer_name or 'Unknown'}")
        st.caption(f"⭐ {ctx.customer_tier or 'Standard'} tier")
        st.caption(f"💬 {len(st.session_state.messages)} messages")

    st.markdown("---")

    # Admin section - Upload with clear feedback
    with st.expander("⚙️ Admin - Upload Documents", expanded=True):
        st.caption("📄 TXT/PDF → Policies | 📊 CSV/XLSX → Orders")
        st.info("💡 **Tip:** You can select multiple files at once (Ctrl/Cmd + Click)")

        # Show success message from previous upload
        if "upload_result" in st.session_state:
            if st.session_state.upload_result["success"]:
                st.success(st.session_state.upload_result["message"])
            else:
                st.error(st.session_state.upload_result["message"])
            del st.session_state.upload_result

        uploaded_files = st.file_uploader(
            "Select multiple files to upload",
            type=['txt', 'pdf', 'csv', 'xlsx'],
            accept_multiple_files=True,
            label_visibility="visible",
            key="file_uploader"
        )

        if uploaded_files:
            st.write(f"**{len(uploaded_files)} file(s) ready:**")
            for f in uploaded_files:
                icon = "📄" if f.name.endswith(('.txt', '.pdf')) else "📊"
                st.write(f"{icon} {f.name} ({f.size // 1024} KB)")

            if st.button("⬆️ Upload & Process", type="primary", use_container_width=True, key="upload_btn"):
                results = []
                total_chunks = 0
                success_count = 0
                error_count = 0

                for file in uploaded_files:
                    try:
                        from src.utils.helpers import is_policy_file, is_order_file

                        # Determine file type
                        if is_policy_file(file.name):
                            save_path = st.session_state.pipeline.uploads_dir / "policies" / file.name
                            ftype = "policy"
                        elif is_order_file(file.name):
                            save_path = st.session_state.pipeline.uploads_dir / "orders" / file.name
                            ftype = "order"
                        else:
                            results.append(f"⚠️ {file.name}: Unsupported file type")
                            error_count += 1
                            continue

                        # Save file
                        save_path.parent.mkdir(parents=True, exist_ok=True)
                        save_path.write_bytes(file.getbuffer())

                        # Process using file path method
                        result = st.session_state.pipeline.process_file_path(str(save_path))

                        if result.status == "success":
                            chunks = result.details.get('chunks_created', 0) if result.details else 0
                            total_chunks += chunks
                            success_count += 1
                            results.append(f"✅ {file.name}: {chunks} chunks")
                        else:
                            error_count += 1
                            error_msg = result.message if result.message else "Processing failed"
                            results.append(f"❌ {file.name}: {error_msg}")

                    except Exception as e:
                        error_count += 1
                        results.append(f"❌ {file.name}: {str(e)}")

                # Get new counts
                new_policies, new_orders = get_system_status()

                # Store result for display after rerun
                if error_count == 0:
                    status_icon = "✅"
                    status_msg = "All files uploaded successfully!"
                elif success_count > 0:
                    status_icon = "⚠️"
                    status_msg = f"Partial success: {success_count} succeeded, {error_count} failed"
                else:
                    status_icon = "❌"
                    status_msg = "Upload failed"

                st.session_state.upload_result = {
                    "success": success_count > 0,
                    "message": f"{status_icon} **{status_msg}**\n\n" +
                               f"📊 **Created {total_chunks} chunks** | {new_policies} policies | {new_orders} orders\n\n" +
                               "**File Details:**\n" + "\n".join(results)
                }

                st.rerun()

    # Clear Chat Button (always visible, below Admin section)
    st.markdown("---")
    if st.button("🔄 Clear Chat", use_container_width=True, type="secondary"):
        reset_conversation()
        st.rerun()

    # Last result details
    if st.session_state.last_result:
        with st.expander("📊 Last Request"):
            r = st.session_state.last_result
            st.caption(f"Type: {'Follow-up' if r.is_followup else 'New'}")
            st.caption(f"Time: {r.metadata.get('duration_seconds', 0):.1f}s")
            if r.resolution_type:
                st.caption(f"Resolution: {r.resolution_type}")


# ============================================================
# MAIN CHAT AREA
# ============================================================

# Check if ready
if not is_ready:
    st.markdown("""
    <div class="welcome-box">
        <h2>👋 Welcome to OmniSupport AI</h2>
        <p>Admin: Upload sample data files using the <strong>"Admin - Upload Documents"</strong> section in the sidebar.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Context banner if in conversation
if st.session_state.conversation_context:
    ctx = st.session_state.conversation_context
    st.markdown(f"""
    <div class="context-banner">
        💬 <strong>Conversation:</strong>
        Order <code>{ctx.order_id or 'N/A'}</code> •
        {ctx.customer_name or 'Customer'} ({ctx.customer_tier or 'Standard'})
        • <em>Ask follow-up questions</em>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("resolution_type"):
            st.caption(f"📌 {msg['resolution_type']}")

# Welcome message if no chat yet
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-box">
        <h2>How can I help you today?</h2>
        <p>Describe your issue below. I can help with orders, returns, refunds, and more.</p>
        <div class="example-queries">
            <span class="example-query">My order ORD-003 arrived damaged</span>
            <span class="example-query">I want to return order ORD-010</span>
            <span class="example-query">What's your refund policy?</span>
            <span class="example-query">Order ORD-040 hasn't arrived</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# CHAT INPUT (Always at bottom - Streamlit default)
# ============================================================
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Process
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Extract order ID if first message
            order_id = None
            if not st.session_state.conversation_context:
                import re
                match = re.search(r'ORD[-_]?\d{3,}', prompt.upper())
                if match:
                    order_id = match.group().replace('_', '-')

            result = st.session_state.orchestrator.process_complaint(
                complaint=prompt,
                order_id=order_id,
                context=st.session_state.conversation_context,
                verbose=False
            )

            st.session_state.last_result = result

            if result.success:
                st.markdown(result.final_response)

                if not result.is_followup and result.resolution_type:
                    st.caption(f"📌 {result.resolution_type}")

                if result.context:
                    st.session_state.conversation_context = result.context

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.final_response,
                    "resolution_type": result.resolution_type if not result.is_followup else None
                })
            else:
                error_msg = f"Sorry, something went wrong: {result.error}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })
