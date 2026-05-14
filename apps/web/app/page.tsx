import Link from "next/link";

const CARDS = [
  {
    title: "1. Pick a dataset",
    description: "Import from Hugging Face or upload a CSV/JSON/XLSX file.",
    href: "/datasets",
    cta: "Manage datasets",
  },
  {
    title: "2. Configure an experiment",
    description:
      "Choose task lanes, models and sampling. Runs locally with the deterministic mock provider by default.",
    href: "/experiments/new",
    cta: "Launch a run",
  },
  {
    title: "3. Compare & report",
    description: "Side-by-side metrics plus an AI-generated markdown report with verified references.",
    href: "/compare",
    cta: "Open comparison",
  },
];

export default function Home() {
  return (
    <section className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Research-grade NLP comparison</h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Evaluate three LLM families across classification, summarization, question-answering and
          instruction-following — with reproducible metrics, artifacts and validated references.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-brand-500 hover:shadow-md"
          >
            <h2 className="text-lg font-medium">{card.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{card.description}</p>
            <span className="mt-4 inline-flex items-center text-sm font-medium text-brand-600">
              {card.cta} →
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
