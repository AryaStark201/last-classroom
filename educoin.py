# app.py
import hashlib
import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict

import streamlit as st
import pandas as pd

# =========================
# 🔹 Blockchain Backend Code
# =========================

# ---------- Transaction and Block ----------
@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: int
    note: str = ""

    def to_dict(self):
        return asdict(self)


class Block:
    def __init__(self, index: int, transactions: List[Transaction],
                 previous_hash: str, nonce: int = 0, timestamp: float = None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = timestamp or time.time()
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        tx_str = json.dumps([t.to_dict() for t in self.transactions], sort_keys=True)
        block_str = f"{self.index}{tx_str}{self.previous_hash}{self.nonce}{self.timestamp}".encode()
        return hashlib.sha256(block_str).hexdigest()


# ---------- Blockchain ----------
class SimpleBlockchain:
    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(index=0, transactions=[], previous_hash="0")
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block: Block) -> Block:
        target = "0" * self.difficulty
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

    def add_block(self, transactions: List[Transaction]) -> Block:
        new_block = Block(len(self.chain), transactions, self.last_block.hash)
        mined = self.proof_of_work(new_block)
        self.chain.append(mined)
        return mined

    def get_balance(self, address: str) -> int:
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance

    def all_balances(self) -> Dict[str, int]:
        balances: Dict[str, int] = {}
        for block in self.chain:
            for tx in block.transactions:
                balances[tx.sender] = balances.get(tx.sender, 0) - tx.amount
                balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
        return balances

    def print_ledger(self):
        for block in self.chain:
            print(f"Block #{block.index} | prev={block.previous_hash[:8]}... | hash={block.hash[:8]}... | nonce={block.nonce}")
            for tx in block.transactions:
                sender = tx.sender if isinstance(tx, Transaction) else tx["sender"]
                recipient = tx.recipient if isinstance(tx, Transaction) else tx["recipient"]
                amount = tx.amount if isinstance(tx, Transaction) else tx["amount"]
                note = tx.note if isinstance(tx, Transaction) else tx.get("note", "")
                print(f"   {sender} -> {recipient} : {amount} ({note})")
            print()


# ---------- Classroom Coin ----------
TEACHER = "TEACHER"

class ClassroomCoin:
    def __init__(self, students: List[str], difficulty: int = 2):
        self.blockchain = SimpleBlockchain(difficulty)
        self.students = set(students)

    def award_coin(self, student: str, reason="Correct Answer"):
        if student not in self.students:
            raise ValueError(f"{student} is not a registered student.")
        tx = Transaction(sender=TEACHER, recipient=student, amount=1, note=reason)
        block = self.blockchain.add_block([tx])
        return block

    def transfer(self, sender: str, recipient: str, amount=1, note=""):
        if sender not in self.students or recipient not in self.students:
            raise ValueError("Both sender and recipient must be registered students.")
        if self.blockchain.get_balance(sender) < amount:
            raise ValueError(f"{sender} does not have enough balance.")
        tx = Transaction(sender=sender, recipient=recipient, amount=amount, note=note)
        block = self.blockchain.add_block([tx])
        return block

    def balance(self, student: str) -> int:
        return self.blockchain.get_balance(student)

    def leaderboard(self) -> Dict[str, int]:
        return dict(sorted(self.blockchain.all_balances().items(), key=lambda x: x[1], reverse=True))


# =========================
# 🎨 Streamlit Frontend Code
# =========================

st.set_page_config(page_title="Classroom Coin", layout="wide")
st.title("🎓 ClassroomCoin — Blockchain Rewards System")

# Initialize session state
if "classroom" not in st.session_state:
    st.session_state.classroom = ClassroomCoin(["Alice", "Bob", "Charlie"], difficulty=2)

classroom = st.session_state.classroom

# Sidebar: Add new student
st.sidebar.header("Manage Students")
new_student = st.sidebar.text_input("Add new student")
if st.sidebar.button("Add Student"):
    classroom.students.add(new_student)
    st.sidebar.success(f"Added {new_student}")

# Award coin
st.subheader("🏅 Award Coin (Teacher ➡ Student)")
award_student = st.selectbox("Select student", sorted(classroom.students))
reason = st.text_input("Reason", value="Good Performance")
if st.button("Award 1 Coin"):
    classroom.award_coin(award_student, reason)
    st.success(f"Awarded 1 coin to {award_student} for: {reason}")

# Transfer coins
st.subheader("💰 Transfer Coins (Student ➡ Student)")
col1, col2 = st.columns(2)
sender = col1.selectbox("Sender", sorted(classroom.students))
recipient = col2.selectbox("Recipient", sorted(classroom.students))
amount = st.number_input("Amount", min_value=1, step=1)
note = st.text_input("Note", value="")
if st.button("Transfer Coins"):
    try:
        classroom.transfer(sender, recipient, amount, note)
        st.success(f"{sender} ➡ {recipient}: {amount} coins")
    except ValueError as e:
        st.error(str(e))

# Show balances
st.subheader("📊 Current Balances")
balances = classroom.blockchain.all_balances()
df_balances = pd.DataFrame(balances.items(), columns=["Student", "Balance"])
st.dataframe(df_balances, use_container_width=True)

# Show blockchain ledger
st.subheader("⛓ Blockchain Ledger")
ledger_data = []
for block in classroom.blockchain.chain:
    for tx in block.transactions:
        ledger_data.append({
            "Block #": block.index,
            "Sender": tx.sender,
            "Recipient": tx.recipient,
            "Amount": tx.amount,
            "Note": tx.note,
            "Hash": block.hash[:10] + "..."
        })

df_ledger = pd.DataFrame(ledger_data)
st.dataframe(df_ledger, use_container_width=True)

# Leaderboard
st.subheader("🏆 Leaderboard")
sorted_balances = classroom.leaderboard()
df_leaderboard = pd.DataFrame(sorted_balances.items(), columns=["Student", "Coins"])
st.table(df_leaderboard)
