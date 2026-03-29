import { useEffect, useRef } from "react";
import { useStore } from "../store";

interface SSEEventData {
  type: string;
  data: Record<string, unknown>;
}

export function useSSE(sessionId: string) {
  const sourceRef = useRef<EventSource | null>(null);

  const appendAssistantToken = useStore((s) => s.appendAssistantToken);
  const addStatusMessage = useStore((s) => s.addStatusMessage);
  const finishAssistantMessage = useStore((s) => s.finishAssistantMessage);
  const setAgentTyping = useStore((s) => s.setAgentTyping);
  const openStock = useStore((s) => s.openStock);
  const updateChart = useStore((s) => s.updateChart);
  const updateFundamentals = useStore((s) => s.updateFundamentals);
  const updateReport = useStore((s) => s.updateReport);

  useEffect(() => {
    const source = new EventSource(`/stream/${sessionId}`);
    sourceRef.current = source;

    let wasTyping = false;

    source.onmessage = (event) => {
      let parsed: SSEEventData;
      try {
        parsed = JSON.parse(event.data);
      } catch {
        return;
      }

      const { type, data } = parsed;

      switch (type) {
        case "token":
          if (!wasTyping) {
            wasTyping = true;
          }
          appendAssistantToken(data.content as string);
          break;

        case "tool_start":
          if (wasTyping) {
            finishAssistantMessage();
            wasTyping = false;
          }
          setAgentTyping(true);
          addStatusMessage(data.status as string);
          break;

        case "tool_result":
          break;

        case "stock_opened":
          openStock(data.symbol as string, data.name as string);
          break;

        case "chart_update":
          updateChart(
            data.symbol as string,
            data.prices as number[],
            data.period as string
          );
          break;

        case "table_update":
          updateFundamentals(
            data.symbol as string,
            data.metrics as Record<string, number | null>
          );
          break;

        case "report_update":
          updateReport(data.symbol as string, data.markdown as string);
          break;

        case "done":
          if (wasTyping) {
            finishAssistantMessage();
            wasTyping = false;
          }
          setAgentTyping(false);
          break;
      }
    };

    source.onerror = () => {
      if (wasTyping) {
        finishAssistantMessage();
        wasTyping = false;
      }
      setAgentTyping(false);
    };

    return () => {
      source.close();
    };
  }, [sessionId]);
}
