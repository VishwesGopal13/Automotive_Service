"use client";

import { useState } from "react";
import { api } from "@/services/api";

export default function IssueForm({ user, onJobCardCreated }) {
  const [issue, setIssue] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState(null);
  const [validationHint, setValidationHint] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!issue.trim()) return;

    setLoading(true);
    setStatus("Validating your request...");
    setError(null);
    setValidationHint(null);

    try {
      // Step 1: Create service request (includes AI validation)
      let serviceRequest;
      try {
        serviceRequest = await api.createServiceRequest(user.id, issue);
      } catch (validationErr) {
        // Check if it's a validation error
        if (validationErr.message.includes("validation_failed") ||
            validationErr.message.includes("not related") ||
            validationErr.message.includes("Please describe") ||
            validationErr.message.includes("Please provide")) {
          setError(validationErr.message);
          setValidationHint("Please describe a vehicle-related issue such as unusual noises, performance problems, warning lights, or maintenance needs.");
          setLoading(false);
          setStatus("");
          return;
        }
        throw validationErr;
      }

      const jobCardId = serviceRequest.job_card_id;

      setStatus("🤖 AI is analyzing your issue...");

      // Step 2: Generate job card details with AI
      const generatedJobCard = await api.generateJobCard(jobCardId);

      setStatus("📍 Finding nearest service center...");

      // Step 3: Assign to best service center
      const assignment = await api.assignServiceCenter(user.id);

      // Step 4: Assign job card to service center
      const serviceCenterId = assignment.service_center_id || assignment.service_centre_id;
      await api.assignJobCard(jobCardId, serviceCenterId);

      // Step 5: Get complete job card
      const jobCard = await api.getJobCard(jobCardId);

      // Transform to frontend format with AI analysis details
      const formattedJobCard = {
        id: jobCard.id,
        customerIssue: jobCard.complaint_text,
        status: jobCard.status?.toLowerCase() || "pending",
        timestamp: new Date(jobCard.created_at).toLocaleString(),
        severity: jobCard.ai_analysis?.severity_category || "Medium",
        serviceType: jobCard.ai_analysis?.predicted_repair_type || "General Service",
        prescribedActions: jobCard.ai_analysis?.recommended_actions || [],
        requiredTools: jobCard.ai_analysis?.required_tools || [],
        serviceCenter: assignment.service_center_name || assignment.service_centre_name,
        serviceCenterId: assignment.service_center_id || assignment.service_centre_id,
        estimatedTime: jobCard.ai_analysis?.estimated_labor_time || `${jobCard.estimated_labor_hours} hours`,
        estimatedCost: jobCard.ai_analysis?.estimated_cost_range || `$${jobCard.estimated_cost?.toFixed(0)}`,
        additionalNotes: jobCard.ai_analysis?.additional_notes,
        vehicle: serviceRequest.vehicle,
      };

      onJobCardCreated(formattedJobCard);
      setIssue("");
      setStatus("");
    } catch (err) {
      console.error(err);
      setError(err.message || "Failed to create job card");
      setStatus("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded shadow">
      <h2 className="font-bold text-lg mb-2">Describe Your Vehicle Issue</h2>
      <p className="text-sm text-gray-600 mb-4">
        Our AI will analyze your issue and generate a detailed job card with recommended repairs.
      </p>

      {user.vehicle && (
        <div className="bg-gray-50 p-3 rounded mb-4 text-sm">
          <strong>Your Vehicle:</strong> {user.vehicle.year} {user.vehicle.make} {user.vehicle.model}
        </div>
      )}

      <textarea
        className="w-full p-3 border rounded focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        rows={4}
        value={issue}
        onChange={(e) => {
          setIssue(e.target.value);
          if (error) {
            setError(null);
            setValidationHint(null);
          }
        }}
        placeholder="e.g., My car is making a strange grinding noise when I apply the brakes. It feels like the braking power has decreased recently."
        required
        disabled={loading}
      />

      {error && (
        <div className="mt-3 bg-red-100 border border-red-300 text-red-700 p-3 rounded text-sm">
          <div className="font-medium">❌ {error}</div>
          {validationHint && (
            <div className="mt-2 text-red-600 text-xs">
              💡 Tip: {validationHint}
            </div>
          )}
        </div>
      )}

      {status && (
        <div className="mt-3 bg-blue-100 border border-blue-300 text-blue-700 p-3 rounded text-sm flex items-center">
          <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          {status}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between">
        <button
          type="submit"
          disabled={loading || !issue.trim()}
          className="bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? "Processing..." : "🔧 Generate Job Card"}
        </button>

        <span className="text-xs text-gray-500">
          Powered by AI
        </span>
      </div>
    </form>
  );
}
