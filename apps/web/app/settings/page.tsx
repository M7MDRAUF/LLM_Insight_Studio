export default function SettingsPage() {
  return (
    <section className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="text-sm text-slate-600">
        Runtime configuration is controlled by the API via environment variables. Use the{" "}
        <code>.env</code> file at the repo root to override.
      </p>
      <ul className="list-disc space-y-1 pl-6 text-sm">
        <li>
          <code>INFERENCE_PROVIDER</code> — <code>mock</code> (default) or <code>transformers</code>.
        </li>
        <li>
          <code>HF_TOKEN</code> — optional, needed for private Hugging Face assets.
        </li>
        <li>
          <code>WEB_ORIGIN</code> — allowed CORS origin (default <code>http://localhost:3000</code>).
        </li>
        <li>
          <code>NEXT_PUBLIC_API_BASE_URL</code> — overrides the API base in the web UI.
        </li>
      </ul>
    </section>
  );
}
