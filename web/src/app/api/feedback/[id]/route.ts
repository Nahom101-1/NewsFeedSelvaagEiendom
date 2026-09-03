import { NextResponse } from "next/server";

import { flaskOrigin } from "@/lib/api";

/**
 * Proxies a judgement through to Flask.
 *
 * The browser talks to this route rather than to Flask directly, so there is
 * no cross-origin request to configure and the API origin stays private.
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const body = await request.json().catch(() => null);

  if (body?.label !== "relevant" && body?.label !== "not_relevant") {
    return NextResponse.json({ error: "ugyldig vurdering" }, { status: 400 });
  }

  try {
    const response = await fetch(`${flaskOrigin}/api/feedback/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: body.label }),
      cache: "no-store",
    });
    return NextResponse.json(await response.json(), {
      status: response.status,
    });
  } catch {
    return NextResponse.json(
      { error: "får ikke kontakt med serveren" },
      { status: 502 },
    );
  }
}
