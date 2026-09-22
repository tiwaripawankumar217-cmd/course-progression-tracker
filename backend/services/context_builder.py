from typing import List, Optional
from backend.models.curriculum import Curriculum
from backend.services.material_processor import ProcessedMaterial


class ContextBuilder:
    """
    Constructs clear, bounded LLM context adhering to the Day 3 source hierarchy.
    Enforces distinct demarcations between Curriculum, Transcript, and Supporting Materials.
    """

    SOURCE_RULES = """=== SOURCE HIERARCHY AND GROUNDING RULES ===
1. SOURCE 1 — CURRICULUM (Authoritative Source of Truth):
   - You may ONLY map to lecture codes, topics, subtopics, classwork, and homework that ACTUALLY EXIST in the supplied curriculum below.
   - You must NEVER invent, assume, or create a new curriculum topic or lecture.
   - If the teacher taught a topic not in the curriculum (e.g. Recursion), place it into 'unmatched_content'. Do NOT add it to 'topics_taught'.

2. SOURCE 2 — LECTURE TRANSCRIPT (Primary Delivery Evidence):
   - The transcript represents what the teacher actually said and taught in the classroom.
   - Every topic marked in 'topics_taught', 'classwork', or 'homework' MUST have a supporting quote/evidence excerpt from the transcript.
   - If there is no transcript evidence that a topic was taught, DO NOT mark it as taught.

3. SOURCE 3 — SUPPORTING MATERIALS (Contextual Academic Reference):
   - Materials (PDFs, PPT slides, notes, DOCX) provide vocabulary, definitions, and planned materials.
   - SUPPORTING MATERIALS MUST NEVER OVERRIDE THE TRANSCRIPT.
   - If a topic appears in a PPT slide or PDF, but the teacher NEVER discusses or explains it in the transcript, classify it under 'topics_not_evidenced'.
"""

    @classmethod
    def format_curriculum(cls, curriculum: Curriculum) -> str:
        """Formats the curriculum into a concise, easily scannable textual representation."""
        lines = []
        if curriculum.course_id or curriculum.course_name:
            lines.append(f"Course: {curriculum.course_name or curriculum.course_id} (ID: {curriculum.course_id})")

        for lec in curriculum.lectures:
            lines.append(f"\nLecture Code: {lec.lecture} (Week {lec.week}, Day {lec.day})")
            if lec.content:
                lines.append("  Planned Topics:")
                for topic in lec.content:
                    lines.append(f"    - {topic}")
            if lec.classwork:
                lines.append("  Planned Classwork:")
                for cw in lec.classwork:
                    lines.append(f"    - {cw}")
            if lec.homework:
                lines.append("  Planned Homework:")
                for hw in lec.homework:
                    lines.append(f"    - {hw}")

        return "\n".join(lines)

    @classmethod
    def build_prompt_context(
        cls,
        curriculum: Curriculum,
        transcript: str,
        materials: Optional[List[ProcessedMaterial]] = None
    ) -> str:
        """
        Combines Curriculum, Transcript, and Supporting Materials into the complete LLM prompt context.
        """
        sections = [
            cls.SOURCE_RULES,
            "\n=== ACTIVE CURRICULUM ===",
            cls.format_curriculum(curriculum),
            "\n=== LECTURE TRANSCRIPT ===",
            transcript.strip(),
        ]

        if materials:
            for mat in materials:
                if mat.content.strip():
                    sections.append(f"\n=== SUPPORTING MATERIAL: {mat.name} ({mat.material_type.upper()}) ===")
                    sections.append(mat.content.strip())

        return "\n\n".join(sections)
