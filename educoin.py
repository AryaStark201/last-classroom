# Save this as blockchain_certificates_app.py
import streamlit as st
import hashlib
import json
from time import time

# ---------------- Blockchain Class ---------------- #
class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_certificates = []
        # Create the genesis block
        self.create_block(previous_hash='0')

    def create_block(self, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'certificates': self.pending_certificates,
            'previous_hash': previous_hash,
        }
        block['hash'] = self.hash(block)
        self.pending_certificates = []
        self.chain.append(block)
        return block

    def add_certificate(self, student_name, course_name):
        self.pending_certificates.append({
            'student_name': student_name,
            'course_name': course_name
        })
        return True

    @staticmethod
    def hash(block):
        block_string = json.dumps({k: block[k] for k in block if k != 'hash'}, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def get_last_block(self):
        return self.chain[-1]

    def verify_certificate(self, student_name):
        results = []
        for block in self.chain:
            for cert in block['certificates']:
                if cert['student_name'].lower() == student_name.lower():
                    results.append({'block_index': block['index'], 'certificate': cert})
        return results

# ---------------- Streamlit UI ---------------- #
st.set_page_config(page_title="Blockchain Certificate App", layout="wide")
st.title("🎓 Blockchain Certificate Management System")

# Initialize blockchain
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()

menu = ["Add Certificate", "Mine Block", "Verify Certificate", "View Blockchain"]
choice = st.sidebar.selectbox("Menu", menu)

# 1. Add Certificate
if choice == "Add Certificate":
    st.subheader("Add New Student Certificate")
    student_name = st.text_input("Student Name")
    course_name = st.text_input("Course Name")
    if st.button("Add Certificate"):
        if student_name and course_name:
            st.session_state.blockchain.add_certificate(student_name, course_name)
            st.success(f"Certificate for {student_name} added successfully!")
        else:
            st.error("Please enter both student name and course name.")

# 2. Mine Block
elif choice == "Mine Block":
    st.subheader("Mine Pending Certificates into a Block")
    if st.button("Mine Block"):
        if st.session_state.blockchain.pending_certificates:
            previous_hash = st.session_state.blockchain.get_last_block()['hash']
            block = st.session_state.blockchain.create_block(previous_hash)
            st.success(f"Block #{block['index']} mined successfully!")
            st.json(block)
        else:
            st.warning("No pending certificates to mine.")

# 3. Verify Certificate
elif choice == "Verify Certificate":
    st.subheader("Verify a Student Certificate")
    search_name = st.text_input("Enter Student Name to Verify")
    if st.button("Verify"):
        if search_name:
            results = st.session_state.blockchain.verify_certificate(search_name)
            if results:
                st.success(f"Certificates found for {search_name}:")
                for res in results:
                    st.json(res)
            else:
                st.error("No certificates found for this student.")
        else:
            st.error("Please enter a student name.")

# 4. View Blockchain
elif choice == "View Blockchain":
    st.subheader("Blockchain Overview")
    for block in st.session_state.blockchain.chain:
        st.markdown(f"### Block #{block['index']}")
        st.write(f"Timestamp: {block['timestamp']}")
        st.write(f"Previous Hash: {block['previous_hash']}")
        st.write(f"Hash: {block['hash']}")
        st.write("Certificates:")
        st.json(block['certificates'])

