#!/usr/bin/env python3
"""Generate an example EDF file for testing and demonstration."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edf import EDF


def generate_distribution(peak: int, max_grade: int, spread: float = 0.15) -> list[float]:
    """
    Generate a bell-curve distribution centered around a peak grade.

    The spread parameter controls distribution width as a fraction of max_grade.
    Lower spread = tighter distribution (low noise), higher spread = wider (high noise).

    Note: For production use, consider deriving spread from actual marker behavior
    data rather than using fixed values. Avoid naive fixed standard deviations.
    """
    dist = []
    for i in range(max_grade + 1):
        diff = abs(i - peak)
        prob = math.exp(-(diff**2) / (2 * (spread * max_grade) ** 2))
        dist.append(prob)

    total = sum(dist)
    return [p / total for p in dist]


def main():
    output_path = Path(__file__).parent / "example.edf"

    # Create new EDF
    edf = EDF(max_grade=20)

    # Set rubric
    edf.rubric = """# Essay Grading Rubric

## Content and Argumentation (10 points)

The essay should demonstrate a clear understanding of the topic and present well-reasoned arguments supported by evidence.

- **Excellent (9-10):** Thesis is compelling and original. Arguments are sophisticated and fully developed with strong evidence.
- **Good (7-8):** Clear thesis with solid arguments. Evidence is relevant and well-integrated.
- **Satisfactory (5-6):** Thesis is present but may be vague. Arguments are adequate but could be stronger.
- **Needs Improvement (3-4):** Weak or unclear thesis. Arguments lack depth or supporting evidence.
- **Unsatisfactory (0-2):** No clear thesis. Arguments are missing or incoherent.

## Structure and Organization (5 points)

The essay should follow a logical structure with clear transitions between ideas.

## Writing Quality (5 points)

Grammar, spelling, punctuation, and style should be appropriate for academic writing.
"""

    # Set prompt
    edf.prompt = """# Essay Assignment: The Impact of Technology on Education

Write a 500-800 word essay discussing how technology has transformed education in the 21st century.

Your essay should:
- Present a clear thesis statement
- Provide specific examples to support your arguments
- Address potential counterarguments
- Conclude with your perspective on the future of educational technology

**Due Date:** End of week 4
**Format:** Markdown text
**Word Count:** 500-800 words
"""

    # Set task-level additional data
    edf.set_task_data(
        school_id="DEMO-001",
        subject_code="ENG-101",
        academic_year="2025",
        difficulty_level="medium",
    )

    # Add submissions
    submissions = [
        {
            "id": "chen_wei_2025",
            "grade": 18,
            "content": """# Technology in Education: A Double-Edged Sword

The integration of technology into education represents one of the most significant shifts in how knowledge is transmitted and acquired in human history. While traditional classrooms relied on textbooks and chalkboards, today's learning environments feature tablets, interactive whiteboards, and artificial intelligence tutors. This essay argues that while technology has democratized access to education and enhanced learning experiences, we must remain vigilant about its potential drawbacks.

## The Democratization of Knowledge

Perhaps the most profound impact of educational technology is its ability to break down barriers to learning. Online courses from prestigious universities are now accessible to students in remote villages. Khan Academy has provided free mathematics education to millions who might otherwise lack access to quality instruction.

## Enhanced Learning Experiences

Technology has also transformed how students engage with material. Interactive simulations allow chemistry students to conduct virtual experiments safely. Virtual reality enables history students to "walk through" ancient Rome.

## The Challenges We Face

However, we must acknowledge significant challenges. The digital divide means that students without reliable internet access fall further behind. Screen time concerns have been linked to attention issues.

## Looking Forward

The future of educational technology lies not in replacing teachers but in augmenting their capabilities. The key is thoughtful implementation that preserves human connection while leveraging technological advantages.
""",
            "student_name": "Wei Chen",
            "student_id": "2025-1001",
        },
        {
            "id": "patel_anika_2025",
            "grade": 15,
            "content": """# How Technology Changed Schools

Technology has really changed how we learn in schools today. When my parents were in school, they didn't have computers in every classroom like we do now. This essay will talk about the good and bad things about technology in education.

## Good Things About Technology

First, technology makes learning more interesting. Instead of just reading from a textbook, we can watch videos, play educational games, and do interactive activities.

Second, technology helps us find information quickly. When I need to research something for a project, I can find articles and videos in seconds.

Third, technology lets students learn from anywhere. During the pandemic, we could still have classes online.

## Bad Things About Technology

However, there are also problems. Some students get distracted by games and social media. Also, not everyone has good technology at home.

## Conclusion

In conclusion, technology has both helped and created challenges for education. I think schools should use technology but also make sure students still learn traditional skills.
""",
            "student_name": "Anika Patel",
            "student_id": "2025-1002",
        },
        {
            "id": "johnson_marcus_2025",
            "grade": 12,
            "content": """# Technology and Education

Technology is everywhere now including in schools. This essay is about technology in education.

Computers are used in schools for many things. Students can type papers instead of writing them by hand. Teachers can show presentations instead of writing on the board.

The internet is also important for education. Students can look things up online for their homework. There are websites that help with learning like Khan Academy.

There are good things and bad things about technology in schools. The good things are that it makes some things easier. The bad things are that it can distract students.

Overall I think technology is helpful for education when used the right way.
""",
            "student_name": "Marcus Johnson",
            "student_id": "2025-1003",
        },
        {
            "id": "oconnor_siobhan_2025",
            "grade": 8,
            "content": """# tech in school

technology is cool and schools use it now. we have chromebooks and stuff.

i like using the computer because typing is faster than writing. also you can play games sometimes.

some kids dont have good wifi at home tho which sucks for them.

teachers put stuff on google classroom which is helpful i guess.

in conclusion technology is in schools now and its probably good mostly.
""",
            "student_name": "Siobhan O'Connor",
            "student_id": "2025-1004",
        },
        {
            "id": "yamamoto_kenji_2025",
            "grade": 17,
            "content": """# Navigating the Digital Transformation of Education

The classroom of 2025 bears little resemblance to its counterpart from even two decades ago. Where once students sat in rows copying notes from a chalkboard, they now collaborate across continents through video conferencing, explore molecular structures in virtual reality, and receive personalized feedback from AI-powered tutoring systems.

## The Promise of Personalization

Traditional education operated on a one-size-fits-all model. Educational technology has begun to dismantle this limitation. Adaptive learning platforms analyze student performance in real-time, identifying knowledge gaps and adjusting content accordingly.

## Global Collaboration and Cultural Exchange

Technology has also transformed education from a local to a global endeavor. Students in Tokyo can collaborate on projects with peers in Toronto, gaining exposure to diverse perspectives.

## Critical Concerns

Yet this technological revolution comes with significant concerns. The commodification of education through technology risks reducing learning to a series of optimizable metrics. The attention economy creates interfaces designed to maximize engagement rather than learning.

## A Balanced Path Forward

The path forward requires neither uncritical embrace nor reactionary rejection of educational technology. Technology should augment rather than replace the fundamentally human elements of education.
""",
            "student_name": "Kenji Yamamoto",
            "student_id": "2025-1005",
        },
    ]

    for sub in submissions:
        grade = sub["grade"]
        # Variance modes model marker noise levels, not systematic biases:
        # - optimistic: low noise (tight distribution, spread=0.10)
        # - expected: medium noise (baseline, spread=0.15)
        # - pessimistic: high noise (wide distribution, spread=0.20)
        # All centered on the same grade - only the spread differs.
        optimistic = generate_distribution(grade, 20, spread=0.10)
        expected = generate_distribution(grade, 20, spread=0.15)
        pessimistic = generate_distribution(grade, 20, spread=0.20)

        edf.add_submission(
            submission_id=sub["id"],
            grade=grade,
            optimistic=optimistic,
            expected=expected,
            pessimistic=pessimistic,
            content=sub["content"],
            student_name=sub["student_name"],
            student_id=sub["student_id"],
        )

    edf.save(output_path)
    print(f"Generated: {output_path}")
    print(f"  Submissions: {len(edf.submissions)}")
    print(f"  Max grade: {edf.max_grade}")


if __name__ == "__main__":
    main()
