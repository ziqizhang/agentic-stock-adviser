import Markdown from "react-markdown";

interface Props {
  markdown: string;
}

export function ReportPane({ markdown }: Props) {
  if (!markdown) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No report yet
      </div>
    );
  }

  return (
    <div className="p-4 prose prose-invert prose-sm max-w-none">
      <Markdown>{markdown}</Markdown>
    </div>
  );
}
