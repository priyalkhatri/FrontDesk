import { NextResponse } from "next/server";

export async function GET() {
  try {
    // Replace with your actual backend URL
    const response = await fetch("http://localhosthost:5000/api/knowledge", {
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch knowledge entries");
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Failed to fetch knowledge entries" },
      { status: 500 }
    );
  }
}
