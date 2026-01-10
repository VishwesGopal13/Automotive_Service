const API_BASE = "http://localhost:5000/api";

async function handleResponse(res) {
  const data = await res.json();
  if (!res.ok) {
    // Include validation_failed flag in error if present
    const errorMessage = data.hint
      ? `${data.error} ${data.hint}`
      : data.error || "API request failed";
    throw new Error(errorMessage);
  }
  return data;
}

export const api = {
  // =============================================================================
  // CUSTOMER ENDPOINTS
  // =============================================================================

  // Get list of customers (for login selection)
  getCustomers: async (page = 1, perPage = 20) => {
    const res = await fetch(`${API_BASE}/customers?page=${page}&per_page=${perPage}`);
    return handleResponse(res);
  },

  // Get customer details
  getCustomer: async (customerId) => {
    const res = await fetch(`${API_BASE}/customers/${customerId}`);
    return handleResponse(res);
  },

  // Get nearby service centers for a customer
  getNearbyCenters: async (customerId) => {
    const res = await fetch(`${API_BASE}/customers/${customerId}/nearby-centers`);
    return handleResponse(res);
  },

  // Get best service center assignment
  assignServiceCenter: async (customerId) => {
    const res = await fetch(`${API_BASE}/assign-service-center/${customerId}`);
    return handleResponse(res);
  },

  // Validate a complaint text before submitting
  validateComplaint: async (complaintText) => {
    const res = await fetch(`${API_BASE}/validate-complaint`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ complaint_text: complaintText }),
    });
    return handleResponse(res);
  },

  // =============================================================================
  // SERVICE REQUEST & JOB CARD ENDPOINTS
  // =============================================================================

  // Create a new service request (job card) - includes AI validation
  createServiceRequest: async (customerId, complaintText) => {
    const res = await fetch(`${API_BASE}/service-request`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ customer_id: customerId, complaint_text: complaintText }),
    });
    return handleResponse(res);
  },

  // Generate job card details (AI)
  generateJobCard: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/generate`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  // Get job card details
  getJobCard: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}`);
    return handleResponse(res);
  },

  // Assign job card to service center and technician
  assignJobCard: async (jobCardId, serviceCenterId, technicianId = null) => {
    const body = { service_center_id: serviceCenterId };
    if (technicianId) body.technician_id = technicianId;

    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return handleResponse(res);
  },

  // =============================================================================
  // TECHNICIAN ENDPOINTS
  // =============================================================================

  // Get list of technicians
  getTechnicians: async (serviceCenterId = null) => {
    const url = serviceCenterId
      ? `${API_BASE}/technicians?service_center_id=${serviceCenterId}`
      : `${API_BASE}/technicians`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  // Get jobs assigned to a technician
  getTechnicianJobs: async (technicianId) => {
    const res = await fetch(`${API_BASE}/technician/${technicianId}/jobs`);
    return handleResponse(res);
  },

  // Start a job
  startJob: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/start`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  // Submit technician report
  submitTechnicianReport: async (jobCardId, report) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/technician-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    });
    return handleResponse(res);
  },

  // Get technician report
  getTechnicianReport: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/technician-report`);
    return handleResponse(res);
  },

  // =============================================================================
  // VALIDATION & INVOICE ENDPOINTS
  // =============================================================================

  // Validate job card (AI)
  validateJobCard: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/validate`, {
      method: "POST",
    });
    return handleResponse(res);
  },

  // Get validation report
  getValidationReport: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/validation-report`);
    return handleResponse(res);
  },

  // Generate invoice
  generateInvoice: async (jobCardId, invoiceData = {}) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/generate-invoice`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(invoiceData),
    });
    return handleResponse(res);
  },

  // Get invoice
  getInvoice: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/invoice`);
    return handleResponse(res);
  },

  // Get full audit report
  getAuditReport: async (jobCardId) => {
    const res = await fetch(`${API_BASE}/job-card/${jobCardId}/audit-report`);
    return handleResponse(res);
  },
};
