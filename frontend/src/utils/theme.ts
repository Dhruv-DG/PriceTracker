// Platform color mapping
export const PLATFORM_COLORS: Record<string, string> = {
  'Amazon': '#ff9900',
  'Flipkart': '#2874f0',
  'Croma': '#0db750',
  'Reliance Digital': '#e42529',
  'Vijay Sales': '#e91e63',
};

export const CHART_COLORS = ['#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6'];

export function getPlatformColor(name: string, index: number = 0): string {
  return PLATFORM_COLORS[name] || CHART_COLORS[index % CHART_COLORS.length];
}
