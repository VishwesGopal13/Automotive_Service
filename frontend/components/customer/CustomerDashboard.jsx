"use client";

import { useEffect, useState, useCallback } from "react";
import Header from "@/components/shared/Header";
import IssueForm from "./IssueForm";
import JobCardView from "@/components/shared/JobCardView";
import { api } from "@/services/api";

export default function CustomerDashboard({ user, onLogout }) {
  const [jobCards, setJobCards] = useState([]);
  const [notification, setNotification] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Function to transform backend job card to frontend format
  const transformJobCard = (jc) => ({
    id: jc.id,
    customerIssue: jc.complaint_text,
    status: jc.status?.toLowerCase() || "pending",
    timestamp: new Date(jc.created_at).toLocaleString(),
    severity: jc.ai_analysis?.severity_category,
    serviceType: jc.ai_analysis?.predicted_repair_type,
    prescribedActions: jc.ai_analysis?.recommended_actions || [],
    serviceCenter: jc.service_center?.name || jc.service_center_id,
    serviceCenterId: jc.service_center_id,
    technician: jc.technician?.name,
    estimatedTime: jc.ai_analysis?.estimated_labor_time,
    estimatedCost: jc.ai_analysis?.estimated_cost_range,
    validationStatus: jc.validation_report?.overall_status,
    invoice: jc.invoice,
  });

  // Poll for updates
  useEffect(() => {
    const interval = setInterval(async () => {
      if (jobCards.length === 0) return;

      try {
        const updatedCards = await Promise.all(
          jobCards.map(async (jc) => {
            try {
              const updated = await api.getJobCard(jc.id);
              return transformJobCard(updated);
            } catch {
              return jc;
            }
          })
        );

        // Check for completed jobs
        updatedCards.forEach((newJc) => {
          const oldJc = jobCards.find(j => j.id === newJc.id);
          if (oldJc && oldJc.status !== "completed" && newJc.status === "completed") {
            setNotification(`Your issue for Job ID ${newJc.id} has been resolved!`);
          }
        });

        setJobCards(updatedCards);
      } catch (err) {
        console.error("Error polling job cards:", err);
      }
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(interval);
  }, [jobCards]);

  const refreshJobCards = useCallback(async () => {
    if (jobCards.length === 0) return;
    setRefreshing(true);
    try {
      const updatedCards = await Promise.all(
        jobCards.map(async (jc) => {
          try {
            const updated = await api.getJobCard(jc.id);
            return transformJobCard(updated);
          } catch {
            return jc;
          }
        })
      );
      setJobCards(updatedCards);
    } catch (err) {
      console.error("Error refreshing:", err);
    } finally {
      setRefreshing(false);
    }
  }, [jobCards]);

  const handleJobCardCreated = (jc) => {
    setJobCards([jc, ...jobCards]);
    setNotification(`Job card ${jc.id} created successfully!`);
    setTimeout(() => setNotification(null), 5000);
  };

  const pendingCards = jobCards.filter(jc =>
    !["completed", "invoiced", "closed"].includes(jc.status)
  );
  const completedCards = jobCards.filter(jc =>
    ["completed", "invoiced", "closed"].includes(jc.status)
  );

  return (
    <>
      <Header user={user} onLogout={onLogout} />

      <div className="max-w-5xl mx-auto p-6 space-y-6">
        <IssueForm user={user} onJobCardCreated={handleJobCardCreated} />

        {notification && (
          <div className="bg-green-100 border border-green-300 text-green-800 p-4 rounded flex justify-between items-center">
            <span>✅ {notification}</span>
            <button
              onClick={() => setNotification(null)}
              className="text-green-600 hover:text-green-800"
            >
              ✕
            </button>
          </div>
        )}

        <div className="flex justify-between items-center">
          <h2 className="font-bold text-lg">Active Service Requests</h2>
          {jobCards.length > 0 && (
            <button
              onClick={refreshJobCards}
              disabled={refreshing}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
          )}
        </div>

        {pendingCards.length === 0 ? (
          <p className="text-gray-500 text-sm">No active service requests. Describe an issue above to get started.</p>
        ) : (
          pendingCards.map(jc => (
            <JobCardView key={jc.id} jobCard={jc} userRole="customer" />
          ))
        )}

        <h2 className="font-bold text-lg mt-8">Completed Services</h2>
        {completedCards.length === 0 ? (
          <p className="text-gray-500 text-sm">No completed services yet.</p>
        ) : (
          completedCards.map(jc => (
            <JobCardView key={jc.id} jobCard={jc} userRole="customer" />
          ))
        )}
      </div>
    </>
  );
}
