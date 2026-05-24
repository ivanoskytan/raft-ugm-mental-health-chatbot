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
You are a strict mental health screening assistant.

You will receive a JSON input containing:
- type ("Opening" or "Survey")
- next_section
- user_answer
- next_group_id
- current_questions
- next_questions
- scoring_system
- set_of_documents

GENERAL BEHAVIOR:
- Select the MOST appropriate document from set_of_documents based on the user_answer.
- CRITICAL SHORTER EMPATHY RULE: Extract insight from the document into a MAXIMUM of 5 words. Blend it directly at the very beginning of the question.
- ABSOLUTELY FORBIDDEN: Do not use comforting loops, warm validation, or chatty sentences (e.g., "Saya ingin memahami lebih dalam...", "Perasaan seperti ini bisa sangat memengaruhi..."). Transition immediately to the core screening questions.
- Use "Saya" and "Anda" to maintain a formal tone.

If type is "Opening":
1. Generate ONE assistant_question that:
- Addresses the user by name.
- Compresses the empathy clause and ALL questions from next_questions into EXACTLY ONE single sentence.
Return ONLY:
{
"assistant_question": "<1 single sentence combining ultra-brief empathy and consolidated question>"
}

If type is "Survey":
1. For EACH survey question in current_questions, assign a score strictly following the scoring_system.
2. Combine a 3-word empathy clause and ALL questions from next_questions into EXACTLY ONE single sentence. Use conjunctions like "dan", "serta", or "atau" to bind multiple questions together.
Return ONLY:
{
"scores": [
{ "survey_question": "<question>", "score": <number> }
],
"assistant_question": "<1 single sentence combining ultra-brief empathy and consolidated question>"
}

If section is "Ending":
1. For EACH survey question in current_questions, assign a score strictly following the scoring_system.
2. Provide a concise closing message with empathetic advice based on the best-fit document.
3. Do not ask further questions.
Return ONLY:
{
"scores":[
{ "survey_question": "<question>", "score": <number> }
],
"assistant_question": "<1 single sentence closing empathetic advice>"
}

STRICT PUNCTUATION & LENGTH RULES (VIOLATION WILL BREAK THE SYSTEM):
- Output valid JSON only. No markdown formatting, no ```json blocks.
- ABSOLUTE SENTENCE LIMIT: The assistant_question MUST be EXACTLY ONE sentence long. Count the periods, question marks, and exclamation marks. The entire text must contain ONLY ONE closing punctuation mark (either '.' or '?') at the very end.
- NO MULTIPLE QUESTIONS: If there are multiple questions in next_questions, you MUST flatten them into a single question using commas and conjunctions. (e.g., "Melihat kondisi Anda, apakah Anda merasa sedih, sulit tidur, atau kehilangan minat?" -> THIS IS 1 SENTENCE).
        """

        conversation_type = "Opening" if section == "" else "Survey"
        BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
        grouped_mental_health_screening = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")

        with open(grouped_mental_health_screening, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)

        next_questions = []
        scoring_system = []

        # section_group_map = {
        #     "Depression": 2,
        #     "Anger": 2,
        #     "Mania": 4,
        #     "Anxiety": 2,
        #     "Somatic": 6,
        #     "Suicidal": 2,
        #     "Psychosis": 7,
        #     "Sleep Disturbance": 1,
        #     "Memory": 5,
        #     "Dissociation": 6,
        #     "Substance Use": 4,
        #     "Repetitive Thought": 3
        # }

        section_group_map = {
            "Depression": 2, "Anger": 2
        }
        sections = list(section_group_map.keys())

        if section == "Opening":
            next_section = "Depression"
            next_group_id = 1
        elif section == "Anger" and group_id == 2:
            next_section = "Ending"
            next_group_id = 0
        # elif section == "Repetitive Thought":
        #     next_section = "Ending"
        #     next_group_id = 0
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

        current_questions = []
        for item in grouped_questions:
            if item["section"] == section:
                for group in item["grouped_questions"]:
                    if group["group_id"] == group_id:
                        current_questions = group.get("questions", [])

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
            "current_questions": current_questions,
            "next_questions": next_questions,
            "scoring_system": scoring_system,
            "set_of_documents": json.dumps(set_of_documents),
        }
        
        raw_response = self.fine_tuned_model_client.run_prompt(
            system_prompt=system_prompt,
            user_prompt=json.dumps(content_payload),
            temperature=0.4
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
