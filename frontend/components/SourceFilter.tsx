import { Source } from "@/lib/types";
import { titleCase } from "@/lib/utils";

interface SourceFilterProps {
  sources: Source[];
  currentSource?: string;
  currentCategory?: string;
}

export function SourceFilter({
  sources,
  currentSource,
  currentCategory
}: SourceFilterProps) {
  const categories = Array.from(new Set(sources.map((source) => source.category))).sort();

  return (
    <div className="flex flex-col gap-3 rounded-[1.4rem] border border-line/70 bg-surface p-4 md:flex-row md:items-center">
      <label className="flex flex-1 flex-col gap-2 text-sm text-muted">
        <span>Source</span>
        <select
          name="source"
          defaultValue={currentSource || ""}
          className="rounded-2xl border border-line bg-page px-4 py-3 text-text outline-none"
        >
          <option value="">All sources</option>
          {sources.map((source) => (
            <option key={source.id} value={source.id}>
              {source.name}
            </option>
          ))}
        </select>
      </label>
      <label className="flex flex-1 flex-col gap-2 text-sm text-muted">
        <span>Category</span>
        <select
          name="category"
          defaultValue={currentCategory || ""}
          className="rounded-2xl border border-line bg-page px-4 py-3 text-text outline-none"
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {titleCase(category)}
            </option>
          ))}
        </select>
      </label>
      <div className="pt-2 md:self-end md:pt-0">
        <button type="submit" className="rounded-full bg-text px-5 py-3 text-sm text-page">
          Apply
        </button>
      </div>
    </div>
  );
}
