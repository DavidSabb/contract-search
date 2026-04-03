import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";

export interface Contract {
  id: string;
  title: string;
  description: string;
  value: number | null;
  currency: string;
  awarded_date: string | null;
  close_date: string | null;
  vendor: string | null;
  department: string;
  country: string;
  source: string;
  url: string | null;
  relevance_score?: number;
  matched_terms?: string[];
  status?: string;
  is_active?: boolean;
}

export interface SourceCounts {
  procuredata: number;
  open_canada: number;
  sam_gov: number;
  usa_spending: number;
}

export type SourceFilter = "all" | "procuredata" | "open_canada" | "sam_gov" | "usa_spending";
export type SortOrder = "best_match" | "newest" | "highest_value" | "lowest_value";

export function useContractSearch() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [query, setQuery] = useState(searchParams.get("q") || "");
  const [results, setResults] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(Number(searchParams.get("page")) || 1);
  const [totalResults, setTotalResults] = useState(0);
  const [sourceCounts, setSourceCounts] = useState<SourceCounts>({
    procuredata: 0,
    open_canada: 0,
    sam_gov: 0,
    usa_spending: 0,
  });
  const [activeSourceFilter, setActiveSourceFilter] = useState<SourceFilter>("all");
  const [sortOrder, setSortOrder] = useState<SortOrder>("best_match");
  const [message, setMessage] = useState<string | null>(null);
  const [suggestedTerms, setSuggestedTerms] = useState<string[]>([]);
  const [showClosed, setShowClosed] = useState(false);

  const search = useCallback(
    async (searchQuery: string, searchPage: number, includeClosed?: boolean) => {
      if (searchQuery.trim().length < 2) return;

      const closed = includeClosed ?? showClosed;

      setLoading(true);
      setError(null);

      setSearchParams({ q: searchQuery, page: String(searchPage) });

      try {
        const response = await fetch("/api/contracts/search/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: searchQuery, page: searchPage, show_closed: closed }),
        });

        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.error || `Search failed (${response.status})`);
        }

        const data = await response.json();
        setResults(data.results);
        setTotalResults(data.total);
        setSourceCounts(data.sources);
        setMessage(data.message || null);
        setSuggestedTerms(data.suggested_terms || []);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Search failed");
        setResults([]);
        setMessage(null);
        setSuggestedTerms([]);
      } finally {
        setLoading(false);
      }
    },
    [setSearchParams, showClosed]
  );

  // Auto-search from URL params on mount
  useEffect(() => {
    const q = searchParams.get("q");
    const p = Number(searchParams.get("page")) || 1;
    if (q && q.trim().length >= 2) {
      setQuery(q);
      setPage(p);
      search(q, p);
    }
    // Only run on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = useCallback(
    (q: string) => {
      setPage(1);
      setQuery(q);
      search(q, 1);
    },
    [search]
  );

  const handlePageChange = useCallback(
    (newPage: number) => {
      setPage(newPage);
      search(query, newPage);
    },
    [search, query]
  );

  const handleToggleClosed = useCallback(
    (value: boolean) => {
      setShowClosed(value);
      if (query.trim().length >= 2) {
        setPage(1);
        search(query, 1, value);
      }
    },
    [search, query]
  );

  // Client-side filtering and sorting
  const filteredResults = results
    .filter((r) => activeSourceFilter === "all" || r.source === activeSourceFilter)
    .sort((a, b) => {
      if (sortOrder === "best_match") {
        return (b.relevance_score ?? 0) - (a.relevance_score ?? 0);
      }
      if (sortOrder === "highest_value") {
        return (b.value ?? 0) - (a.value ?? 0);
      }
      if (sortOrder === "lowest_value") {
        return (a.value ?? 0) - (b.value ?? 0);
      }
      // newest
      const aDate = a.awarded_date || a.close_date || "";
      const bDate = b.awarded_date || b.close_date || "";
      return bDate.localeCompare(aDate);
    });

  return {
    query,
    setQuery,
    results: filteredResults,
    allResults: results,
    loading,
    error,
    page,
    totalResults,
    sourceCounts,
    activeSourceFilter,
    setActiveSourceFilter,
    sortOrder,
    setSortOrder,
    message,
    suggestedTerms,
    showClosed,
    handleToggleClosed,
    handleSearch,
    handlePageChange,
  };
}
