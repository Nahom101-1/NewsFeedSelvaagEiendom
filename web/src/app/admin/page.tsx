import Link from "next/link";

import { getAdmin } from "@/lib/api";
import type { AdminPayload } from "@/lib/types";

export const dynamic = "force-dynamic";

/**
 * Everything the reader's page deliberately hides: scores, gate counts, feed
 * health, collection runs and label progress.
 *
 * Denser than the reader's page on purpose — this one is read by whoever owns
 * the pipeline, and the numbers are the point.
 */
export default async function AdminPage() {
  const data = await getAdmin();

  if (!data) {
    return (
      <Shell>
        <h1 className="font-body text-[32px] font-semibold">
          Får ikke kontakt med API-et
        </h1>
        <p className="mt-4 font-sans text-[16px] text-petroleum/70">
          Start Flask: <Code>uv run flask --app nyhetsradar.app run</Code>
        </p>
      </Shell>
    );
  }

  const { totals, labels } = data;
  const labelTotal = labels.relevant + labels.not_relevant;

  return (
    <Shell>
      <header className="border-b-2 border-petroleum pb-5">
        <h1 className="font-body text-[32px] font-semibold">
          Teknisk oversikt
        </h1>
        <p className="mt-2 font-sans text-[15px] text-petroleum/60">
          Oppdatert {data.generated_at} · terskel {data.threshold}
        </p>
      </header>

      <Section title="Volum">
        <Stats
          items={[
            ["Samlet inn", totals.collected],
            ["Unike saker", totals.unique],
            ["Gjennom filter", totals.gated],
            ["Blokkert", totals.blocked],
            ["Over terskel", totals.over_threshold],
            ["Klynger med flere kilder", totals.multi_source_clusters],
          ]}
        />
        <p className="mt-4 font-sans text-[15px] text-petroleum/65">
          Duplikater slått sammen: {totals.collapse_pct} %. Lav andel er ventet
          så lenge innsamlingen er et engangsuttrekk over flere måneder — ekte
          syndikering dukker først opp når det samme nyhetsdøgnet hentes flere
          ganger.
        </p>
      </Section>

      <Section title="Treningsdata">
        <Stats
          items={[
            ["Nyttig", labels.relevant],
            ["Ikke nyttig", labels.not_relevant],
            ["Totalt", labelTotal],
            ["Med embedding", labels.with_embedding],
          ]}
        />
        <p className="mt-4 font-sans text-[15px] text-petroleum/65">
          Fase 2 trenger noen hundre merkede eksempler.{" "}
          {labels.with_embedding === 0 && labelTotal > 0
            ? "Merk at ingen av dem har embedding lagret ennå — den må på plass før dataene kan brukes til å trene."
            : null}
        </p>
      </Section>

      <Section title="Fordeling av poeng">
        <Distribution rows={data.distribution} threshold={data.threshold} />
      </Section>

      <Section title={`Kilder (${data.sources.length})`}>
        <table className="w-full font-sans text-[15px]">
          <thead>
            <tr className="border-b-2 border-petroleum text-left text-[13px] tracking-wide text-petroleum/55 uppercase">
              <th className="py-2 font-normal">Kilde</th>
              <th className="py-2 text-right font-normal">Saker</th>
              <th className="py-2 text-right font-normal">Nyeste</th>
            </tr>
          </thead>
          <tbody>
            {data.sources.map((source) => (
              <tr className="border-b border-sand" key={source.name}>
                <td className="py-2 pr-4">{source.name}</td>
                <td className="py-2 text-right tabular-nums">
                  {source.count}
                </td>
                <td className="py-2 text-right text-petroleum/60">
                  {source.latest || "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title={`Feeder i drift (${data.feeds.length})`}>
        <ul className="font-sans text-[15px]">
          {data.feeds.map((feed) => (
            <li
              className="flex flex-wrap justify-between gap-2 border-b border-sand py-2"
              key={feed.url}
            >
              <span>{feed.name}</span>
              <span className="text-petroleum/55">{feed.type}</span>
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Siste innsamlinger">
        {data.runs.length === 0 ? (
          <p className="font-sans text-[15px] text-petroleum/60">
            Ingen kjøringer registrert.
          </p>
        ) : (
          <ul className="font-sans text-[15px]">
            {data.runs.map((run) => (
              <li className="border-b border-sand py-2" key={run.started}>
                <span className="text-petroleum/55">
                  {run.started.slice(0, 16).replace("T", " ")}
                </span>{" "}
                — {run.inserted} nye av {run.seen} sett, {run.feeds_ok} feeder
                {run.feeds_failed > 0 ? (
                  <span className="text-rust"> ({run.feeds_failed} feilet)</span>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Scoring">
        <Stats
          items={Object.entries(data.scored_by).map(([name, n]) => [name, n])}
        />
      </Section>

      <footer className="mt-14 border-t border-sand pt-6">
        <Link
          className="font-sans text-[15px] text-petroleum/55 no-underline hover:text-petroleum hover:underline"
          href="/"
        >
          Tilbake til nyhetene
        </Link>
      </footer>
    </Shell>
  );
}

function Distribution({
  rows,
  threshold,
}: {
  rows: AdminPayload["distribution"];
  threshold: number;
}) {
  const max = Math.max(1, ...rows.map((r) => r.count));
  return (
    <ul className="font-sans text-[15px]">
      {rows.map((row) => (
        <li className="flex items-center gap-3 py-1" key={row.from}>
          <span className="w-16 shrink-0 tabular-nums text-petroleum/60">
            {row.from}–{row.to}
          </span>
          <span className="h-4 flex-1 bg-sand/50">
            <span
              className={`block h-full ${row.from >= threshold ? "bg-rust" : "bg-petroleum/40"}`}
              style={{ width: `${(row.count / max) * 100}%` }}
            />
          </span>
          <span className="w-12 shrink-0 text-right tabular-nums">
            {row.count}
          </span>
        </li>
      ))}
    </ul>
  );
}

function Stats({ items }: { items: [string, number][] }) {
  return (
    <dl className="grid grid-cols-3 gap-x-6 gap-y-5 max-sm:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label}>
          <dd className="font-sans text-[28px] leading-none font-medium tabular-nums">
            {value}
          </dd>
          <dt className="mt-1.5 font-sans text-[13px] tracking-wide text-petroleum/55 uppercase">
            {label}
          </dt>
        </div>
      ))}
    </dl>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12">
      <h2 className="mb-5 font-sans text-[13px] tracking-[0.13em] text-petroleum/55 uppercase">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="bg-stone px-1.5 py-0.5 font-mono text-[14px]">
      {children}
    </code>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto w-full max-w-[860px] px-6 py-14 max-sm:px-5 max-sm:py-10">
      <p className="mb-10 font-sans text-[13px] tracking-[0.14em] text-petroleum/50 uppercase">
        Nyhetsradar
      </p>
      {children}
    </main>
  );
}
