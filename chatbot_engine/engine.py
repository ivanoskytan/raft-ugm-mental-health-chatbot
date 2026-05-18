from config.config import Settings
from chatbot_engine.llm_client import GPTClient
from chatbot_engine.retriever import Retriever

import os
import json
import logging

settings = Settings.load()

class ChatbotEngine:
    def __init__(self):
        self.fine_tuned_model_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model=settings.FINE_TUNED_MODEL
        )
        self.logger = logging.getLogger("ChatbotEngine")
        self.retriever = Retriever()
        return
    
    def generate_response(self, user_query):
        user_answer = user_query.get("user_answer", "")
        group_id = user_query.get("group_id", "")
        section = user_query.get("section", "")

        system_prompt = """
You are a mental health screening assistant.

You will receive a JSON input containing:
- type ("Opening" or "Survey")
- next_section
- user_answer
- next_group_id
- next_questions
- scoring_system
- set_of_documents

GENERAL BEHAVIOR:
- Select the MOST appropriate document from set_of_documents based on the user_answer.
- Do NOT write a standalone empathetic sentence. Instead, blend a highly compressed empathetic acknowledgment directly into the question itself.
- Avoid all conversational filler, preambles, or reassurance loops (e.g., do NOT use "Saya memahami bahwa...", "Saya di sini untuk...", "Emosi bisa sangat kompleks...").
- Use "Saya" and "Anda" to maintain a formal and polite tone.

If type is "Opening":
1. Generate ONE assistant_question that:
- Addresses the user by name.
- Merges a very brief empathy/advice phrase and every single question from next_questions into EXACTLY 1 single, cohesive sentence.
Return ONLY:
{
"assistant_question": "<1 single sentence combining brief empathy and consolidated question>"
}

If type is "Survey":
1. For EACH survey question in next_questions, assign a score strictly following the scoring_system.
2. Combine a very brief empathy phrase and all questions from next_questions into EXACTLY 1 single, cohesive sentence.
Return ONLY:
{
"scores": [
{ "survey_question": "<question>", "score": <number> }
],
"assistant_question": "<1 single sentence combining brief empathy and consolidated question>"
}

If section is "Ending":
1. Provide a concise closing message with empathetic advice based on the best-fit document.
2. Do not ask further questions.
- STRICTLY limits the output to EXACTLY 1 single sentence.
Return ONLY:
{
"assistant_question": "<1 single sentence closing empathetic advice>"
}

STRICT RULES:
- Output valid JSON only.
- Do NOT include explanations or markdown formatting.
- CRITICAL LENGTH RULE: The assistant_question text must be EXACTLY 1 sentence long. Count the periods; there must only be one.
- No introductory filler sentences. Transition immediately from a brief empathy clause into the question using conjunctions like "jadi", "maka", or "namun".
- Ensure all questions in next_questions are covered in the final combined question.
        """

        conversation_type = "Opening" if section == "" else "Survey"
        BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
        grouped_mental_health_screening = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")

        with open(grouped_mental_health_screening, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)

        next_questions = []
        scoring_system = []

        section_group_map = {
            "Depression": 2, "Anger": 2, "Mania": 1, "Anxiety": 2, "Somatic": 3,
            "Suicidal": 2, "Psychosis": 2, "Sleep Disturbance": 1, "Memory": 1,
            "Dissociation": 2, "Substance Use": 2, "Repetitive Thought": 2
        }

        # section_group_map = {
        #     "Depression": 2, "Repetitive Thought": 2
        # }
        sections = list(section_group_map.keys())

        if section == "Opening":
            next_section = "Depression"
            next_group_id = 1
        elif section == "Repetitive Thought":
            next_section = "Ending"
            next_group_id = 0
        else:
            current_index = sections.index(section)
            max_group = section_group_map[section]

            if group_id < max_group:
                next_section = section
                next_group_id = group_id + 1
            else:
                if current_index + 1 < len(sections):
                    next_section = sections[current_index + 1]
                    next_group_id = 1
                else:
                    next_section = None
                    next_group_id = None

        if next_section != "Ending":
            for item in grouped_questions:
                if item["section"] == next_section:
                    scoring_system = item.get("scoring_system", [])
                    for group in item["grouped_questions"]:
                        if group["group_id"] == next_group_id:
                            next_questions = group.get("questions", [])

        set_of_documents = []
        if section != "Opening":
            set_of_documents = self.retriever.run(
                query=user_answer,
                aspect=section,
            )
        
        self.logger.info(f"Questions for section '{next_section}' and group '{next_group_id}': {next_questions}")

        content_payload = {
            "type": conversation_type,
            "next_section": next_section,
            "user_answer": user_answer,
            "next_group_id": next_group_id,
            "next_questions": next_questions,
            "scoring_system": scoring_system,
            "set_of_documents": json.dumps(set_of_documents),
        }
        
        raw_response = self.fine_tuned_model_client.run_prompt(
            system_prompt=system_prompt,
            user_prompt=json.dumps(content_payload),
            temperature=0.6
        )

        try:
            response = {
                "model": json.loads(raw_response.strip()),
                "next_group_id": next_group_id,
                "next_section": next_section
            }

            return response
        except json.JSONDecodeError:
            return {
                "error": "[Chatbot Engine]: Model returned invalid JSON format"
            }
