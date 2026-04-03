import { useState, type KeyboardEvent } from "react";
import { useContractSearch } from "../hooks/useContractSearch";
import ContractCard from "./ContractCard";
import SearchFilters from "./SearchFilters";
import LoadingSkeleton from "./LoadingSkeleton";
import "./ContractSearch.css";

export default function ContractSearch() {
  const {
    query,
    setQuery,
    results,
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
  } = useContractSearch();

  const [inputValue, setInputValue] = useState(query);

  const onSubmit = () => {
    if (inputValue.trim().length >= 2) {
      handleSearch(inputValue.trim());
    }
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") onSubmit();
  };

  return (
    <div className="contract-search">
      <div className="search-header">
        <h1>Government Contract Search</h1>
        <p className="subtitle">
          Search across Canadian and US federal procurement databases
        </p>
      </div>

      <div className="search-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Search government contracts (e.g. packaging, IT, construction...)"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <button className="search-button" onClick={onSubmit} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      <div className="active-toggle-row">
        <label className="toggle-label">
          <span className="toggle-switch">
            <input
              type="checkbox"
              checked={showClosed}
              onChange={(e) => handleToggleClosed(e.target.checked)}
            />
            <span className="toggle-slider" />
          </span>
          <span className="toggle-text">
            {showClosed ? "Include Closed" : "Active Only"}
          </span>
        </label>
        <span className="toggle-hint">
          {showClosed
            ? ""
            : "Showing active contracts only. Toggle to include closed/completed contracts."}
        </span>
      </div>

      {showClosed && totalResults > 0 && !loading && (
        <div className="closed-warning">
          Showing all contracts including closed and completed ones
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {totalResults > 0 && !loading && (
        <SearchFilters
          activeSourceFilter={activeSourceFilter}
          onSourceFilterChange={setActiveSourceFilter}
          sortOrder={sortOrder}
          onSortChange={setSortOrder}
          sourceCounts={sourceCounts}
          totalResults={totalResults}
        />
      )}

      {loading && <LoadingSkeleton />}

      {!loading && results.length > 0 && (
        <div className="results-list">
          {results.map((contract) => (
            <ContractCard key={contract.id} contract={contract} />
          ))}
        </div>
      )}

      {!loading && totalResults > 0 && results.length === 0 && (
        <div className="no-results">
          No results match the selected filter. Try selecting "All" sources.
        </div>
      )}

      {!loading && query && totalResults === 0 && !error && (
        <div className="no-results">
          {message || `No contracts found for "${query}". Try a different search term.`}
          {suggestedTerms.length > 0 && (
            <div className="suggested-terms">
              <p>Try these related terms:</p>
              <div className="suggestion-chips">
                {suggestedTerms.map((term) => (
                  <button
                    key={term}
                    className="suggestion-chip"
                    onClick={() => {
                      setInputValue(term);
                      handleSearch(term);
                    }}
                  >
                    {term}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && totalResults > 0 && (
        <div className="pagination">
          <button
            className="page-button"
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1}
          >
            &larr; Previous
          </button>
          <span className="page-info">Page {page}</span>
          <button
            className="page-button"
            onClick={() => handlePageChange(page + 1)}
            disabled={results.length < 20}
          >
            Next &rarr;
          </button>
        </div>
      )}
    </div>
  );
}
