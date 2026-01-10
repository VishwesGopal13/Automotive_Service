"use client";

import { useEffect, useState, useCallback } from "react";
import Header from "@/components/shared/Header";
import JobCardView from "@/components/shared/JobCardView";
import TechnicianReportModal from "./TechnicianReportModal";
import { api } from "@/services/api";

export default function TechnicianDashboard({ user, onLogout }) {
  const [jobCards, setJobCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  const [reportModalJob, setReportModalJob] = useState(null);

  // Transform backend job card to frontend format
  const transformJobCard = (jc) => ({
    id: jc.id,
    customerIssue: jc.complaint_text,
    customerName: jc.customer?.name,
    customerId: jc.customer_id,
    status: jc.status?.toLowerCase() || "pending",
    timestamp: new Date(jc.created_at).toLocaleString(),
    severity: jc.ai_analysis?.severity_category,
    serviceType: jc.ai_analysis?.predicted_repair_type,
    prescribedActions: jc.ai_analysis?.recommended_actions || [],
    serviceCenter: jc.service_center?.name || jc.service_center_id,
    serviceCenterId: jc.service_center_id,
    technician: jc.technician?.name,
    technicianId: jc.technician_id,
    estimatedTime: jc.ai_analysis?.estimated_labor_time,
    estimatedCost: jc.ai_analysis?.estimated_cost_range,
    validationStatus: jc.validation_report?.overall_status,
    vehicle: jc.customer?.vehicle,
  });

  // Fetch technician's jobs
  const fetchJobs = useCallback(async () => {
    try {
      setError(null);
      const response = await api.getTechnicianJobs(user.id);
      // Backend returns job_cards, not jobs
      const jobs = response.job_cards || response.jobs || [];
      setJobCards(jobs.map(transformJobCard));
    } catch (err) {
      console.error("Error fetching jobs:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [user.id]);

  useEffect(() => {
    fetchJobs();

    // Poll for updates every 15 seconds
    const interval = setInterval(fetchJobs, 15000);
    return () => clearInterval(interval);
  }, [fetchJobs]);

  const handleAction = async (action, jobCardId) => {
    try {
      if (action === "start") {
        await api.startJob(jobCardId);
        setNotification(`Job ${jobCardId} started successfully!`);
        fetchJobs();
      } else if (action === "report") {
        setReportModalJob(jobCardId);
      }
    } catch (err) {
      setNotification(`Error: ${err.message}`);
    }

    setTimeout(() => setNotification(null), 5000);
  };

  const handleReportSubmit = async (report) => {
    try {
      await api.submitTechnicianReport(reportModalJob, report);
      setNotification(`Report submitted for ${reportModalJob}. AI validation in progress...`);

      // Trigger AI validation
      try {
        await api.validateJobCard(reportModalJob);
        setNotification(`Job ${reportModalJob} has been validated!`);
      } catch (valErr) {
        console.error("Validation error:", valErr);
      }

      setReportModalJob(null);
      fetchJobs();
    } catch (err) {
      setNotification(`Error submitting report: ${err.message}`);
    }

    setTimeout(() => setNotification(null), 5000);
  };

  const pendingJobs = jobCards.filter(j =>
    ["assigned", "in_progress"].includes(j.status)
  );
  const completedJobs = jobCards.filter(j =>
    ["work_completed", "validated", "completed", "invoiced", "closed"].includes(j.status)
  );

  return (
    <>
      <Header user={user} onLogout={onLogout} />

      <div className="max-w-6xl mx-auto p-6 space-y-8">
        {/* Technician Info */}
        <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="font-bold text-lg">{user.name}</h2>
              <p className="text-sm text-gray-600">
                {user.employeeId} | Service Center: {user.serviceCenterId}
              </p>
              <p className="text-sm text-gray-600">
                Specializations: {user.specializations?.join(", ") || "General"}
              </p>
            </div>
            <button
              onClick={fetchJobs}
              className="text-indigo-600 hover:text-indigo-800 text-sm"
            >
              ↻ Refresh
            </button>
          </div>
        </div>

        {notification && (
          <div className={`p-4 rounded flex justify-between items-center ${
            notification.includes("Error")
              ? "bg-red-100 border border-red-300 text-red-800"
              : "bg-green-100 border border-green-300 text-green-800"
          }`}>
            <span>{notification.includes("Error") ? "❌" : "✅"} {notification}</span>
            <button onClick={() => setNotification(null)} className="hover:opacity-70">✕</button>
          </div>
        )}

        {error && (
          <div className="bg-red-100 border border-red-300 text-red-700 p-4 rounded">
            Error loading jobs: {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading jobs...</div>
        ) : (
          <>
            {/* Active Jobs */}
            <div>
              <h2 className="font-bold text-lg mb-4">Active Jobs ({pendingJobs.length})</h2>
              {pendingJobs.length === 0 ? (
                <p className="text-gray-500 text-sm">No active jobs assigned to you.</p>
              ) : (
                <div className="space-y-4">
                  {pendingJobs.map((job) => (
                    <JobCardView
                      key={job.id}
                      jobCard={job}
                      userRole="technician"
                      onAction={handleAction}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Completed Jobs */}
            <div>
              <h2 className="font-bold text-lg mb-4">Completed Jobs ({completedJobs.length})</h2>
              {completedJobs.length === 0 ? (
                <p className="text-gray-500 text-sm">No completed jobs yet.</p>
              ) : (
                <div className="space-y-4">
                  {completedJobs.map((job) => (
                    <JobCardView
                      key={job.id}
                      jobCard={job}
                      userRole="technician"
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Report Modal */}
      {reportModalJob && (
        <TechnicianReportModal
          jobCardId={reportModalJob}
          onSubmit={handleReportSubmit}
          onClose={() => setReportModalJob(null)}
        />
      )}
    </>
  );
}
