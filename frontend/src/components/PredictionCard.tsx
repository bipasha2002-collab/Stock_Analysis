export default function PredictionCard({ data }: { data: any }) {
  if (!data) return null;

  return (
    <div className="p-6 bg-[rgb(var(--charcoal))] rounded-xl shadow border border-white/10">
      <h3 className="text-xl font-semibold mb-2 text-white">AI Prediction</h3>
      <p className="text-lg text-[rgb(var(--blue-gray))]">
        Prediction: <b className="text-white">{data.prediction}</b>
      </p>
      <p className="text-[rgb(var(--blue-gray))]">Confidence: <span className="text-white">{Math.round(data.confidence * 100)}%</span></p>
      <p className="text-[rgb(var(--blue-gray))]">Risk Level: <span className="text-white">{data.risk_level}</span></p>
    </div>
  );
}
