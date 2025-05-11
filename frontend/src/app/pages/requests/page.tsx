"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import HelpRequestCard from "../../components/HelpRequestCard";
import { HelpRequest } from "../../../../utils/api";

export default function RequestsPage() {
  const [requests, setRequests] = useState<HelpRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    fetchRequests();
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchRequests, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchRequests = async () => {
    try {
      const response = await fetch("/api/help-requests");
      if (!response.ok) throw new Error("Failed to fetch requests");
      const data = await response.json();
      setRequests(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleResponse = async (requestId: string, response: string) => {
    try {
      const res = await fetch(`/api/help-requests/${requestId}/respond`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ response }),
      });

      if (!res.ok) throw new Error("Failed to submit response");

      // Refresh the requests
      fetchRequests();
    } catch (err) {
      console.error("Error submitting response:", err);
      alert("Failed to submit response");
    }
  };

  const filteredRequests = requests.filter(
    (request) => statusFilter === "all" || request.status === statusFilter
  );

  if (loading && requests.length === 0)
    return <div className="text-center py-8">Loading...</div>;
  if (error)
    return <div className="text-red-500 text-center py-8">Error: {error}</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Help Requests</h1>
          <Link
            href="/"
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
          >
            Back to Home
          </Link>
        </div>

        <div className="mb-6">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Requests</option>
            <option value="pending">Pending</option>
            <option value="resolved">Resolved</option>
            <option value="unresolved">Unresolved</option>
          </select>
        </div>

        <div className="space-y-4">
          {filteredRequests.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No {statusFilter === "all" ? "" : statusFilter} requests found
            </p>
          ) : (
            filteredRequests.map((request) => (
              <HelpRequestCard
                key={request.request_id}
                request={request}
                onResolve={handleResponse}
                onMarkUnresolved={(id) => handleResponse(id, "Marked as unresolved")}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
