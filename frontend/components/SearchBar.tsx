interface SearchBarProps {
  defaultValue?: string;
  action?: string;
  placeholder?: string;
}

export function SearchBar({
  defaultValue,
  action = "/search",
  placeholder = "Search title or article text"
}: SearchBarProps) {
  return (
    <form action={action} className="flex flex-col gap-3 md:flex-row">
      <input
        type="search"
        name="q"
        defaultValue={defaultValue}
        placeholder={placeholder}
        aria-label="Search articles"
        className="min-w-0 flex-1 rounded-[1.4rem] border border-line bg-surface px-5 py-4 text-base text-text outline-none placeholder:text-muted"
      />
      <button type="submit" className="rounded-full bg-text px-6 py-4 text-sm text-page">
        Search
      </button>
    </form>
  );
}
