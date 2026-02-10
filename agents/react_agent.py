from agents.tools import search_docs
from llm.ollama import OllamaLLM


SYSTEM_PROMPT = """You are an OpenStack troubleshooting assistant.

You use the ReAct pattern:
- Thought: analyze the symptom
- Action: search documentation if needed
- Observation: note relevant facts
- Final: explain likely causes and safe checks

Rules:
- You may search at most twice.
- If you have enough evidence to explain the issue, you MUST produce a Final answer.
- Documentation may explain mechanisms, not exact error messages.
- Do not include CLI commands or configuration snippets unless they are explicitly present in the retrieved documentation.
- Prefer explanation over remediation.
"""


class ReActAgent:
    def __init__(self, model: str | None = None):
        self.llm = OllamaLLM(model=model)

    def run(self, symptom: str, service: str | None = None):
        context = ""
        history = []

        for step in range(3):
            # --- Normal ReAct prompt ---
            prompt = f"""{SYSTEM_PROMPT}

Symptom:
{symptom}

Context so far:
{context}

Respond with ONE of the following formats:

Thought: ...
Action: search_docs(query="...", service="{service}")

OR

Final: ...
"""
            reply = self.llm.generate(prompt).strip()
            history.append(reply)

            # --- Final answer ---
            if reply.lower().startswith("final"):
                return reply, history

            # --- Tool call ---
            if "Action:" in reply:
                query = self._extract_query(reply)
                results = search_docs(query, service=service)

                obs = self._format_results(results)
                context += f"\nObservation:\n{obs}\n"

                # --- Force synthesis after evidence ---
                if step >= 1:
                    final_prompt = f"""{SYSTEM_PROMPT}

Symptom:
{symptom}

Evidence from documentation:
{context}

Based on the evidence above, provide a Final explanation.
Do NOT call any tools.
Respond only with:

Final: ...
"""
                    final_reply = self.llm.generate(final_prompt).strip()
                    history.append(final_reply)
                    return final_reply, history
            else:
                break

        return "Final: Unable to reach a grounded conclusion.", history

    def _extract_query(self, text: str) -> str:
        start = text.find('query="') + 7
        end = text.find('"', start)
        return text[start:end]

    def _format_results(self, results):
        out = []
        for r in results[:3]:
            out.append(
                f"- {r['service']} | {r['heading']}:\n  {r['text'][:300]}"
            )
        return "\n".join(out)
