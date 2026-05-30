#!/usr/bin/env python3
"""
code-tutor-api — student code → personalized explanation, mistake patterns,
next exercise, mastery score — for coding bootcamps and education platforms
"""
import anthropic, json, re, sys
from pathlib import Path

SYSTEM = """You are a patient, expert coding tutor who adapts to each student's level.
Analyze this student's code submission and provide personalized tutoring.

Never just give them the answer — guide them to understand.
Identify their current mental model and correct misunderstandings gently.

Return ONLY valid JSON — no markdown, no explanation.

{
  "student_level": "complete_beginner|beginner|intermediate|advanced",
  "assignment_understood": true_or_false,
  "code_works": true_or_false,
  "bugs": [
    {
      "line": number_or_null,
      "bug": "what is wrong",
      "socratic_question": "question to guide student to find the bug themselves",
      "hint": "gentle hint without giving answer",
      "explanation": "full explanation shown after they try"
    }
  ],
  "conceptual_gaps": [
    {
      "concept": "concept they seem to misunderstand",
      "evidence": "what in their code shows this",
      "explanation": "plain-language explanation",
      "analogy": "real-world analogy to make it click"
    }
  ],
  "what_they_did_well": ["specific things to praise — genuine, not generic"],
  "code_quality_feedback": {
    "naming": "feedback on variable/function naming",
    "structure": "feedback on code organization",
    "efficiency": "efficiency observations",
    "style": "style improvements"
  },
  "mastery_score": {
    "overall": number_0_to_100,
    "concepts": [
      {"concept":"loops","score":number_0_to_100},
      {"concept":"functions","score":number_0_to_100}
    ]
  },
  "next_exercise": {
    "title": "title of next exercise",
    "description": "exercise description",
    "difficulty": "same|slightly_harder",
    "concept_practiced": "what concept this reinforces",
    "starter_code": "optional starter code or null"
  },
  "motivational_message": "genuine, specific encouragement — not generic 'great job'",
  "suggested_resources": [
    {"resource":"string","url":"string or null","why":"why this helps"}
  ],
  "confidence": 0.0
}"""

def tutor(code: str, assignment: str = "", language: str = "auto", level: str = "auto") -> dict:
    client = anthropic.Anthropic()
    context_parts = [
        f"Language: {language}" if language != "auto" else "",
        f"Student level: {level}" if level != "auto" else "",
        f"Assignment: {assignment}" if assignment else "",
        f"\nStudent code:\n{code[:10000]}"
    ]
    prompt = "\n".join(p for p in context_parts if p)
    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=2500, system=SYSTEM,
        messages=[{"role":"user","content":f"Tutor this student:\n\n{prompt}"}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

def print_feedback(r: dict):
    score = r.get("mastery_score",{}).get("overall",0)
    works = r.get("code_works",False)
    bugs = r.get("bugs",[])
    gaps = r.get("conceptual_gaps",[])

    print(f"\n{'═'*60}")
    print(f"  CODE TUTOR — Level: {r.get('student_level','?').replace('_',' ').upper()}")
    print(f"  Mastery: {score}/100 | Code works: {'✅' if works else '❌'}")
    print(f"{'═'*60}")

    wells = r.get("what_they_did_well",[])
    if wells:
        print(f"\n  ✅ What you did well:")
        for w in wells: print(f"  • {w}")

    if bugs:
        print(f"\n  BUGS ({len(bugs)})")
        for bug in bugs:
            line = f" (line {bug['line']})" if bug.get("line") else ""
            print(f"\n  🔍 {bug.get('bug','')}{line}")
            print(f"  Question: {bug.get('socratic_question','')}")
            print(f"  Hint: {bug.get('hint','')}")

    if gaps:
        print(f"\n  CONCEPTS TO REVISIT")
        for gap in gaps:
            print(f"\n  📚 {gap.get('concept','')}")
            print(f"  {gap.get('explanation','')[:150]}")
            if gap.get("analogy"): print(f"  Think of it like: {gap['analogy'][:100]}")

    next_ex = r.get("next_exercise",{})
    if next_ex:
        print(f"\n  NEXT EXERCISE: {next_ex.get('title','')}")
        print(f"  {next_ex.get('description','')[:150]}")

    print(f"\n  💪 {r.get('motivational_message','Keep going!')}")
    print(f"  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="AI coding tutor for student code review")
    p.add_argument("code", help="Code file or '-' for stdin")
    p.add_argument("--assignment","-a",default="",help="Assignment description")
    p.add_argument("--language","-l",default="auto")
    p.add_argument("--level",default="auto",choices=["auto","complete_beginner","beginner","intermediate","advanced"])
    p.add_argument("--json",action="store_true")
    a = p.parse_args()
    src = sys.stdin.read() if a.code=="-" else (Path(a.code).read_text(encoding="utf-8",errors="replace") if Path(a.code).exists() else a.code)
    r = tutor(src, a.assignment, a.language, a.level)
    if a.json: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_feedback(r)
