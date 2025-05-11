"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import KnowledgeBaseEntry from "../../components/KnowledgeBaseEntry";

interface KnowledgeEntry {
  id: string;
  question: string;
  answer: string;
  created_at: string;
  updated_at: string;
  source_request_id?: string;
}

export default function KnowledgePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchKnowledgeEntries();
  }, []);

  const fetchKnowledgeEntries = async () => {
    try {
      const response = await fetch("/api/knowledge");
      if (!response.ok) throw new Error("Failed to fetch knowledge entries");
      const data = await response.json();
      setEntries(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const filteredEntries = entries.filter(
    (entry) =>
      entry.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      entry.answer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Knowledge Base</h1>
          <Link
            href="/"
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 transition-colors"
          >
            Back to Home
          </Link>
        </div>

        <div className="mb-6">
          <input
            type="text"
            placeholder="Search questions and answers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="space-y-4">
          {filteredEntries.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              {searchTerm
                ? "No matching entries found"
                : "No knowledge entries yet"}
            </p>
          ) : (
            filteredEntries.map((entry) => (
              <KnowledgeBaseEntry key={entry.id} entry={entry} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
