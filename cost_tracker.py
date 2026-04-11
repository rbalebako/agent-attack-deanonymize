from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CostTracker:
    """
    Accumulates LLM token usage across all agent calls in a single run.

    Pricing constants are for Gemini 2.0 Flash (USD per 1M tokens).
    Update if switching models — see https://ai.google.dev/pricing
    """

    # Gemini 2.0 Flash pricing (USD / 1M tokens)
    INPUT_COST_PER_M_USD: float = 0.075
    OUTPUT_COST_PER_M_USD: float = 0.30

    input_tokens: int = 0
    output_tokens: int = 0
    agent_calls: Dict[str, int] = field(default_factory=dict)

    def record_usage(self, agent_name: str, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.agent_calls[agent_name] = self.agent_calls.get(agent_name, 0) + 1

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        input_cost = (self.input_tokens / 1_000_000) * self.INPUT_COST_PER_M_USD
        output_cost = (self.output_tokens / 1_000_000) * self.OUTPUT_COST_PER_M_USD
        return round(input_cost + output_cost, 6)

    @property
    def total_agent_calls(self) -> int:
        return sum(self.agent_calls.values())

    def report(self) -> str:
        lines = [
            f"Input tokens:   {self.input_tokens:,}",
            f"Output tokens:  {self.output_tokens:,}",
            f"Total tokens:   {self.total_tokens:,}",
            f"Estimated cost: ${self.estimated_cost_usd:.6f} USD",
            f"Agent calls:    {dict(self.agent_calls)}",
            f"Total calls:    {self.total_agent_calls}",
        ]
        return "\n".join(lines)
