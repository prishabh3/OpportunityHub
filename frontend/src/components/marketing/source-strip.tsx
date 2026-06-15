const sources = [
  "Google",
  "Microsoft",
  "Amazon",
  "Meta",
  "Apple",
  "NVIDIA",
  "OpenAI",
  "Anthropic",
  "Stripe",
  "Netflix",
  "Uber",
  "Airbnb",
  "Devpost",
  "MLH",
  "Unstop",
];

export function SourceStrip() {
  return (
    <section className="border-y border-border/40 bg-card/30 px-6 py-10">
      <div className="mx-auto max-w-6xl">
        <p className="mb-6 text-center text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Aggregating opportunities from
        </p>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4">
          {sources.map((source) => (
            <span
              key={source}
              className="text-sm font-medium text-muted-foreground/70 transition-colors hover:text-foreground"
            >
              {source}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
