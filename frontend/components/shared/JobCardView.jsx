"use client";

// Streamlit app URL - configurable via environment variable
const STREAMLIT_APP_URL = process.env.NEXT_PUBLIC_STREAMLIT_URL || "http://localhost:8501";

const statusColors = {
  created: "bg-gray-100 text-gray-700",
  generated: "bg-blue-100 text-blue-700",
  assigned: "bg-purple-100 text-purple-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  work_completed: "bg-orange-100 text-orange-700",
  validated: "bg-teal-100 text-teal-700",
  completed: "bg-green-100 text-green-700",
  invoiced: "bg-green-100 text-green-700",
  closed: "bg-green-100 text-green-700",
};

const severityColors = {
  low: "text-green-600",
  medium: "text-yellow-600",
  high: "text-orange-600",
  critical: "text-red-600",
};

export default function JobCardView({ jobCard, userRole = "customer", onAction }) {
  const statusColor = statusColors[jobCard.status] || "bg-gray-100 text-gray-700";
  const severityColor = severityColors[jobCard.severity?.toLowerCase()] || "text-gray-600";

  // Open Streamlit app with job card ID as query parameter
  const openStreamlitApp = () => {
    const streamlitUrl = `${STREAMLIT_APP_URL}?ro=${jobCard.id}`;
    window.open(streamlitUrl, "_blank");
  };

  return (
    <div className="bg-white p-6 rounded shadow border-l-4 border-indigo-500">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-bold text-lg">{jobCard.id}</h3>
          <p className="text-sm text-gray-500">{jobCard.timestamp}</p>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${statusColor}`}>
          {jobCard.status?.toUpperCase().replace("_", " ") ?? "PENDING"}
        </span>
      </div>

      <div className="bg-gray-50 p-3 rounded mb-4">
        <p className="text-gray-800">{jobCard.customerIssue}</p>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
        <div>
          <span className="text-gray-500">Severity:</span>{" "}
          <span className={`font-medium ${severityColor}`}>
            {jobCard.severity ?? "Analyzing..."}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Service Type:</span>{" "}
          <span className="font-medium">{jobCard.serviceType ?? "Determining..."}</span>
        </div>
        {jobCard.estimatedTime && (
          <div>
            <span className="text-gray-500">Est. Time:</span>{" "}
            <span className="font-medium">{jobCard.estimatedTime}</span>
          </div>
        )}
        {jobCard.estimatedCost && (
          <div>
            <span className="text-gray-500">Est. Cost:</span>{" "}
            <span className="font-medium">{jobCard.estimatedCost}</span>
          </div>
        )}
      </div>

      {jobCard.prescribedActions?.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-1">Recommended Actions:</p>
          <ul className="list-disc ml-5 text-sm space-y-1">
            {jobCard.prescribedActions.map((action, i) => (
              <li key={i}>{action}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="border-t pt-3 mt-3 flex justify-between items-center text-sm">
        <div>
          <span className="text-gray-500">Service Center:</span>{" "}
          <span className="text-indigo-600 font-medium">
            {jobCard.serviceCenter ?? "Assigning..."}
          </span>
          {jobCard.technician && (
            <>
              <span className="text-gray-400 mx-2">|</span>
              <span className="text-gray-500">Technician:</span>{" "}
              <span className="font-medium">{jobCard.technician}</span>
            </>
          )}
        </div>

        {jobCard.validationStatus && (
          <span className={`px-2 py-1 rounded text-xs ${
            jobCard.validationStatus === "approved"
              ? "bg-green-100 text-green-700"
              : jobCard.validationStatus === "needs_review"
              ? "bg-yellow-100 text-yellow-700"
              : "bg-red-100 text-red-700"
          }`}>
            {jobCard.validationStatus === "approved" ? "✓ Validated" : "⚠ Review Needed"}
          </span>
        )}
      </div>

      {jobCard.invoice && (
        <div className="mt-4 bg-green-50 p-3 rounded border border-green-200">
          <p className="text-green-800 font-medium">
            💰 Invoice: ${jobCard.invoice.total_amount?.toFixed(2)}
          </p>
          <p className="text-sm text-green-600">
            Invoice #{jobCard.invoice.invoice_number}
          </p>
        </div>
      )}

      {/* Action buttons for technician */}
      {userRole === "technician" && (
        <div className="mt-4 flex gap-2 flex-wrap">
          {jobCard.status === "assigned" && onAction && (
            <button
              onClick={() => onAction("start", jobCard.id)}
              className="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700"
            >
              ▶ Start Work
            </button>
          )}

          {/* Open Streamlit App - available for in_progress jobs */}
          {(jobCard.status === "in_progress" || jobCard.status === "assigned") && (
            <button
              onClick={openStreamlitApp}
              className="bg-orange-500 text-white px-4 py-2 rounded text-sm hover:bg-orange-600 flex items-center gap-2"
            >
              🔧 Open Service Portal
            </button>
          )}

          {jobCard.status === "in_progress" && onAction && (
            <button
              onClick={() => onAction("report", jobCard.id)}
              className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700"
            >
              ✓ Submit Report
            </button>
          )}
        </div>
      )}
    </div>
  );
}
