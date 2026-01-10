"""
Service Center Assignment Service

Uses pre-computed top-k service center index for O(1) customer assignment.
Based on haversine distance calculations.
"""
import os
import math
import pickle
import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configuration
K = 5  # Top K service centers per customer
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CUSTOMER_FILE = DATA_DIR / "customers.csv"
SERVICE_FILE = DATA_DIR / "service_centres.csv"
INDEX_FILE = DATA_DIR / "customer_topk_index.pkl"


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees).
    Returns distance in kilometers.
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_customer_topk_index() -> Dict[str, List[str]]:
    """
    Build top-K service center index for all customers.
    This should be run once when data changes.
    """
    customers = pd.read_csv(CUSTOMER_FILE)
    services = pd.read_csv(SERVICE_FILE)

    customer_topk = {}

    for _, cust in customers.iterrows():
        distances = []

        for _, sc in services.iterrows():
            dist = haversine(
                cust["latitude"], cust["longitude"],
                sc["latitude"], sc["longitude"]
            )
            distances.append((sc["scid"], dist))

        # Sort by distance and take top K
        distances.sort(key=lambda x: x[1])
        top_k_scids = [scid for scid, _ in distances[:K]]

        customer_topk[cust["cid"]] = top_k_scids

    # Persist index to disk
    with open(INDEX_FILE, "wb") as f:
        pickle.dump(customer_topk, f)

    print("✅ Customer Top-K index built and saved")
    return customer_topk


def load_topk_index() -> Dict[str, List[str]]:
    """Load pre-computed top-k index from disk."""
    if not INDEX_FILE.exists():
        return build_customer_topk_index()
    
    with open(INDEX_FILE, "rb") as f:
        return pickle.load(f)


def load_service_centers_df() -> pd.DataFrame:
    """Load service centers data from CSV."""
    return pd.read_csv(SERVICE_FILE)


class AssignmentService:
    """Service for assigning customers to service centers."""
    
    def __init__(self):
        self._topk_index: Optional[Dict[str, List[str]]] = None
        self._service_df: Optional[pd.DataFrame] = None
    
    @property
    def topk_index(self) -> Dict[str, List[str]]:
        """Lazy load the top-k index."""
        if self._topk_index is None:
            self._topk_index = load_topk_index()
        return self._topk_index
    
    @property
    def service_df(self) -> pd.DataFrame:
        """Lazy load the service centers dataframe."""
        if self._service_df is None:
            self._service_df = load_service_centers_df()
        return self._service_df
    
    def reload_data(self):
        """Reload data from disk (useful after data updates)."""
        self._topk_index = load_topk_index()
        self._service_df = load_service_centers_df()
    
    def assign_service_center(self, customer_id: str) -> Dict[str, Any]:
        """
        Assign the best available service center for a customer.
        Uses pre-computed top-k index for O(1) lookup.
        """
        if customer_id not in self.topk_index:
            return {
                "status": "error",
                "message": f"Customer ID {customer_id} not found in index"
            }

        top_centres = self.topk_index[customer_id]

        for scid in top_centres:
            row = self.service_df.loc[self.service_df["scid"] == scid]
            if row.empty:
                continue
            row = row.iloc[0]
            if row["technician_available"] == "yes":
                return {
                    "status": "assigned",
                    "customer_id": customer_id,
                    "service_center_id": scid,
                    "service_center_name": row["name"],
                    "location": row["location_human"]
                }

        return {
            "status": "delayed",
            "customer_id": customer_id,
            "message": "All nearby service centres busy. Assignment in 24 hours."
        }
    
    def get_top_k_centers(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get the top-k service centers for a customer with details."""
        if customer_id not in self.topk_index:
            return []
        
        centers = []
        for scid in self.topk_index[customer_id]:
            row = self.service_df.loc[self.service_df["scid"] == scid]
            if not row.empty:
                row = row.iloc[0]
                centers.append({
                    "scid": scid,
                    "name": row["name"],
                    "location": row["location_human"],
                    "available": row["technician_available"] == "yes"
                })
        return centers


# Singleton instance
assignment_service = AssignmentService()

