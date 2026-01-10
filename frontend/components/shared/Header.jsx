"use client";

import { Car, LogOut, User, Wrench } from "lucide-react";

export default function Header({ user, onLogout }) {
  return (
    <header className="bg-white shadow p-4 flex justify-between items-center">
      <div className="flex items-center gap-3">
        <Car className="text-indigo-600 w-8 h-8" />
        <div>
          <h1 className="font-bold text-lg">AutoService AI</h1>
          <p className="text-sm text-gray-500 capitalize">
            {user.role} Portal
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          {user.role === "customer" ? (
            <User className="w-4 h-4 text-gray-500" />
          ) : (
            <Wrench className="w-4 h-4 text-gray-500" />
          )}
          <div className="text-right">
            <p className="font-medium">{user.name}</p>
            <p className="text-xs text-gray-500">
              {user.role === "customer" ? user.id : user.employeeId}
            </p>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition flex items-center gap-2"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </header>
  );
}
