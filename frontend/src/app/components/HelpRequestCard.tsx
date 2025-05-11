import React, { useState } from "react";
import { HelpRequest } from "../../../utils/api";

interface HelpRequestCardProps {
  request: HelpRequest;
  onResolve: (requestId: string, answer: string) => void;
  onMarkUnresolved: (requestId: string) => void;
}

const HelpRequestCard: React.FC<HelpRequestCardProps> = ({
  request,
  onResolve,
  onMarkUnresolved,
}) => {
  const [answer, setAnswer] = useState("");

  const formatDate = (dateString: string) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleString();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (answer.trim()) {
      onResolve(request.request_id, answer);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-4 mb-4 border-l-4 border-blue-500">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-sm text-gray-500">
            From: {request.customer_number}
          </p>
          <p className="text-sm text-gray-500">
            Created: {formatDate(request.created_at)}
          </p>
          <div className="mt-2">
            <h3 className="font-semibold">Question:</h3>
            <p className="text-gray-700">{request.question}</p>
          </div>
        </div>
        <span
          className={`px-2 py-1 rounded-full text-xs font-semibold ${
            request.status === "pending"
              ? "bg-yellow-100 text-yellow-800"
              : request.status === "resolved"
              ? "bg-green-100 text-green-800"
              : "bg-red-100 text-red-800"
          }`}
        >
          {request.status}
        </span>
      </div>

      {request.status === "resolved" && (
        <div className="mt-3">
          <h3 className="font-semibold">Answer:</h3>
          <p className="text-gray-700">{request.answer}</p>
          <p className="text-xs text-gray-500 mt-1">
            Resolved at: {formatDate(request.resolved_at || "")}
          </p>
        </div>
      )}

      {request.status === "pending" && (
        <form onSubmit={handleSubmit} className="mt-3">
          <div className="mb-3">
            <label
              htmlFor={`answer-${request.request_id}`}
              className="block font-semibold mb-1"
            >
              Your Answer:
            </label>
            <textarea
              id={`answer-${request.request_id}`}
              className="w-full p-2 border rounded-md"
              rows={3}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              required
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              onClick={() => onMarkUnresolved(request.request_id)}
            >
              Mark Unresolved
            </button>
            <button
              type="submit"
              className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              Send Answer
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default HelpRequestCard;
