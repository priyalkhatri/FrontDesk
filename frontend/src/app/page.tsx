import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <main className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-8">
          AI Receptionist System
        </h1>

        <div className="grid md:grid-cols-2 gap-6 mt-12">
          <Link
            href="/pages/knowledge"
            className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-100 transition-colors"
          >
            <h2 className="text-2xl text-gray-800 font-bold mb-2">
              Knowledge Base
            </h2>
            <p className="text-gray-600">
              View and manage learned answers from customer interactions
            </p>
          </Link>

          <Link
            href="/pages/requests"
            className="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-100 transition-colors"
          >
            <h2 className="text-2xl font-bold mb-2 text-gray-800">
              Help Requests
            </h2>
            <p className="text-gray-600">
              Manage and respond to pending customer inquiries
            </p>
          </Link>
        </div>

        <div className="mt-12 p-6 bg-blue-50 rounded-lg">
          <h3 className="text-xl font-semibold mb-2 text-gray-800">
            System Status
          </h3>
          <p className="text-gray-700">AI Receptionist is running...</p>
          <p className="text-sm text-gray-500 mt-2">
            The system will automatically escalate unknown questions to
            supervisors.
          </p>
        </div>
      </div>
    </main>
  );
}
