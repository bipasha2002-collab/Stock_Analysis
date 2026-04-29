import { useEffect, useState } from "react";
import { api, DemoStock } from "@/lib/api";

export default function PopularStocks({
  onSelect,
}: {
  onSelect: (s: string) => void;
}) {
  const [stocks, setStocks] = useState<DemoStock[]>([]);

  useEffect(() => {
    api.getDemoStocks().then((data) => {
      setStocks(data.stocks);
    });
  }, []);

  return (
    <select
      onChange={(e) => onSelect(e.target.value)}
      className="mb-6 px-4 py-2 border rounded-md"
    >
      <option value="">Select popular stock</option>

      {stocks.map((s) => (
        <option key={s.symbol} value={s.symbol}>
          {s.symbol} — {s.name}
        </option>
      ))}
    </select>
  );
}
