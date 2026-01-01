#!/usr/bin/env python3
"""Generate an example EDF file for testing and demonstration."""

import sys
from pathlib import Path

# Add parent directory to path so we can import edf
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edf import EDFBuilder


def generate_distribution(peak: int, max_grade: int, spread: float = 0.15) -> list[float]:
    """Generate a bell-curve-ish distribution centered around a peak grade."""
    import math

    dist = []
    for i in range(max_grade + 1):
        # Gaussian-like distribution
        diff = abs(i - peak)
        prob = math.exp(-(diff**2) / (2 * (spread * max_grade) ** 2))
        dist.append(prob)

    # Normalize to sum to 1.0
    total = sum(dist)
    return [p / total for p in dist]


def main():
    output_path = Path(__file__).parent / "example.edf"

    builder = EDFBuilder()
    builder.set_max_grade(20)
    builder.set_version(1)

    # Set rubric
    builder.set_rubric("""# Essay Grading Rubric

## Content and Argumentation (10 points)

The essay should demonstrate a clear understanding of the topic and present well-reasoned arguments supported by evidence.

- **Excellent (9-10):** Thesis is compelling and original. Arguments are sophisticated and fully developed with strong evidence.
- **Good (7-8):** Clear thesis with solid arguments. Evidence is relevant and well-integrated.
- **Satisfactory (5-6):** Thesis is present but may be vague. Arguments are adequate but could be stronger.
- **Needs Improvement (3-4):** Weak or unclear thesis. Arguments lack depth or supporting evidence.
- **Unsatisfactory (0-2):** No clear thesis. Arguments are missing or incoherent.

## Structure and Organization (5 points)

The essay should follow a logical structure with clear transitions between ideas.

- **Excellent (5):** Flawless organization with seamless transitions.
- **Good (4):** Well-organized with effective transitions.
- **Satisfactory (3):** Basic structure present but transitions may be abrupt.
- **Needs Improvement (2):** Disorganized with poor flow.
- **Unsatisfactory (0-1):** No discernible structure.

## Writing Quality (5 points)

Grammar, spelling, punctuation, and style should be appropriate for academic writing.

- **Excellent (5):** Virtually error-free with sophisticated style.
- **Good (4):** Minor errors that don't impede understanding.
- **Satisfactory (3):** Some errors but meaning is clear.
- **Needs Improvement (2):** Frequent errors that affect readability.
- **Unsatisfactory (0-1):** Pervasive errors that obscure meaning.
""")

    # Set prompt
    builder.set_prompt("""# Essay Assignment: The Impact of Technology on Education

Write a 500-800 word essay discussing how technology has transformed education in the 21st century. Consider both the benefits and challenges of integrating technology into learning environments.

Your essay should:
- Present a clear thesis statement
- Provide specific examples to support your arguments
- Address potential counterarguments
- Conclude with your perspective on the future of educational technology

**Due Date:** End of week 4
**Format:** Markdown text
**Word Count:** 500-800 words
""")

    # Set task-level additional data
    builder.set_task_data(
        school_id="DEMO-001",
        subject_code="ENG-101",
        academic_year="2025",
        difficulty_level="medium",
    )

    # Add submissions with varying quality
    submissions = [
        {
            "id": "chen_wei_2025",
            "grade": 18,
            "content": """# Technology in Education: A Double-Edged Sword

The integration of technology into education represents one of the most significant shifts in how knowledge is transmitted and acquired in human history. While traditional classrooms relied on textbooks and chalkboards, today's learning environments feature tablets, interactive whiteboards, and artificial intelligence tutors. This essay argues that while technology has democratized access to education and enhanced learning experiences, we must remain vigilant about its potential drawbacks.

## The Democratization of Knowledge

Perhaps the most profound impact of educational technology is its ability to break down barriers to learning. Online courses from prestigious universities are now accessible to students in remote villages. Khan Academy has provided free mathematics education to millions who might otherwise lack access to quality instruction. This democratization represents a fundamental shift in who can learn and what they can learn.

## Enhanced Learning Experiences

Technology has also transformed how students engage with material. Interactive simulations allow chemistry students to conduct virtual experiments safely. Virtual reality enables history students to "walk through" ancient Rome. Adaptive learning systems adjust difficulty in real-time based on student performance. These tools can accommodate different learning styles and paces in ways that were previously impossible.

## The Challenges We Face

However, we must acknowledge significant challenges. The digital divide means that students without reliable internet access fall further behind. Screen time concerns have been linked to attention issues and reduced physical activity. Additionally, the ease of finding information online may be reducing students' critical thinking skills and their ability to synthesize complex ideas independently.

## Looking Forward

The future of educational technology lies not in replacing teachers but in augmenting their capabilities. AI can handle routine assessment, freeing teachers to focus on mentorship and complex problem-solving discussions. The key is thoughtful implementation that preserves human connection while leveraging technological advantages.

In conclusion, technology in education is neither savior nor villain but a powerful tool that requires wisdom in its application. Our task is to harness its benefits while mitigating its risks.
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

First, technology makes learning more interesting. Instead of just reading from a textbook, we can watch videos, play educational games, and do interactive activities. This helps students who learn better by seeing and doing things rather than just reading.

Second, technology helps us find information quickly. When I need to research something for a project, I can find articles and videos in seconds. This saves a lot of time compared to going to the library and looking through books.

Third, technology lets students learn from anywhere. During the pandemic, we could still have classes online. Some students who are sick or live far away can still participate in class through video calls.

## Bad Things About Technology

However, there are also problems with technology in education. Some students get distracted by games and social media when they should be learning. It's hard to focus when you have a device that can do so many fun things.

Also, not everyone has good technology at home. Some students don't have computers or fast internet, so they can't do their homework as easily as other students. This creates an unfair situation.

Another problem is that students might not learn how to think for themselves. When you can look up any answer on Google, you might not develop good problem-solving skills.

## Conclusion

In conclusion, technology has both helped and created challenges for education. I think schools should use technology but also make sure students still learn traditional skills. Teachers should help students use technology responsibly.
""",
            "student_name": "Anika Patel",
            "student_id": "2025-1002",
        },
        {
            "id": "johnson_marcus_2025",
            "grade": 12,
            "content": """# Technology and Education

Technology is everywhere now including in schools. This essay is about technology in education.

Computers are used in schools for many things. Students can type papers instead of writing them by hand. Teachers can show presentations instead of writing on the board. Schools have computer labs where students can do research.

The internet is also important for education. Students can look things up online for their homework. There are websites that help with learning like Khan Academy. Some classes are even taught completely online.

Phones are technology too but they can be distracting. Some schools don't allow phones in class. But phones can also be used for learning if used correctly.

There are good things and bad things about technology in schools. The good things are that it makes some things easier and more interesting. The bad things are that it can distract students and not everyone has access to technology.

In the future technology will probably be used even more in schools. Maybe robots will teach classes or students will learn in virtual reality. It will be interesting to see what happens.

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

i like using the computer because typing is faster than writing. also you can play games sometimes when the teacher isnt looking lol.

some kids dont have good wifi at home tho which sucks for them. my wifi is pretty good so i can do my homework.

teachers put stuff on google classroom which is helpful i guess. you can see your assignments and turn them in online.

in conclusion technology is in schools now and its probably good mostly.
""",
            "student_name": "Siobhan O'Connor",
            "student_id": "2025-1004",
        },
        {
            "id": "yamamoto_kenji_2025",
            "grade": 17,
            "content": """# Navigating the Digital Transformation of Education

The classroom of 2025 bears little resemblance to its counterpart from even two decades ago. Where once students sat in rows copying notes from a chalkboard, they now collaborate across continents through video conferencing, explore molecular structures in virtual reality, and receive personalized feedback from AI-powered tutoring systems. This transformation raises fundamental questions about the nature and purpose of education itself.

## The Promise of Personalization

Traditional education operated on a one-size-fits-all model, with thirty students receiving identical instruction regardless of their individual needs, interests, or pace of learning. Educational technology has begun to dismantle this limitation. Adaptive learning platforms analyze student performance in real-time, identifying knowledge gaps and adjusting content accordingly. A student struggling with algebraic equations receives additional practice problems and alternative explanations, while a peer who has mastered the concept moves on to more challenging material. This personalization was previously possible only through one-on-one tutoring available to the privileged few.

## Global Collaboration and Cultural Exchange

Technology has also transformed education from a local to a global endeavor. Students in Tokyo can collaborate on projects with peers in Toronto, gaining exposure to diverse perspectives and developing cross-cultural communication skills increasingly vital in our interconnected world. Language learning applications connect learners with native speakers across the globe, making authentic practice accessible to all rather than just those who can afford international travel.

## Critical Concerns

Yet this technological revolution comes with significant concerns. The commodification of education through technology risks reducing learning to a series of optimizable metrics, potentially sacrificing depth for measurable efficiency. The attention economy that drives much of the technology industry creates interfaces designed to maximize engagement rather than learning. Furthermore, the collection of detailed data on student learning patterns raises serious privacy concerns.

## A Balanced Path Forward

The path forward requires neither uncritical embrace nor reactionary rejection of educational technology. Instead, educators and policymakers must thoughtfully evaluate which technologies genuinely serve learning outcomes and which merely serve commercial interests masquerading as innovation. Technology should augment rather than replace the fundamentally human elements of education: the mentorship of caring teachers, the social development that comes from peer interaction, and the cultivation of wisdom alongside knowledge.

The measure of success for educational technology should ultimately be whether it helps develop thoughtful, capable, and ethical human beings prepared to address the challenges of their time.
""",
            "student_name": "Kenji Yamamoto",
            "student_id": "2025-1005",
        },
    ]

    for sub in submissions:
        grade = sub["grade"]
        # Generate distributions with different spreads for optimistic/expected/pessimistic
        optimistic = generate_distribution(min(grade + 1, 20), 20, spread=0.12)
        expected = generate_distribution(grade, 20, spread=0.15)
        pessimistic = generate_distribution(max(grade - 1, 0), 20, spread=0.18)

        builder.add_submission(
            submission_id=sub["id"],
            grade=grade,
            optimistic=optimistic,
            expected=expected,
            pessimistic=pessimistic,
            content=sub["content"],
            student_name=sub["student_name"],
            student_id=sub["student_id"],
        )

    builder.write(output_path)
    print(f"Generated: {output_path}")
    print(f"  Submissions: {len(submissions)}")
    print(f"  Max grade: 20")


if __name__ == "__main__":
    main()
