import Link from "next/link";

import { StoryCard } from "@/components/story-card";
import { getBrief } from "@/lib/api";

export const dynamic = "force-dynamic";

/**
 * The reader's page. One column, one job: read the week's stories and say
 * whether each was useful.
 *
 * Everything technical — scores, thresholds, feed health, counts — is on
 * /admin. Nothing here needs explaining to use.
 */
export default async function HomePage() {
  const data = await getBrief();

  if (!data) {
    return (
      <Shell>
        <h1 className="font-body text-[34px] font-semibold">
          Får ikke kontakt med serveren
        </h1>
        <p className="mt-4 max-w-[55ch] font-body text-[19px] leading-relaxed text-petroleum/80">
          Nyhetsradar henter saker fra et program som ikke svarer akkurat nå.
          Prøv å laste siden på nytt om litt.
        </p>
      </Shell>
    );
  }

  const count = data.stories.length;

  return (
    <Shell>
      <header>
        <h1 className="font-body text-[40px] leading-tight font-semibold text-balance max-sm:text-[30px]">
          Nyheter denne uken
        </h1>
        <p className="mt-3 font-sans text-[17px] text-petroleum/65">
          {count === 0
            ? "Ingen saker akkurat nå."
            : count === 1
              ? "1 sak å lese."
              : `${count} saker å lese.`}{" "}
          Oppdatert {data.generated_at}.
        </p>
      </header>

      {count > 0 ? (
        <>
          <p className="mt-8 max-w-[55ch] rounded-none border-l-2 border-rust bg-fromage px-5 py-4 font-body text-[18px] leading-relaxed">
            Les overskriftene. Trykk <strong>Nyttig for meg</strong> eller{" "}
            <strong>Ikke nyttig</strong> under hver sak. Det gjør listen bedre
            neste uke.
          </p>

          <div className="mt-10">
            {data.stories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        </>
      ) : (
        <p className="mt-8 max-w-[55ch] font-body text-[19px] leading-relaxed text-petroleum/80">
          Det har ikke kommet noe nytt som er verdt å lese ennå. Prøv igjen
          senere i dag.
        </p>
      )}

      <footer className="mt-16 border-t border-sand pt-6">
        <Link
          className="font-sans text-[15px] text-petroleum/55 no-underline hover:text-petroleum hover:underline"
          href="/admin"
        >
          Teknisk oversikt
        </Link>
      </footer>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="mx-auto w-full max-w-[720px] px-6 py-14 max-sm:px-5 max-sm:py-10">
      <p className="mb-10 font-sans text-[13px] tracking-[0.14em] text-petroleum/50 uppercase">
        Nyhetsradar
      </p>
      {children}
    </main>
  );
}
