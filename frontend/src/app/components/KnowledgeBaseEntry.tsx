import React from "react";
import { KnowledgeBaseEntry as KBEntry } from "../../../utils/api";

interface KnowledgeBaseEntryProps {
  entry: KBEntry;
}

const KnowledgeBaseEntry: React.FC<KnowledgeBaseEntryProps> = ({ entry }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="bg-white shadow rounded-lg p-4 mb-4 border-l-4 border-green-500">
      <div className="mb-2">
        <h3 className="font-semibold">Question:</h3>
        <p className="text-gray-700">{entry.question}</p>
      </div>
      <div className="mb-2">
        <h3 className="font-semibold">Answer:</h3>
        <p className="text-gray-700">{entry.answer}</p>
      </div>
      <p className="text-xs text-gray-500">
        Added on: {formatDate(entry.created_at)}
      </p>
    </div>
  );
};

export default KnowledgeBaseEntry;
