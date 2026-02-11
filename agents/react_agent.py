from agents.tools import search_docs
from llm.ollama import OllamaLLM
import re


SYSTEM_PROMPT = """You are an OpenStack troubleshooting assistant.

You MUST reason step-by-step using the following format:

Thought: your reasoning about the symptom
Action: search_docs(query="...", service="...")   (if you need documentation)
Observation: summary of retrieved evidence
Final: grounded explanation strictly based on evidence

Rules:
- You may search at most twice.
- You MUST search before producing Final.
- You MUST use retrieved evidence in your explanation.
- Do NOT provide generic explanations.
- If evidence is insufficient, say so.
- Do NOT invent configuration or causes.
- If evidence spans multiple services, you MUST explain how those services interact.
- You MUST describe causal relationships between services if applicable.
"""


class ReActAgent:
    def __init__(self, model=None, debug=False):
        self.model = model
        self.debug = debug
        self.llm = OllamaLLM(model=model)

    def run(self, symptom: str, service: str | None = None):
        evidence_found = False
        context = ""
        history = []

        for step in range(2):
            prompt = f"""{SYSTEM_PROMPT}

    Symptom:
    {symptom}

    Evidence from documentation:
    {context}

    Instructions:
    - You MUST base your answer strictly on the evidence above.
    - You MUST explicitly reference specific behaviors described in the evidence.
    - If the evidence does not explain the issue, say:
    "The retrieved documentation does not describe this failure mode."

    Respond with ONE of the following formats:

    Thought: ...
    Action: search_docs(query="...", service="{service}")

    OR

    Final: ...
    """

            if self.debug:
                print("\n[DEBUG] ===== LLM PROMPT =====\n")
                print(prompt[:800])

            reply = self.llm.generate(prompt).strip()
            history.append(reply)

            if self.debug:
                print("\n[DEBUG] ===== LLM REPLY =====\n")
                print(reply)

            # --- Handle Final FIRST ---
            match = re.search(r'final:\s*(.*)', reply, re.IGNORECASE | re.DOTALL)
            if match:
                final_part = "Final: " + match.group(1).strip()
                if not evidence_found:
                    return "Final: No relevant documentation was retrieved to support a grounded conclusion.", history
                return final_part.strip(), history

            # --- Tool call ---
            if "action:" in reply.lower():
                query = self._extract_query(reply)

                expanded_query = query

                if self.debug:
                    print("\n[DEBUG] Search query:", expanded_query)

                results = search_docs(expanded_query, service=service)

                if results:
                    evidence_found = True

                if self.debug:
                    if isinstance(results, dict):
                        total = sum(len(v) for v in results.values())
                    else:
                        total = len(results)

                    print(f"[DEBUG] Retrieved {total} results")

                obs = self._format_results(results)
                context += f"\nObservation:\n{obs}\n"

                if step >= 1:
                    final_prompt = f"""{SYSTEM_PROMPT}

    Symptom:
    {symptom}

    Evidence from documentation:
    {context}

    Based strictly on the evidence above:

    - You MUST reference specific phrases from the excerpts.
    - You MUST explain which excerpt supports each claim.
    - If no excerpt explicitly describes this failure mode, say so.

    Respond only with:

    Final: ...
    """
                    if not evidence_found:
                        return "Final: No relevant documentation was retrieved to support a grounded conclusion.", history

                    final_reply = self.llm.generate(final_prompt).strip()
                    history.append(final_reply)
                    return final_reply, history


        return "Final: Unable to reach a grounded conclusion.", history

    def _extract_query(self, text: str) -> str:
        match = re.search(r'query\s*=\s*"([^"]+)"', text)
        return match.group(1) if match else text
    
    def _format_results(self, results):
        """
        Supports:
        - Multi-service: Dict[str, List[dict]]
        - Single-service (legacy): List[dict]
        """

        out = []

        # --- Multi-service mode ---
        if isinstance(results, dict):
            for svc, svc_results in results.items():
                out.append(f"\n=== Service: {svc.upper()} ===\n")

                for r in svc_results[:3]:
                    out.append(
                        f"""Source: {r.get('source')}
    Service: {r.get('service')}
    Score: {r.get('score'):.3f}

    Excerpt:
    \"\"\"{r['text'][:800]}\"\"\"
    """
                    )

            return "\n---\n".join(out)

        # --- Flat list (backward compatibility) ---
        if isinstance(results, list):
            for r in results[:3]:
                out.append(
                    f"""Source: {r.get('source')}
    Service: {r.get('service')}
    Score: {r.get('score'):.3f}

    Excerpt:
    \"\"\"{r['text'][:800]}\"\"\"
    """
                )

            return "\n---\n".join(out)

        return ""

