"use client";

import { useState, useEffect } from "react";
import { Car, User, Wrench } from "lucide-react";
import { api } from "@/services/api";

export default function Login({ onLogin }) {
  const [role, setRole] = useState("customer");
  const [customers, setCustomers] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState("");
  const [selectedTechnician, setSelectedTechnician] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [customersRes, techniciansRes] = await Promise.all([
        api.getCustomers(1, 50),
        api.getTechnicians(),
      ]);
      setCustomers(customersRes.customers || []);
      setTechnicians(techniciansRes.technicians || []);
    } catch (err) {
      setError("Failed to connect to backend. Make sure the server is running on port 5000.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (role === "customer") {
      const customer = customers.find(c => c.id === selectedCustomer);
      if (customer) {
        onLogin({
          id: customer.id,
          name: customer.name,
          email: customer.email,
          role: "customer",
          vehicle: customer.vehicle,
          location: customer.location_human,
        });
      }
    } else {
      const technician = technicians.find(t => t.id === parseInt(selectedTechnician));
      if (technician) {
        onLogin({
          id: technician.id,
          name: technician.name,
          employeeId: technician.employee_id,
          role: "technician",
          serviceCenterId: technician.service_center_id,
          specializations: technician.specializations,
        });
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-xl w-full max-w-md">
        <div className="flex justify-center mb-4">
          <Car className="w-12 h-12 text-indigo-600" />
        </div>

        <h1 className="text-2xl font-bold text-center mb-6">
          AutoService AI
        </h1>

        {error && (
          <div className="bg-red-100 border border-red-300 text-red-700 p-3 rounded mb-4 text-sm">
            {error}
            <button
              onClick={loadData}
              className="ml-2 underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}

        <div className="flex gap-2 mb-6">
          <button
            type="button"
            onClick={() => setRole("customer")}
            className={`flex-1 py-2 rounded transition ${
              role === "customer"
                ? "bg-indigo-600 text-white"
                : "bg-gray-200 hover:bg-gray-300"
            }`}
          >
            <User className="inline mr-2 w-4 h-4" /> Customer
          </button>

          <button
            type="button"
            onClick={() => setRole("technician")}
            className={`flex-1 py-2 rounded transition ${
              role === "technician"
                ? "bg-indigo-600 text-white"
                : "bg-gray-200 hover:bg-gray-300"
            }`}
          >
            <Wrench className="inline mr-2 w-4 h-4" /> Technician
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">
            Loading...
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {role === "customer" ? (
              <>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Customer
                </label>
                <select
                  className="w-full p-3 border rounded bg-white"
                  value={selectedCustomer}
                  onChange={(e) => setSelectedCustomer(e.target.value)}
                  required
                >
                  <option value="">-- Select a customer --</option>
                  {customers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.id}) - {c.vehicle?.make} {c.vehicle?.model}
                    </option>
                  ))}
                </select>
                {selectedCustomer && (
                  <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                    {(() => {
                      const c = customers.find(c => c.id === selectedCustomer);
                      return c ? (
                        <>
                          <p><strong>Vehicle:</strong> {c.vehicle?.year} {c.vehicle?.make} {c.vehicle?.model}</p>
                          <p><strong>Location:</strong> {c.location_human}</p>
                        </>
                      ) : null;
                    })()}
                  </div>
                )}
              </>
            ) : (
              <>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Technician
                </label>
                <select
                  className="w-full p-3 border rounded bg-white"
                  value={selectedTechnician}
                  onChange={(e) => setSelectedTechnician(e.target.value)}
                  required
                >
                  <option value="">-- Select a technician --</option>
                  {technicians.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name} ({t.employee_id}) - {t.service_center_id}
                    </option>
                  ))}
                </select>
                {selectedTechnician && (
                  <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                    {(() => {
                      const t = technicians.find(t => t.id === parseInt(selectedTechnician));
                      return t ? (
                        <>
                          <p><strong>Employee ID:</strong> {t.employee_id}</p>
                          <p><strong>Service Center:</strong> {t.service_center_id}</p>
                          <p><strong>Specializations:</strong> {t.specializations?.join(", ") || "General"}</p>
                          <p><strong>Status:</strong> {t.availability_status}</p>
                        </>
                      ) : null;
                    })()}
                  </div>
                )}
              </>
            )}

            <button
              type="submit"
              disabled={role === "customer" ? !selectedCustomer : !selectedTechnician}
              className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Login as {role === "customer" ? "Customer" : "Technician"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
