export function AssumptionsPanel({
  assumptions,
  title = "How this was calculated",
}: {
  assumptions: string[];
  title?: string;
}) {
  return (
    <details className="assumptions">
      <summary>{title}</summary>
      <ul>
        {assumptions.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </details>
  );
}
