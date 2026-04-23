import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { SimTimeseries } from "@/types/api";

type Channel = "speed" | "rpm" | "accel" | "power";

const CHANNEL_META: Record<
  Channel,
  { label: string; unit: string; color: string; key: keyof SimTimeseries }
> = {
  speed: {
    label: "Velocity",
    unit: "km/h",
    color: "#f97316",
    key: "v_kmh",
  },
  rpm: {
    label: "Engine RPM",
    unit: "rpm",
    color: "#38bdf8",
    key: "rpm",
  },
  accel: {
    label: "Longitudinal g",
    unit: "g",
    color: "#a3e635",
    key: "accel_g",
  },
  power: {
    label: "Power",
    unit: "kW",
    color: "#e879f9",
    key: "power_kw",
  },
};

interface Props {
  timeseries: SimTimeseries;
  channel: Channel;
  etMark?: number;
}

export function SimChart({ timeseries, channel, etMark }: Props) {
  const meta = CHANNEL_META[channel];
  const values = timeseries[meta.key] as number[] | undefined;
  const times = timeseries.t_s;
  if (!values || !times || values.length === 0) {
    return (
      <div className="h-56 flex items-center justify-center text-carbon-500 text-sm">
        No data.
      </div>
    );
  }
  const points = times.map((t, i) => ({ t, v: values[i] }));

  return (
    <div className="h-56">
      <div className="flex items-baseline justify-between mb-2">
        <div className="text-xs uppercase tracking-wider text-carbon-500">
          {meta.label}
        </div>
        <div className="text-[10px] text-carbon-600">{meta.unit}</div>
      </div>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid strokeDasharray="2 4" stroke="#1e293b" />
          <XAxis
            dataKey="t"
            type="number"
            domain={["dataMin", "dataMax"]}
            tickFormatter={(v) => v.toFixed(1)}
            stroke="#475569"
            fontSize={10}
          />
          <YAxis stroke="#475569" fontSize={10} width={40} />
          <Tooltip
            contentStyle={{
              background: "#0f172a",
              border: "1px solid #1e293b",
              fontSize: 11,
            }}
            formatter={(v: number) => [v.toFixed(2), meta.unit]}
            labelFormatter={(t: number) => `t=${t.toFixed(3)} s`}
          />
          {etMark != null && (
            <ReferenceLine
              x={etMark}
              stroke="#f97316"
              strokeDasharray="3 3"
              label={{
                value: `ET ${etMark.toFixed(3)}s`,
                fill: "#f97316",
                fontSize: 10,
                position: "insideTopRight",
              }}
            />
          )}
          <Line
            type="monotone"
            dataKey="v"
            stroke={meta.color}
            strokeWidth={1.8}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export const SIM_CHANNELS: Channel[] = ["speed", "rpm", "accel", "power"];
