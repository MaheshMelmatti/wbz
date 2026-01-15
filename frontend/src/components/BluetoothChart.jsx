import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from "recharts";

export default function BluetoothChart({ items }) {
  if (!items?.length) return null;

  const data = items.map((d) => ({
    name: d["Device Name"],
    proximity: Number(d["Proximity (%)"]) || 0,
  }));

  const best = Math.max(...data.map(d => d.proximity));

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <XAxis dataKey="name" tick={{ fill: "#cbd5f5" }} />
          <YAxis
            domain={[0, 100]}
            tick={{ fill: "#cbd5f5" }}
            label={{ value: "Proximity (%)", angle: -90, position: "insideLeft" }}
          />
          <Tooltip />
          <Bar dataKey="proximity" radius={[6, 6, 0, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.proximity === best ? "#22c55e" : "#38bdf8"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
