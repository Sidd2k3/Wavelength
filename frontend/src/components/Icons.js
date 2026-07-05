import React from "react";

const base = { width: 22, height: 22, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round", strokeLinejoin: "round" };

export function RocketIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" />
      <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 19 3a12.88 12.88 0 0 1-2.06 8A22.35 22.35 0 0 1 13 13z" />
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" />
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
    </svg>
  );
}

export function BriefcaseIcon(props) {
  return (
    <svg {...base} {...props}>
      <rect x="2.5" y="7.5" width="19" height="12" rx="2" />
      <path d="M8 7.5V6a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v1.5" />
      <path d="M2.5 12.5h19" />
    </svg>
  );
}

export function HammerIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M14.5 5.5l4 4" />
      <path d="M2.5 21.5l7-7" />
      <path d="M11 8.5L15.5 4a2.12 2.12 0 0 1 3 3L14 11.5z" />
      <path d="M9 10.5l4.5 4.5" />
    </svg>
  );
}

export function ChartIcon(props) {
  return (
    <svg {...base} {...props}>
      <path d="M4 20V10" />
      <path d="M11 20V4" />
      <path d="M18 20v-7" />
      <path d="M2.5 20h19" />
    </svg>
  );
}

export function GlobeIcon(props) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M2.5 12h19" />
      <path d="M12 2.5c2.5 2.7 3.9 6.1 3.9 9.5s-1.4 6.8-3.9 9.5c-2.5-2.7-3.9-6.1-3.9-9.5S9.5 5.2 12 2.5z" />
    </svg>
  );
}

export function ArrowLeftIcon(props) {
  return (
    <svg {...base} width={18} height={18} {...props}>
      <path d="M19 12H5" />
      <path d="M11 18l-6-6 6-6" />
    </svg>
  );
}

export function ExternalLinkIcon(props) {
  return (
    <svg {...base} width={15} height={15} {...props}>
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
      <path d="M15 3h6v6" />
      <path d="M10 14L21 3" />
    </svg>
  );
}

export function ICONS_BY_KEY_MAP() {
  return {
    rocket: RocketIcon,
    briefcase: BriefcaseIcon,
    hammer: HammerIcon,
    chart: ChartIcon,
    globe: GlobeIcon,
  };
}
