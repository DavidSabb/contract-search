import type { SourceFilter, SortOrder, SourceCounts } from "../hooks/useContractSearch";
import "./SearchFilters.css";

interface Props {
  activeSourceFilter: SourceFilter;
  onSourceFilterChange: (filter: SourceFilter) => void;
  sortOrder: SortOrder;
  onSortChange: (sort: SortOrder) => void;
  sourceCounts: SourceCounts;
  totalResults: number;
}

const SOURCE_OPTIONS: { value: SourceFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "procuredata", label: "\u{1F1E8}\u{1F1E6} ProcureData" },
  { value: "open_canada", label: "\u{1F1E8}\u{1F1E6} Open Canada" },
  { value: "sam_gov", label: "\u{1F1FA}\u{1F1F8} SAM.gov" },
  { value: "usa_spending", label: "\u{1F1FA}\u{1F1F8} USASpending" },
];

export default function SearchFilters({
  activeSourceFilter,
  onSourceFilterChange,
  sortOrder,
  onSortChange,
  sourceCounts,
  totalResults,
}: Props) {
  const activeSources = Object.values(sourceCounts).filter((c) => c > 0).length;

  return (
    <div className="search-filters">
      <div className="filter-row">
        <div className="source-pills">
          {SOURCE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              className={`pill ${activeSourceFilter === opt.value ? "active" : ""}`}
              onClick={() => onSourceFilterChange(opt.value)}
            >
              {opt.label}
              {opt.value !== "all" && sourceCounts[opt.value as keyof SourceCounts] > 0 && (
                <span className="pill-count">{sourceCounts[opt.value as keyof SourceCounts]}</span>
              )}
            </button>
          ))}
        </div>
        <select
          className="sort-select"
          value={sortOrder}
          onChange={(e) => onSortChange(e.target.value as SortOrder)}
        >
          <option value="best_match">Best Match</option>
          <option value="newest">Newest First</option>
          <option value="highest_value">Highest Value</option>
          <option value="lowest_value">Lowest Value</option>
        </select>
      </div>
      <p className="results-summary">
        Showing {totalResults} results across {activeSources} source{activeSources !== 1 ? "s" : ""}
      </p>
    </div>
  );
}
