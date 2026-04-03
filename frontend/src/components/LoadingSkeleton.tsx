import "./LoadingSkeleton.css";

export default function LoadingSkeleton() {
  return (
    <div className="skeleton-list">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton-line skeleton-title" />
          <div className="skeleton-line skeleton-short" />
          <div className="skeleton-line skeleton-medium" />
          <div className="skeleton-line skeleton-short" />
        </div>
      ))}
    </div>
  );
}
