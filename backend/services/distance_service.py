"""
Distance Service for calculating haversine distances and finding optimal assignments.

Note: For O(1) service center assignment using pre-computed top-k index,
use the AssignmentService from services/assignment_service.py instead.
"""
import math
from typing import Dict, Any, Optional

from automotive_service.models.service_center import ServiceCenter, Technician


class DistanceService:
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        Returns distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers
        r = 6371

        return c * r

    @staticmethod
    def find_optimal_assignment(customer_lat: float, customer_lon: float,
                              specialization_required: str = None) -> Optional[Dict[str, Any]]:
        """
        Find the optimal service center and technician based on:
        1. Distance (Haversine)
        2. Technician availability (technician_available flag or actual technicians)
        3. Specialization match (if required)

        Note: For pre-computed O(1) lookups, use AssignmentService.assign_service_center()
        """
        service_centers = ServiceCenter.query.all()
        best_assignment = None
        min_distance = float('inf')

        for center in service_centers:
            # Skip if no technicians available at this center
            if not center.technician_available:
                continue

            distance = DistanceService.haversine_distance(
                customer_lat, customer_lon,
                center.latitude, center.longitude
            )

            # Find available technicians at this center (if any are defined)
            available_technicians = [
                tech for tech in center.technicians
                if tech.is_available()
            ]

            # If we have technicians defined, check availability
            # Otherwise, rely on technician_available flag
            if center.technicians and not available_technicians:
                continue

            # If specialization is required, filter technicians
            if specialization_required and available_technicians:
                specialized_techs = [
                    tech for tech in available_technicians
                    if specialization_required.lower() in (tech.specializations or '').lower()
                ]
                if specialized_techs:
                    available_technicians = specialized_techs

            if distance < min_distance:
                min_distance = distance

                # Select technician with lowest current workload (if any)
                best_technician = None
                if available_technicians:
                    best_technician = min(available_technicians, key=lambda t: t.current_workload)

                best_assignment = {
                    'service_center': center.to_dict(),
                    'service_center_id': center.id,
                    'technician': best_technician.to_dict() if best_technician else None,
                    'distance_km': round(distance, 2)
                }

        return best_assignment


# Singleton instance
distance_service = DistanceService()