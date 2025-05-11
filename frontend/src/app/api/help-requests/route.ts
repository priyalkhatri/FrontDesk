import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Replace with your actual backend URL
    const response = await fetch("http://localhost:5000/api/help-requests", {
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch help requests");
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch help requests" },
      { status: 500 }
    );
  }
}
