"use client";

import { useState, useTransition } from "react";

import type { Feedback, Story } from "@/lib/types";

/**
 * One story, plus the two buttons that are the whole point of the pilot:
 * every click is a labelled training example.
 *
 * Deliberately plain. No score, no category, no cluster chip — a number reads
 * as more precise than it is, and none of it helps the reader decide whether
 * the story matters. That detail lives on /admin.
 */
export function StoryCard({ story }: { story: Story }) {
  const [choice, setChoice] = useState<Feedback>(story.feedback);
  const [failed, setFailed] = useState(false);
  const [pending, startTransition] = useTransition();

  function choose(label: Exclude<Feedback, null>) {
    const next = choice === label ? null : label;
    const previous = choice;

    // Optimistic: the button responds immediately and rolls back if the write
    // fails, so a slow network never feels like a dead button.
    setChoice(next);
    setFailed(false);

    startTransition(async () => {
      try {
        const response = await fetch(`/api/feedback/${story.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ label: next ?? label }),
        });
        if (!response.ok) throw new Error();
      } catch {
        setChoice(previous);
        setFailed(true);
      }
    });
  }

  const note = story.why || story.summary;

  return (
    <article className="border-b border-sand py-8 first:pt-0">
      <a
        className="group block no-underline"
        href={story.url}
        target="_blank"
        rel="noopener noreferrer"
      >
        <h2 className="font-body text-[26px] leading-snug font-semibold text-balance text-petroleum group-hover:underline max-sm:text-[22px]">
          {story.title}
        </h2>
      </a>

      {note ? (
        <p className="mt-3 max-w-[62ch] font-body text-[19px] leading-relaxed text-pretty text-petroleum/80 max-sm:text-[17px]">
          {note}
        </p>
      ) : null}

      <p className="mt-3 font-sans text-[15px] text-petroleum/60">
        {story.source} · {story.published}
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Choice
          onClick={() => choose("relevant")}
          selected={choice === "relevant"}
          disabled={pending}
          tone="yes"
        >
          Nyttig for meg
        </Choice>
        <Choice
          onClick={() => choose("not_relevant")}
          selected={choice === "not_relevant"}
          disabled={pending}
          tone="no"
        >
          Ikke nyttig
        </Choice>

        {choice && !failed ? (
          <span className="font-sans text-[15px] text-petroleum/55">Takk</span>
        ) : null}
        {failed ? (
          <span className="font-sans text-[15px] text-rust">
            Kunne ikke lagre. Prøv igjen.
          </span>
        ) : null}
      </div>
    </article>
  );
}

function Choice({
  children,
  onClick,
  selected,
  disabled,
  tone,
}: {
  children: React.ReactNode;
  onClick: () => void;
  selected: boolean;
  disabled: boolean;
  tone: "yes" | "no";
}) {
  // 52px tall and full-width on phones: comfortably above the 44px minimum
  // touch target, and easy to hit without aiming.
  const base =
    "inline-flex min-h-[52px] items-center justify-center border-2 px-6 font-sans text-[17px] " +
    "transition-colors disabled:opacity-60 max-sm:w-full";
  const selectedStyle =
    tone === "yes"
      ? "border-petroleum bg-petroleum text-paper"
      : "border-petroleum bg-sand text-petroleum";
  const idle =
    "border-petroleum/30 bg-transparent text-petroleum hover:border-petroleum hover:bg-fromage";

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={selected}
      className={`${base} ${selected ? selectedStyle : idle}`}
    >
      {selected ? `✓ ${children}` : children}
    </button>
  );
}
