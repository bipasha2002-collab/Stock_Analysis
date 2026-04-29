export default function NewsList() {
  const news = [
    { title: "Fed interest rate decision impacts tech stocks", sentiment: "Negative" },
    { title: "Strong earnings boost market confidence", sentiment: "Positive" }
  ];

  return (
    <div className="p-6 bg-[rgb(var(--charcoal))] rounded-xl shadow border border-white/10">
      <h3 className="text-xl font-semibold mb-3 text-white">Recent News</h3>
      <ul className="space-y-2">
        {news.map((n, i) => (
          <li key={i}>
            <span className="font-medium text-white">{n.title}</span>
            <span className="ml-2 text-sm text-[rgb(var(--blue-gray))]">({n.sentiment})</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

