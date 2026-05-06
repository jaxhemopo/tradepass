export const brand = {
  name: "SparkyPass",
  tagline: "Pass your sparky exam with confidence",
  colors: {
    primary: "TODO",
    accent: "TODO",
  },
  regulations: ["AS/NZS 3000", "ESR 2010"],
} as const;

export type Brand = typeof brand;
