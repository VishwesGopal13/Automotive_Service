"use client";

import { useState } from "react";

export default function TechnicianReportModal({ jobCardId, onSubmit, onClose }) {
  const [report, setReport] = useState({
    procedures_performed: "",
    parts_replaced: "",
    tools_used: "",
    labor_time: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    // Convert comma-separated strings to arrays
    const formattedReport = {
      procedures_performed: report.procedures_performed.split(",").map(s => s.trim()).filter(Boolean),
      parts_replaced: report.parts_replaced.split(",").map(s => s.trim()).filter(Boolean),
      tools_used: report.tools_used.split(",").map(s => s.trim()).filter(Boolean),
      labor_time: report.labor_time,
      notes: report.notes,
    };

    await onSubmit(formattedReport);
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Submit Work Report</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">
              ×
            </button>
          </div>

          <p className="text-sm text-gray-600 mb-4">Job Card: {jobCardId}</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Procedures Performed *
              </label>
              <textarea
                className="w-full p-2 border rounded"
                rows={2}
                placeholder="e.g., Inspected brake pads, Replaced worn brake pads, Test drive"
                value={report.procedures_performed}
                onChange={(e) => setReport({ ...report, procedures_performed: e.target.value })}
                required
              />
              <p className="text-xs text-gray-500">Separate multiple items with commas</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Parts Replaced
              </label>
              <input
                type="text"
                className="w-full p-2 border rounded"
                placeholder="e.g., Front brake pads, Brake rotors"
                value={report.parts_replaced}
                onChange={(e) => setReport({ ...report, parts_replaced: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tools Used
              </label>
              <input
                type="text"
                className="w-full p-2 border rounded"
                placeholder="e.g., Socket set, Jack stands, Torque wrench"
                value={report.tools_used}
                onChange={(e) => setReport({ ...report, tools_used: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Labor Time *
              </label>
              <input
                type="text"
                className="w-full p-2 border rounded"
                placeholder="e.g., 2 hours"
                value={report.labor_time}
                onChange={(e) => setReport({ ...report, labor_time: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Additional Notes
              </label>
              <textarea
                className="w-full p-2 border rounded"
                rows={2}
                placeholder="Any additional observations or recommendations..."
                value={report.notes}
                onChange={(e) => setReport({ ...report, notes: e.target.value })}
              />
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 py-2 border border-gray-300 rounded hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
              >
                {submitting ? "Submitting..." : "Submit Report"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

