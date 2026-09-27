import Link from "next/link";

import RunsTable from "@/components/RunsTable";
import { Card, Empty } from "@/components/ui";
import { getRuns } from "@/lib/api";

export default async function RunsPage(props: PageProps<"/runs">) {
  const { experiment_id } = await props.searchParams;
  const experimentId = typeof experiment_id === "string" ? experiment_id : undefined;
  const runs = await getRuns(experimentId);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-xl font-semibold">{experimentId ? `Runs in experiment #${experimentId}` : "All runs"}</h1>
        {experimentId && (
          <Link href="/runs" className="text-sm text-series-1 hover:underline">
            show all runs
          </Link>
        )}
      </div>
      <Card>{runs.length > 0 ? <RunsTable runs={runs} /> : <Empty>No runs found.</Empty>}</Card>
    </div>
  );
}
