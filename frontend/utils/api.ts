export interface KnowledgeBaseEntry {
  question: string;
  answer: string;
  created_at: string;
}

export interface HelpRequest {
  request_id: string;
  customer_number: string;
  question: string;
  answer?: string;
  status: 'pending' | 'resolved' | 'unresolved';
  created_at: string;
  resolved_at?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export const api = {
  knowledge: {
    getAll: () => fetch(`${API_BASE_URL}/api/knowledge`),
  },
  helpRequests: {
    getAll: () => fetch(`${API_BASE_URL}/api/help-requests`),
    respond: (id: string, response: string) =>
      fetch(`${API_BASE_URL}/api/help-requests/${id}/respond`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ response }),
      }),
  },
};
