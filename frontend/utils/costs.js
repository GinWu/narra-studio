const toFiniteNumber = (value, fallback = 0) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

const normalizeCostItem = (item = {}) => {
  const estimatedTotalCost = toFiniteNumber(
    item.estimated_total_cost ?? item.estimated_cost_total ?? item.total_cost,
    0
  );
  const currency = item.currency || 'USD';
  const capabilityType = item.capability_type || item.capability || currency;

  return {
    ...item,
    capability_type: capabilityType,
    currency,
    estimated_total_cost: estimatedTotalCost,
    known_cost_count: toFiniteNumber(item.known_cost_count ?? item.count, 0),
    unknown_cost_count: toFiniteNumber(item.unknown_cost_count, 0)
  };
};

export const normalizeCostSummary = (summary = {}) => {
  const safeSummary = summary && typeof summary === 'object' ? summary : {};
  const sourceItems = Array.isArray(safeSummary.items)
    ? safeSummary.items
    : Array.isArray(safeSummary.by_currency)
      ? safeSummary.by_currency
      : [];

  return {
    ...safeSummary,
    items: sourceItems.map(normalizeCostItem),
    record_count: toFiniteNumber(safeSummary.record_count, 0),
    unknown_cost_count: toFiniteNumber(safeSummary.unknown_cost_count, 0)
  };
};

export const sumEstimatedCosts = (items = []) => {
  if (!Array.isArray(items)) return 0;
  return items.reduce((sum, item) => sum + toFiniteNumber(item?.estimated_total_cost, 0), 0);
};
