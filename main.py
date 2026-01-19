
# This is a retail store dashboard that simulates sales and inventory management.

# Instructions to run on Replit:
# 1. Via shell: "streamlit run main.py --server.headless true"
# 2. Via button: Clicking the "Run" button will launch Streamlit via subprocess.

# Github: https://github.com/DesignsbyBlanc/demo_retail_store_model

import sys
import subprocess
import os
import streamlit as st
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timedelta
import uuid
import statistics
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import socket

st.set_page_config(page_title="Retail Live Dashboard", layout="wide")

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def launch_streamlit():
    """Prevent infinite loop of launching Streamlit on Replit"""
    if os.environ.get("STREAMLIT_RUNNING"):
        return
    if st.runtime.exists():
        
       # 1: Streamlit is already running.
       # 2: Port 8501 is in use. If both conditions true app likely run via 
       #  "streamlit run". I can add logic later to use another port.
       # 3: Streamlit is not running. Launch it.
       
        os.environ["STREAMLIT_RUNNING"] = "1"
        if is_port_in_use(8501):
            os.environ["STREAMLIT_RUNNING"] = "2"
        return
    else:
        os.environ["STREAMLIT_RUNNING"] = "3"
        print("Launching Streamlit app...")
        python_exe = sys.executable
        script_path = os.path.abspath(__file__)
        subprocess.run([
                python_exe, "-m", "streamlit", "run", script_path,
                "--server.headless", "true"
            ])
        sys.exit(0)

if __name__ == "__main__":
    launch_streamlit()


# ------------------------------------------
# 1. DATA MODELS
# ------------------------------------------


@dataclass
class ShelfTracking:
    date_received: datetime
    date_displayed: datetime


@dataclass
class Transaction:
    transaction_id: str
    storeitem_name: str
    location: str
    quantity_change: int
    timestamp: datetime
    transaction_type: str


@dataclass
class StoreItem:
    name: str
    upc: str
    quantity: int
    category: str
    location: str
    shelf_tracking: ShelfTracking
    transactions: List[Transaction] = field(default_factory=list)
    _sold_durations: List[int] = field(default_factory=list)

    def _record_transaction(self, qty_change: int, transaction_type: str):
        txn = Transaction(
            transaction_id=str(uuid.uuid4()),
            storeitem_name=self.name,
            location=self.location,
            quantity_change=qty_change,
            timestamp=datetime.now(),
            transaction_type=transaction_type,
        )
        self.transactions.append(txn)
        return txn

    def purchase(self, qty: int = 1):
        if qty > self.quantity:
            raise ValueError("Not enough inventory to purchase")

        sell_date = datetime.now()
        days_on_shelf = max(0, (sell_date -
                                self.shelf_tracking.date_displayed).days)

        for _ in range(qty):
            self._sold_durations.append(days_on_shelf)

        self.quantity -= qty
        st.toast(f"Sold {qty} of {self.name}", duration="long")
        print(f"Sold {qty} of {self.name}")
        return self._record_transaction(-qty, "purchase")

    def return_item(self, qty: int = 1):
        for _ in range(min(qty, len(self._sold_durations))):
            self._sold_durations.pop()
        self.quantity += qty
        st.toast(f"Returned {qty} of {self.name}", duration="long")
        print(f"Returned {qty} of {self.name}")
        return self._record_transaction(qty, "return")

    def replenish(self, qty: int = 1):
        self.quantity += qty
        st.toast(f"Replenished {qty} of {self.name}", duration="long")
        print(f"Replenished {qty} of {self.name}")
        return self._record_transaction(qty, "replenish")

    @property
    def average_days_to_sell(self):
        return statistics.mean(
            self._sold_durations) if self._sold_durations else 0


# ------------------------------------------
# 2. STORE GENERATION
# ------------------------------------------


def random_shelf_tracking():
    days_received = random.randint(8, 12)
    days_displayed = random.randint(1, days_received)
    return ShelfTracking(datetime.now() - timedelta(days=days_received),
                         datetime.now() - timedelta(days=days_displayed))


def generate_store():
    items_list = [
        StoreItem("Baby Yoda Keychain", "57023", 20, "Keychain",
                  "Front Counter", random_shelf_tracking()),
        StoreItem("iPhone 15 Case", "88002", 20, "Accessory", "End Cap A",
                  random_shelf_tracking()),
        StoreItem("Disney Princess Keychain", "99011", 20, "Keychain",
                  "Main Shelf", random_shelf_tracking()),
        StoreItem("Mandalorian Keychain", "57089", 20, "Keychain",
                  "Main Shelf", random_shelf_tracking()),
        StoreItem("LED Lanyard", "44022", 20, "Accessory", "Rotating Rack",
                  random_shelf_tracking())
    ]

    # simulate sales
    for item, rng in zip(items_list, [(10, 15), (6, 10), (5, 9), (4, 8),
                                      (1, 5)]):
        item.purchase(random.randint(*rng))

    return items_list


# ------------------------------------------
# 3. SESSION-STATE
# ------------------------------------------

if "store_items" not in st.session_state:
    st.session_state.store_items = generate_store()

items = st.session_state.store_items

# ------------------------------------------
# 4. SIDEBAR CONTROLS
# ------------------------------------------

st.sidebar.header("Inventory Actions")

item_names = [i.name for i in items]
selected_item_name = st.sidebar.selectbox("Select item", item_names)
selected_item = next(i for i in items if i.name == selected_item_name)

qty = st.sidebar.number_input("Quantity", 1, 20, 1)

c1, c2, c3 = st.sidebar.columns(3)

if c1.button("Sell"):
    try:
        selected_item.purchase(qty)
        items = st.session_state.store_items
        st.sidebar.success(f"Sold {qty}")
        print(f"{st.session_state.store_items}")
        time.sleep(0.25)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if c2.button("Restock"):
    try:
        selected_item.replenish(qty)
        items = st.session_state.store_items
        st.sidebar.success("Restocked")
        print(f"{st.session_state.store_items}")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if c3.button("Return"):
    try:
        selected_item.return_item(qty)
        items = st.session_state.store_items
        st.sidebar.success("Returned to inventory")
        print(f"{st.session_state.store_items}")
        time.sleep(0.25)
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if st.sidebar.button("Simulate Day Passing"):
    for item in items:
        item.shelf_tracking.date_displayed -= timedelta(days=1)
        print(f"New shelf date: {item.shelf_tracking.date_displayed} for {item.name}")
    items = st.session_state.store_items
    st.sidebar.info("Day passed")
    st.rerun()

if st.sidebar.button("Reset Store"):
    st.session_state.store_items = generate_store()
    st.rerun()

# ------------------------------------------
# 5. KPIs
# ------------------------------------------

st.title("Live Retail Store Dashboard")

total_units_sold = (sum(-t.quantity_change for item in items
                       for t in item.transactions
                       if t.transaction_type == "purchase") - sum(t.quantity_change for item in items
       for t in item.transactions
       if t.transaction_type == "return"))

avg_days = statistics.mean([i.average_days_to_sell for i in items])

best_location = max(set(i.location for i in items),
                    key=lambda loc: sum(-t.quantity_change for i in items
                                        if i.location == loc
                                        for t in i.transactions
                                        if t.transaction_type == "purchase"))

k1, k2, k3 = st.columns(3)
k1.metric("Units Sold", total_units_sold)
k2.metric("Avg Sell Time", f"{avg_days:.1f} days")
k3.metric("Top Location", best_location)

# ------------------------------------------
# 6. PIE CHART
# ------------------------------------------
st.subheader("Most Popular Items")

fig1, ax1 = plt.subplots()
sales = [
    (sum(-t.quantity_change for t in item.transactions
        if t.transaction_type == "purchase") - sum(t.quantity_change for t in item.transactions
        if t.transaction_type == "return")) for item in items
]
labels = [item.name for item in items]

ax1.pie(sales, labels=labels, autopct="%1.1f%%")
ax1.set_title("Most Popular Items")

st.pyplot(fig1)

# ------------------------------------------
# 7. HEAT MAPS
# ------------------------------------------

# Sales by location
location_sales = {}
for item in items:
    sold = (sum(-t.quantity_change for t in item.transactions
               if t.transaction_type == "purchase") - sum(t.quantity_change for t in item.transactions
                  if t.transaction_type == "return"))
    location_sales[item.location] = location_sales.get(item.location, 0) + sold

df_sales = pd.DataFrame.from_dict(location_sales,
                                  orient="index",
                                  columns=["Units Sold"])

st.subheader("Heat Map: Sales by Location")

fig2, ax2 = plt.subplots()
heat = ax2.imshow(df_sales, cmap="Blues", aspect="auto")
plt.colorbar(heat, ax=ax2)
ax2.set_xticks([0])
ax2.set_xticklabels(["Units Sold"])
ax2.set_yticks(range(len(df_sales.index)))
ax2.set_yticklabels(df_sales.index)

for (i, j), val in np.ndenumerate(df_sales.values):
    ax2.text(j, i, f"{int(val)}", ha="center", va="center", color="black")

st.pyplot(fig2)

# Average days-to-sell location heatmap
location_days = {}
for item in items:
    location_days.setdefault(item.location,
                             []).append(item.average_days_to_sell)

location_avg = {loc: sum(v) / len(v) for loc, v in location_days.items()}
df_avg = pd.DataFrame.from_dict(location_avg,
                                orient="index",
                                columns=["Avg Days"])

st.subheader("Heat Map: Avg Days to Sell")

fig3, ax3 = plt.subplots()
heat2 = ax3.imshow(df_avg, cmap="Oranges", aspect="auto")
plt.colorbar(heat2, ax=ax3)
ax3.set_xticks([0])
ax3.set_xticklabels(["Avg Days"])
ax3.set_yticks(range(len(df_avg.index)))
ax3.set_yticklabels(df_avg.index)

for (i, j), val in np.ndenumerate(df_avg.values):
    ax3.text(j, i, f"{val:.1f}", ha="center", va="center", color="black")

st.pyplot(fig3)
