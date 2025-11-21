"""LLM-driven synthesis for Polyseek Sentient."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

try:
    from litellm import acompletion
except ImportError:  # pragma: no cover
    acompletion = None  # type: ignore

from .config import Settings, load_settings
from .fetch_market import MarketData
from .scrape_context import MarketContext
from .signals_client import SignalRecord


@dataclass
class AnalysisRequest:
    market: MarketData
    context: MarketContext
    signals: List[SignalRecord]
    depth: str
    perspective: str


async def run_analysis(
    request: AnalysisRequest,
    settings: Optional[Settings] = None,
) -> Dict:
    """Invoke the LLM to compute verdict / drivers / sources.
    
    For 'quick' mode: Single-pass analysis.
    For 'deep' mode: Planner → Critic → Follow-up → Final (4-step analysis).
    """
    settings = settings or load_settings()
    if settings.app.offline_mode or acompletion is None or not settings.llm.api_key:
        return _offline_analysis(request)

    if request.depth == "deep":
        return await _run_deep_analysis(request, settings)
    else:
        return await _run_quick_analysis(request, settings)


async def _run_quick_analysis(
    request: AnalysisRequest,
    settings: Settings,
) -> Dict:
    """Quick mode: Single-pass analysis."""
    system_prompt = (
        "You are Polyseek Sentient, a rigorous prediction market analyst. "
        "You must analyze provided market data, comments, and external signals. "
        "Follow instructions precisely, cite source IDs, and output valid JSON."
    )
    user_prompt = _build_user_prompt(request)
    response = await acompletion(
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
        response_format={"type": "json_object"},
    )
    content = response["choices"][0]["message"]["content"]
    
    # Try direct JSON parse first (most common case)
    import json
    try:
        # Clean the content
        cleaned_content = content.strip()
        # Remove markdown code blocks if present
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:].strip()
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:].strip()
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3].strip()
        
        # Try to parse directly
        direct_parse = json.loads(cleaned_content)
        if isinstance(direct_parse, dict) and all(field in direct_parse for field in ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]):
            result = direct_parse
        else:
            # Missing required fields, use fallback parser
            result = _parse_response_json(content)
    except (json.JSONDecodeError, ValueError) as e:
        # JSON parse failed, use fallback parser
        result = _parse_response_json(content)
    
    # Ensure result is a dict
    if not isinstance(result, dict):
        result = {}
    
    # Validate that result has required fields
    required_fields = ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        # Return fallback structure
        result = {
            "verdict": "UNCERTAIN",
            "confidence_pct": 50.0,
            "summary": f"LLM returned invalid response structure. Expected fields: {required_fields}",
            "key_drivers": [
                {
                    "text": "LLM response format error",
                    "source_ids": ["SRC_FORMAT_ERROR"],
                }
            ],
            "uncertainty_factors": ["LLM response did not match expected format"],
            "sources": [
                {
                    "id": "SRC_FORMAT_ERROR",
                    "title": "Format Error",
                    "url": "",
                    "type": "news",
                    "sentiment": "neutral",
                }
            ],
        }
    
    result["metadata"] = result.get("metadata", {})
    result["metadata"]["mode"] = "quick"
    return result


async def _run_deep_analysis(
    request: AnalysisRequest,
    settings: Settings,
) -> Dict:
    """Deep mode: Planner → Critic → Follow-up → Final (4-step analysis)."""
    system_prompt = (
        "You are Polyseek Sentient, a rigorous prediction market analyst. "
        "You must analyze provided market data, comments, and external signals. "
        "Follow instructions precisely, cite source IDs, and output valid JSON."
    )
    
    # Step 1: Planner - Create analysis plan
    planner_prompt = _build_planner_prompt(request)
    planner_response = await acompletion(
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": planner_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    plan = _parse_response_json(planner_response["choices"][0]["message"]["content"])
    
    # Step 2: Critic - Critically evaluate the plan and identify gaps
    critic_prompt = _build_critic_prompt(request, plan)
    critic_response = await acompletion(
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": critic_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )
    critique = _parse_response_json(critic_response["choices"][0]["message"]["content"])
    
    # Step 3: Follow-up - Gather additional data if gaps identified
    additional_signals = list(request.signals)  # Copy original signals
    # Note: In a full implementation, we would use follow_up_queries to search for additional information
    # For now, we use the comprehensive signals already gathered
    # Future enhancement: Implement targeted follow-up searches based on critique
    
    # Step 4: Final - Perform final analysis with all data
    final_request = AnalysisRequest(
        market=request.market,
        context=request.context,
        signals=additional_signals,
        depth="deep",
        perspective=request.perspective,
    )
    final_prompt = _build_final_prompt(final_request, plan, critique)
    final_response = await acompletion(
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt},
        ],
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens * 2,  # Allow more tokens for deep analysis
        response_format={"type": "json_object"},
    )
    result = _parse_response_json(final_response["choices"][0]["message"]["content"])
    result["metadata"] = result.get("metadata", {})
    result["metadata"]["mode"] = "deep"
    result["metadata"]["plan"] = plan.get("analysis_plan", [])
    result["metadata"]["critique"] = {
        "gaps": critique.get("gaps", []),
        "follow_up_queries": critique.get("follow_up_queries", []),
    }
    return result


def _build_planner_prompt(request: AnalysisRequest) -> str:
    """Build prompt for planning phase."""
    market = request.market
    context = request.context
    rules = context.resolution_rules or "N/A"
    signals_summary = f"{len(request.signals)} external signals available"
    
    return f"""
You are planning a deep analysis of a prediction market. Create an analysis plan.

Market:
- Title: {market.title}
- Category: {market.category}
- Deadline UTC: {market.deadline}
- Prices: YES={market.prices.yes} NO={market.prices.no}
- Resolution rules: {rules}
- External signals: {signals_summary}

Respond with JSON containing:
{{
  "analysis_plan": [
    "Step 1: Analyze market fundamentals",
    "Step 2: Evaluate external evidence",
    "Step 3: Assess uncertainty factors",
    ...
  ],
  "key_questions": [
    "What are the main factors driving this market?",
    "What evidence supports YES vs NO?",
    ...
  ],
  "information_gaps": [
    "Missing data about X",
    "Need more information about Y",
    ...
  ]
}}
"""


def _build_critic_prompt(request: AnalysisRequest, plan: Dict) -> str:
    """Build prompt for critic phase."""
    market = request.market
    plan_str = json.dumps(plan, indent=2)
    signals_summary = "\n".join(
        f"- {s.source_type}:{s.source} [{s.sentiment}] {s.title[:60]}"
        for s in request.signals[:10]
    ) or "No external signals available."
    
    return f"""
You are critically evaluating an analysis plan for a prediction market.

Market: {market.title}
Current plan:
{plan_str}

Available signals:
{signals_summary}

Critically evaluate the plan and identify:
1. Gaps in the analysis
2. Missing information that should be gathered
3. Potential biases or assumptions
4. Areas that need deeper investigation

Respond with JSON containing:
{{
  "gaps": [
    "Gap 1: Missing information about X",
    "Gap 2: Need to verify Y",
    ...
  ],
  "follow_up_queries": [
    "Additional search query 1",
    "Additional search query 2",
    ...
  ],
  "biases": [
    "Potential bias 1",
    ...
  ],
  "recommendations": [
    "Recommendation 1",
    ...
  ]
}}
"""


def _build_final_prompt(request: AnalysisRequest, plan: Dict, critique: Dict) -> str:
    """Build prompt for final analysis phase."""
    market = request.market
    context = request.context
    rules = context.resolution_rules or "N/A"
    comments_block = "\n".join(
        f"- ({c.sentiment}) [{c.comment_id}] {c.body[:200]}"
        for c in context.comments
    ) or "No on-platform discussion available."
    signals_block = "\n".join(
        f"- {s.source_type}:{s.source} [{s.sentiment}] ({s.url}) {s.title}"
        for s in request.signals
    ) or "No external signals were retrieved."
    
    plan_summary = json.dumps(plan.get("analysis_plan", []), indent=2)
    critique_summary = json.dumps({
        "gaps": critique.get("gaps", []),
        "recommendations": critique.get("recommendations", []),
    }, indent=2)
    
    return f"""
You are performing the FINAL deep analysis of a prediction market. You have:
1. Created an analysis plan
2. Critically evaluated it and identified gaps
3. Gathered additional information

Now perform the final comprehensive analysis.

Market:
- Title: {market.title}
- Category: {market.category}
- Deadline UTC: {market.deadline}
- Prices: YES={market.prices.yes} NO={market.prices.no}
- Liquidity: {market.liquidity}
- Volume 24h: {market.volume_24h}
- Resolution rules: {rules}

Analysis Plan:
{plan_summary}

Critique Findings:
{critique_summary}

Platform comments:
{comments_block}

External signals (including follow-up research):
{signals_block}

Operating mode:
- Depth: deep
- Perspective: {request.perspective}

Perform a comprehensive analysis considering:
1. The original plan
2. The critique findings
3. All available evidence (original + follow-up)
4. Both pro and con arguments
5. Uncertainty factors

Respond with valid JSON containing:
- verdict: "YES" | "NO" | "UNCERTAIN"
- confidence_pct: number between 0-100
- summary: comprehensive analysis summary
- key_drivers: array of objects with "text" and "source_ids", maximum 3 items
- uncertainty_factors: array of strings
- next_steps: optional array of strings
- sources: array of objects with "id", "title", "url", "type", "sentiment"

IMPORTANT: 
- This is a DEEP analysis - be thorough and consider all angles
- Cite source IDs in key_drivers
- sources[].type must be "market", "comment", "sns", or "news"
- Include at least one source
- If evidence is insufficient, verdict MUST be UNCERTAIN
"""


def _build_user_prompt(request: AnalysisRequest) -> str:
    market = request.market
    context = request.context
    rules = context.resolution_rules or "N/A"
    comments_block = "\n".join(
        f"- ({c.sentiment}) [{c.comment_id}] {c.body[:200]}"
        for c in context.comments
    ) or "No on-platform discussion available."
    signals_block = "\n".join(
        f"- {s.source_type}:{s.source} [{s.sentiment}] ({s.url}) {s.title}"
        for s in request.signals
    ) or "No external signals were retrieved."

    return f"""
You must analyze a prediction market and respond with valid JSON containing EXACTLY these fields:
- verdict: "YES" | "NO" | "UNCERTAIN" (required)
- confidence_pct: number between 0-100 (required)
- summary: string describing your analysis (required)
- key_drivers: array of objects, each with "text" (string) and "source_ids" (array of strings), maximum 3 items (required)
- uncertainty_factors: array of strings (required)
- next_steps: optional array of strings
- sources: array of objects, each with "id" (string), "title" (string), "url" (string), "type" ("market"|"comment"|"sns"|"news"), "sentiment" ("pro"|"con"|"neutral"), optional "timestamp" (string) (required)

CRITICAL REQUIREMENTS:
- You MUST return a JSON object with ALL required fields listed above
- Do NOT return a partial response or a different structure
- key_drivers must be an array of objects, not strings. Each object must have "text" and "source_ids" fields.
- sources[].type must be exactly one of: "market", "comment", "sns", or "news" (not "prediction_market" or other values)
- Include at least one source.
- The JSON must be valid and complete

Market:
- Title: {market.title}
- Category: {market.category}
- Deadline UTC: {market.deadline}
- Prices: YES={market.prices.yes} NO={market.prices.no}
- Liquidity: {market.liquidity}
- Volume 24h: {market.volume_24h}
- Resolution rules: {rules}

Operating mode:
- Depth: {request.depth}
- Perspective: {request.perspective}

Platform comments:
{comments_block}

External signals:
{signals_block}

Instructions:
1. Consider BOTH pro and con evidence. Devil's advocate mode requires at least two counter arguments.
2. Base prior probability on current YES price; adjust via likelihood style reasoning.
3. Cite source IDs in key_drivers using the provided IDs or synthetic ones for generated sources.
4. Always include at least one uncertainty factor. If evidence is insufficient, verdict MUST be UNCERTAIN.
5. Format key_drivers as: [{{"text": "...", "source_ids": ["SRC1"]}}, ...]
6. Format sources as: [{{"id": "SRC1", "title": "...", "url": "...", "type": "market", "sentiment": "neutral"}}, ...]

Example JSON structure (YOU MUST FOLLOW THIS EXACT STRUCTURE):
{{
  "verdict": "UNCERTAIN",
  "confidence_pct": 50.0,
  "summary": "Your comprehensive analysis summary here",
  "key_drivers": [
    {{"text": "Driver description", "source_ids": ["SRC1", "SRC2"]}}
  ],
  "uncertainty_factors": ["Factor 1"],
  "next_steps": ["Optional step 1"],
  "sources": [
    {{"id": "SRC1", "title": "Source title", "url": "https://...", "type": "market", "sentiment": "neutral"}}
  ]
}}

REMEMBER: You MUST return a complete JSON object with ALL required fields: verdict, confidence_pct, summary, key_drivers, uncertainty_factors, and sources.
"""


def _parse_response_json(raw: str) -> Dict:
    """Parse JSON response with fallback handling for malformed JSON."""
    import re
    import json
    
    cleaned = raw.strip()
    
    # Remove markdown code blocks
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    
    # Try to find JSON object boundaries
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        cleaned = cleaned[start_idx:end_idx + 1]
    
    # Try parsing
    try:
        parsed = json.loads(cleaned)
        # Validate required fields
        if isinstance(parsed, dict) and all(field in parsed for field in ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]):
            return parsed
        else:
            # Missing required fields, continue to fallback handling
            pass
    except json.JSONDecodeError as e:
        # JSON parse error - try to fix common issues
        # Try to fix common JSON issues
        try:
            # Fix trailing commas
            fixed = re.sub(r',(\s*[}\]])', r'\1', cleaned)
            # Try parsing again
            parsed = json.loads(fixed)
            if isinstance(parsed, dict) and all(field in parsed for field in ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]):
                return parsed
        except Exception:
            pass
    except json.JSONDecodeError as e:
        # Try to fix common JSON issues
        try:
            # Fix unescaped quotes and newlines in string values
            # This is a heuristic approach - find string values and fix them
            fixed = cleaned
            
            # Try to fix trailing commas
            fixed = re.sub(r',\s*}', '}', fixed)
            fixed = re.sub(r',\s*]', ']', fixed)
            
            # Try to fix unescaped newlines in strings (but preserve escaped ones)
            # Match string values and replace unescaped newlines
            def fix_string(match):
                s = match.group(0)
                # Only fix if it's not already escaped
                s = s.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                return s
            
            # Try parsing the fixed version
            try:
                return json.loads(fixed)
            except:
                pass
            
            # Try to extract just the JSON object using balanced braces
            brace_count = 0
            start = -1
            best_end = -1
            for i, char in enumerate(cleaned):
                if char == '{':
                    if start == -1:
                        start = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start != -1:
                        best_end = i
                        try:
                            parsed = json.loads(cleaned[start:i+1])
                            # Validate that it has required fields
                            if all(field in parsed for field in ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]):
                                return parsed
                        except:
                            pass
            
            # If we found a complete JSON object but it failed validation, try to fix it
            if start != -1 and best_end != -1:
                try:
                    # Try to close incomplete strings/arrays/objects
                    partial_json = cleaned[start:best_end+1]
                    # Try to add missing closing braces/brackets
                    open_braces = partial_json.count('{') - partial_json.count('}')
                    open_brackets = partial_json.count('[') - partial_json.count(']')
                    fixed_json = partial_json + '}' * open_braces + ']' * open_brackets
                    parsed = json.loads(fixed_json)
                    if all(field in parsed for field in ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]):
                        return parsed
                except:
                    pass
            
            # Try regex extraction as last resort
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        except Exception as parse_error:
            # Last resort: return a fallback structure
            return {
                "verdict": "UNCERTAIN",
                "confidence_pct": 50.0,
                "summary": f"JSON parsing error: {str(parse_error)}. Raw response (first 300 chars): {cleaned[:300]}...",
                "key_drivers": [
                    {
                        "text": "Unable to parse LLM response - JSON format error",
                        "source_ids": ["SRC_PARSE_ERROR"],
                    }
                ],
                "uncertainty_factors": ["LLM response parsing failed - invalid JSON format"],
                "sources": [
                    {
                        "id": "SRC_PARSE_ERROR",
                        "title": "Parse Error",
                        "url": "",
                        "type": "news",
                        "sentiment": "neutral",
                    }
                ],
            }
        
        # Last resort: return a fallback structure
        return {
            "verdict": "UNCERTAIN",
            "confidence_pct": 50.0,
            "summary": f"JSON parsing error: Unable to parse response. Raw response (first 300 chars): {cleaned[:300]}...",
            "key_drivers": [
                {
                    "text": "Unable to parse LLM response - JSON format error",
                    "source_ids": ["SRC_PARSE_ERROR"],
                }
            ],
            "uncertainty_factors": ["LLM response parsing failed - invalid JSON format"],
            "sources": [
                {
                    "id": "SRC_PARSE_ERROR",
                    "title": "Parse Error",
                    "url": "",
                    "type": "news",
                    "sentiment": "neutral",
                }
            ],
        }


def _offline_analysis(request: AnalysisRequest) -> Dict:
    return {
        "verdict": "UNCERTAIN",
        "confidence_pct": 50.0,
        "summary": "Offline mode stub analysis. Connect to network for real results.",
        "key_drivers": [
            {
                "text": "Offline environment cannot fetch live data.",
                "source_ids": ["SRC_OFFLINE"],
            }
        ],
        "uncertainty_factors": ["No external data available in offline mode."],
        "sources": [
            {
                "id": "SRC_OFFLINE",
                "title": "Offline Stub",
                "url": request.market.url,
                "type": "news",
                "sentiment": "neutral",
            }
        ],
        "analysis_timestamp": None,
        "metadata": {"offline": True},
    }
