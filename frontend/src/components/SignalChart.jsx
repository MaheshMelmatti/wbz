import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip
);

export default function SignalChart({
  items = [],
  onPointClick,
  selectedIndex,
}) {
  if (!items.length) {
    return (
      <div className="text-slate-400 text-center py-10">
        No signal data to display.
      </div>
    );
  }

  const labels = items.map(
    (n, i) => n.Name || n.ssid || `Network ${i + 1}`
  );

  const values = items.map((n) => {
    const v = n["Signal (dBm)"] ?? n.rssi ?? -90;
    return typeof v === "string" ? parseInt(v) : v;
  });

  const data = {
    labels,
    datasets: [
      {
        data: values,
        borderColor: "#38bdf8",
        backgroundColor: "rgba(56,189,248,0.15)",
        tension: 0.35,
        fill: true,

        pointRadius: 5,
        pointHoverRadius: 9,
        pointBorderWidth: 2,

        pointBackgroundColor: values.map((_, i) =>
          i === selectedIndex ? "#22c55e" : "#38bdf8"
        ),
        pointBorderColor: values.map((_, i) =>
          i === selectedIndex ? "#22c55e" : "#0ea5e9"
        ),
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,

    onClick: (_, elements) => {
      if (elements.length && onPointClick) {
        onPointClick(elements[0].index);
      }
    },

    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(15,23,42,0.95)",
        borderColor: "#38bdf8",
        borderWidth: 1,
        titleColor: "#e5e7eb",
        bodyColor: "#cbd5f5",
        callbacks: {
          label: (ctx) =>
            `${labels[ctx.dataIndex]} • ${ctx.raw} dBm`,
        },
      },
    },

    scales: {
      y: {
        ticks: { color: "#cbd5f5" },
        grid: { color: "rgba(255,255,255,0.08)" },
      },
      x: {
        ticks: { display: false },
        grid: { display: false },
      },
    },
  };

  return (
    <div className="h-64">
      <Line data={data} options={options} />
    </div>
  );
}
