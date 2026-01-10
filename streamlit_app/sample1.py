import pandas as pd
import numpy as np

# -----------------------------
# Haversine distance function
# -----------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(
        np.radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + \
        np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2

    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


# -----------------------------
# Load data
# -----------------------------
customers = pd.read_csv("/Users/vishwesg/Documents/VS_Code/Innovation Challenge Project Files/Data/customers.csv")
service_centres = pd.read_csv("/Users/vishwesg/Documents/VS_Code/Innovation Challenge Project Files/Data/service_centres.csv")


# -----------------------------
# Assign nearest service centre
# -----------------------------
assignments = []

for _, cust in customers.iterrows():
    distances = haversine(
        cust["latitude"],
        cust["longitude"],
        service_centres["latitude"],
        service_centres["longitude"]
    )

    nearest_idx = distances.idxmin()
    nearest_sc = service_centres.loc[nearest_idx]

    assignment_status = (
        "Immediate"
        if nearest_sc["technician_available"] == "yes"
        else "Within 24 hours"
    )

    assignments.append({
        "cid": cust["cid"],
        "customer_name": cust["name"],
        "assigned_scid": nearest_sc["scid"],
        "service_centre_name": nearest_sc["name"],
        "distance_km": round(distances[nearest_idx], 2),
        "technician_available": nearest_sc["technician_available"],
        "assignment_status": assignment_status
    })


# -----------------------------
# Final assignment table
# -----------------------------
assignment_df = pd.DataFrame(assignments)

# Save to CSV
output_path = "/Users/vishwesg/Documents/VS_Code/Innovation Challenge Project Files/Datacustomer_service_assignments.csv"
assignment_df.to_csv(output_path, index=False)

print("Assignment completed.")
print(f"Output saved to: {output_path}")