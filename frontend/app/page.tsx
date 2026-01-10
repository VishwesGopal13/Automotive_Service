"use client";

import { useState } from "react";
import Login from "@/components/auth/Login";
import CustomerDashboard from "@/components/customer/CustomerDashboard";
import TechnicianDashboard from "@/components/technician/TechnicianDashboard";

export default function HomePage() {
  const [user, setUser] = useState<any>(null);

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  return user.role === "customer" ? (
    <CustomerDashboard user={user} onLogout={() => setUser(null)} />
  ) : (
    <TechnicianDashboard user={user} onLogout={() => setUser(null)} />
  );
}
