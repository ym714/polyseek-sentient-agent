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
        "Follow instructions precisely, cite source IDs, and output valid JSON.\n\n"
        "CRITICAL: You MUST respond with ONLY a valid JSON object. "
        "Do not include any text before or after the JSON. "
        "Do not wrap the JSON in markdown code blocks."
    )
    user_prompt = _build_user_prompt(request)
    
    # Detect if using Gemini model
    is_gemini = "gemini" in settings.llm.model.lower()
    
    # Build completion parameters
    completion_params = {
        "model": settings.llm.model,
        "api_key": settings.llm.api_key,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,  # Use full token limit
    }
    
    # Only add response_format for OpenAI models
    if not is_gemini:
        completion_params["response_format"] = {"type": "json_object"}
    
    try:
        response = await acompletion(**completion_params)
        content = response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[ERROR] LLM API call failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return _create_error_response(f"LLM API error: {str(e)}")
    
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
            # Missing required fields, log and use fallback parser
            print(f"[WARNING] LLM response missing required fields. Got: {list(direct_parse.keys()) if isinstance(direct_parse, dict) else type(direct_parse)}")
            print(f"[DEBUG] Raw response (first 500 chars): {content[:500]}")
            result = _parse_response_json(content)
    except (json.JSONDecodeError, ValueError) as e:
        # JSON parse failed, log and use fallback parser
        print(f"[ERROR] JSON parse failed: {str(e)}")
        print(f"[DEBUG] Raw response (first 500 chars): {content[:500]}")
        result = _parse_response_json(content)
    
    # Ensure result is a dict
    if not isinstance(result, dict):
        result = {}
    
    # Validate that result has required fields
    required_fields = ["verdict", "confidence_pct", "summary", "key_drivers", "sources"]
    missing_fields = [field for field in required_fields if field not in result]
    if missing_fields:
        print(f"[ERROR] Missing required fields after parsing: {missing_fields}")
        print(f"[DEBUG] Parsed result keys: {list(result.keys())}")
        # Return fallback structure
        return _create_error_response(f"LLM response missing fields: {missing_fields}")
    
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
        "Follow instructions precisely, cite source IDs, and output valid JSON.\n\n"
        "CRITICAL: You MUST respond with ONLY a valid JSON object. "
        "Do not include any text before or after the JSON. "
        "Do not wrap the JSON in markdown code blocks."
    )
    
    # Detect if using Gemini model
    is_gemini = "gemini" in settings.llm.model.lower()
    
    # Step 1: Planner - Create analysis plan
    planner_prompt = _build_planner_prompt(request)
    planner_params = {
        "model": settings.llm.model,
        "api_key": settings.llm.api_key,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": planner_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    if not is_gemini:
        planner_params["response_format"] = {"type": "json_object"}
    
    planner_response = await acompletion(**planner_params)
    plan_content = planner_response["choices"][0]["message"]["content"]
    plan = _parse_response_json(plan_content)
    
    # Ensure plan is a dict
    if not isinstance(plan, dict):
        plan = {"analysis_plan": [], "key_questions": [], "information_gaps": []}
    
    # Step 2: Critic - Critically evaluate the plan and identify gaps
    critic_prompt = _build_critic_prompt(request, plan)
    critic_params = {
        "model": settings.llm.model,
        "api_key": settings.llm.api_key,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": critic_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    if not is_gemini:
        critic_params["response_format"] = {"type": "json_object"}
    
    critic_response = await acompletion(**critic_params)
    critique_content = critic_response["choices"][0]["message"]["content"]
    critique = _parse_response_json(critique_content)
    
    # Ensure critique is a dict
    if not isinstance(critique, dict):
        critique = {"gaps": [], "follow_up_queries": [], "biases": [], "recommendations": []}
    
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
    final_params = {
        "model": settings.llm.model,
        "api_key": settings.llm.api_key,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt},
        ],
        "temperature": settings.llm.temperature,
        "max_tokens": settings.llm.max_tokens,  # Use full token limit
    }
    if not is_gemini:
        final_params["response_format"] = {"type": "json_object"}
    
    final_response = await acompletion(**final_params)
    final_content = final_response["choices"][0]["message"]["content"]
    result = _parse_response_json(final_content)
    
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
    result["metadata"]["mode"] = "deep"
    result["metadata"]["plan"] = plan.get("analysis_plan", []) if isinstance(plan, dict) else []
    result["metadata"]["critique"] = {
        "gaps": critique.get("gaps", []) if isinstance(critique, dict) else [],
        "follow_up_queries": critique.get("follow_up_queries", []) if isinstance(critique, dict) else [],
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
You are performing the FINAL deep analysis of a prediction market. This is a COMPREHENSIVE, PROFESSIONAL-GRADE analysis.

You have completed:
1. ✅ Created a structured analysis plan
2. ✅ Critically evaluated the plan and identified gaps
3. ✅ Gathered comprehensive evidence from multiple sources

Now perform the final deep analysis with MAXIMUM RIGOR and INSIGHT.

=== MARKET INFORMATION ===
- Title: {market.title}
- Category: {market.category}
- Deadline: {market.deadline}
- Current Prices: YES={market.prices.yes} ({float(market.prices.yes)*100:.1f}%), NO={market.prices.no} ({float(market.prices.no)*100:.1f}%)
- Liquidity: {market.liquidity}
- Volume (24h): {market.volume_24h}
- Resolution Rules: {rules}

=== ANALYSIS PLAN ===
{plan_summary}

=== CRITICAL GAPS IDENTIFIED ===
{critique_summary}

=== EVIDENCE BASE ===

Platform Discussion:
{comments_block}

External Intelligence:
{signals_block}

=== ANALYTICAL FRAMEWORK ===

You MUST apply the following analytical frameworks:

1. **BASE RATE ANALYSIS**
   - What is the historical base rate for similar events?
   - How does the current market price compare to the base rate?
   - What factors justify deviation from the base rate?

2. **SCENARIO PLANNING**
   - Identify 3-5 distinct scenarios (optimistic, pessimistic, most likely)
   - Assign probabilities to each scenario
   - Explain key triggers and indicators for each scenario

3. **EVIDENCE QUALITY ASSESSMENT**
   - Evaluate source credibility (primary vs secondary, expert vs opinion)
   - Assess recency and relevance of evidence
   - Identify potential biases in sources

4. **CAUSAL REASONING**
   - Map causal chains: X → Y → Outcome
   - Identify necessary vs sufficient conditions
   - Highlight feedback loops and second-order effects

5. **UNCERTAINTY QUANTIFICATION**
   - Distinguish between epistemic (knowledge) and aleatory (randomness) uncertainty
   - Identify key unknowns and information gaps
   - Specify what new information would most change your assessment

=== OUTPUT REQUIREMENTS ===

Respond with valid JSON containing:

- **verdict**: "YES" | "NO" | "UNCERTAIN"
- **confidence_pct**: 0-100 (your confidence in the verdict, NOT the probability of YES)
- **summary**: 8-12 sentences providing:
  * Opening context and market overview (2 sentences)
  * Base rate analysis and market comparison (2 sentences)
  * Key evidence synthesis (3-4 sentences)
  * Scenario analysis (2 sentences)
  * Final assessment with caveats (2 sentences)

- **key_drivers**: Array of 5-7 drivers, each with:
  * "text": 3-5 sentences explaining:
    - What the driver is
    - Why it matters (causal mechanism)
    - How strong the evidence is
    - Potential counterarguments
  * "source_ids": Array of relevant source IDs

- **uncertainty_factors**: Array of 5-8 factors, each being:
  * Specific and actionable
  * Categorized (epistemic vs aleatory if relevant)
  * Quantifiable where possible

- **next_steps**: Array of 5-7 actionable recommendations:
  * Specific information to gather
  * Key indicators to monitor
  * Decision triggers

- **sources**: Array of all cited sources with:
  * "id": Unique identifier
  * "title": Full title
  * "url": Complete URL
  * "type": "market" | "comment" | "sns" | "news"
  * "sentiment": "pro" | "con" | "neutral"

=== QUALITY STANDARDS ===

Your analysis MUST demonstrate:
- ✅ Deep domain knowledge and contextual understanding
- ✅ Rigorous evidence evaluation and source criticism
- ✅ Clear causal reasoning and logical argumentation
- ✅ Balanced consideration of pro/con arguments
- ✅ Explicit acknowledgment of uncertainties and limitations
- ✅ Actionable insights and recommendations
- ✅ Professional-grade writing (clear, precise, jargon-free)

=== CRITICAL REMINDERS ===

- This is DEEP mode - provide MAXIMUM detail and insight
- Each key_driver should be 3-5 sentences (not 1-2)
- Summary should be 8-12 sentences (not 3-5)
- Cite specific evidence with source IDs
- Be intellectually honest about uncertainties
- Avoid generic statements - be specific and concrete
- Think like a professional analyst, not a chatbot

NOW PERFORM THE ANALYSIS:
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

    return f"""Analyze this prediction market and return ONLY a JSON object (no markdown, no explanation).

REQUIRED JSON STRUCTURE:
{{
  "verdict": "YES" | "NO" | "UNCERTAIN",
  "confidence_pct": <number 0-100>,
  "summary": "<comprehensive 3-5 sentence analysis>",
  "key_drivers": [
    {{"text": "<detailed explanation>", "source_ids": ["SRC1", "SRC2"]}}
  ],
  "uncertainty_factors": ["<factor 1>", "<factor 2>"],
  "sources": [
    {{"id": "SRC1", "title": "<title>", "url": "<url>", "type": "market|comment|sns|news", "sentiment": "pro|con|neutral"}}
  ]
}}

MARKET DATA:
- Title: {market.title}
- Category: {market.category}
- Deadline: {market.deadline}
- Current Prices: YES={market.prices.yes}, NO={market.prices.no}
- Liquidity: {market.liquidity}
- Volume 24h: {market.volume_24h}
- Resolution Rules: {rules}

PLATFORM COMMENTS:
{comments_block}

EXTERNAL SIGNALS:
{signals_block}

ANALYSIS INSTRUCTIONS:
1. Evaluate BOTH pro and con evidence
2. Use current YES price ({market.prices.yes}) as base probability
3. Cite source IDs in key_drivers (use provided IDs or create synthetic ones like SRC1, SRC2)
4. Include at least 2-3 uncertainty factors
5. If evidence is insufficient, verdict MUST be "UNCERTAIN"
6. Write detailed key_drivers (full sentences explaining impact)
7. Ensure sources[].type is exactly: "market", "comment", "sns", or "news"
8. Include at least 3 sources

EXAMPLE RESPONSE FORMAT:
{{
  "verdict": "UNCERTAIN",
  "confidence_pct": 45.0,
  "summary": "Based on the available evidence, this market presents significant uncertainty. The current price of {market.prices.yes} suggests market participants are moderately bearish. However, key information gaps and conflicting signals prevent a confident prediction. The analysis considers both supporting and opposing factors.",
  "key_drivers": [
    {{"text": "Recent news indicates positive momentum, with multiple sources reporting favorable developments. This could push the outcome toward YES.", "source_ids": ["SRC1", "SRC2"]}},
    {{"text": "However, historical precedent and expert commentary suggest caution. Similar situations have resolved negatively in the past.", "source_ids": ["SRC3"]}}
  ],
  "uncertainty_factors": [
    "Limited reliable data available for this specific scenario",
    "Conflicting expert opinions create ambiguity",
    "Timeline uncertainty affects probability assessment"
  ],
  "sources": [
    {{"id": "SRC1", "title": "News Article Title", "url": "https://example.com", "type": "news", "sentiment": "pro"}},
    {{"id": "SRC2", "title": "Social Media Discussion", "url": "https://twitter.com/example", "type": "sns", "sentiment": "pro"}},
    {{"id": "SRC3", "title": "Expert Analysis", "url": "https://example.com/analysis", "type": "news", "sentiment": "con"}}
  ]
}}

NOW ANALYZE THE MARKET AND RETURN ONLY THE JSON OBJECT:
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


def _create_error_response(error_message: str) -> Dict:
    """Create a standardized error response structure."""
    return {
        "verdict": "UNCERTAIN",
        "confidence_pct": 50.0,
        "summary": error_message,
        "key_drivers": [
            {
                "text": "Analysis failed due to technical error. Please try again or contact support.",
                "source_ids": ["SRC_ERROR"],
            }
        ],
        "uncertainty_factors": ["Technical error prevented analysis"],
        "sources": [
            {
                "id": "SRC_ERROR",
                "title": "Error",
                "url": "",
                "type": "news",
                "sentiment": "neutral",
            }
        ],
        "metadata": {"error": True, "error_message": error_message},
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
