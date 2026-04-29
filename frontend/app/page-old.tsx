"use client";

import { useState } from "react";
import Header from "@/components/Header";
import { StockSearch } from "@/components/StockSearch";
import PopularStocks from "@/components/PopularStocks";
import PredictionCard from "@/components/PredictionCard";
import NewsList from "@/components/NewsList";
import { api } from "@/lib/api";

export default function HomePage() {
  const [prediction, setPrediction] = useState<any>(null);

  const handleSearch = async (symbol: string) => {
    const res = await api.getPrediction(symbol);
    setPrediction(res);
  };

  return (
    <main className="max-w-6xl mx-auto px-6 py-10">
      <Header />
      <StockSearch onStockSelect={handleSearch} />
      <PopularStocks onSelect={handleSearch} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
        <PredictionCard data={prediction} />
        <NewsList />
      </div>
    </main>
  );
}
