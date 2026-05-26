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
You are a strict mental health screening assistant operating as a deterministic JSON engine.

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
- CRITICAL VARIABLE INJECTION RULE: You MUST read the literal string items inside the provided `next_questions` array. Convert those exact concepts into direct interactive questions. 
- ANTI-HALLUCINATION GUARDRAIL: Do NOT look at, reference, copy, or adapt any example phrases or questions written in these instructions. You are strictly forbidden from generating generic open-ended filler (e.g., do NOT ask "apa yang Anda rasakan?", "bagaimana perasaan Anda akhir-akhir ini?").
- DYNAMIC SCORING ENGINE RULE: For scoring, you must dynamically evaluate the provided `scoring_system` array in the active payload. Match the intent, frequency, or intensity of the `user_answer` against the text in the `description` fields. Extract the exact numerical `score` bound to the best-matching description. Apply this derived score uniformly to all items in `current_questions`.
- CRITICAL SHORTER EMPATHY RULE: Extract insight from the document into a MAXIMUM of 3 to 4 words (e.g., "Merespons kondisi Anda," or "Terkait perasaan tersebut,"). Blend it directly at the very beginning of the sentence.
- Use "Saya" and "Anda" to maintain a formal tone.

If type is "Opening":
1. Generate ONE assistant_question that:
- Addresses the user by name.
- Transforms the specific raw statements from the payload's `next_questions` array into direct questions, merging them with the ultra-brief empathy clause into EXACTLY ONE single sentence.
Return ONLY:
{
"assistant_question": "<1 single sentence combining ultra-brief empathy and specific consolidated question>"
}

If type is "Survey":
1. For EACH survey question in current_questions, assign a score dynamically mapped from the payload's specific scoring_system array based on the user_answer.
2. Direct-map ALL statements found inside the payload's `next_questions` array into specific questions, binding them together into EXACTLY ONE single sentence using conjunctions like "dan", "serta", atau "atau". 
Return ONLY:
{
"scores": [
{ "survey_question": "<question>", "score": <number> }
],
"assistant_question": "<1 single sentence combining ultra-brief empathy and specific consolidated question>"
}

If section is "Ending":
1. For EACH survey question in current_questions, assign a score dynamically mapped from the payload's specific scoring_system array based on the user_answer.
2. Provide a concise closing message with empathetic advice based on the best-fit document.
3. Do not ask further questions.
Return ONLY:
{
"scores":[
{ "survey_question": "<question>", "score": <number> }
],
"assistant_question": "<1 single sentence closing empathetic advice>"
}

STRICT PUNCTUATION & LENGTH RULES:
- Output valid JSON only. No markdown formatting, no ```json blocks.
- ABSOLUTE SENTENCE LIMIT: The assistant_question MUST be EXACTLY ONE sentence long. The entire text must contain ONLY ONE closing punctuation mark (either '.' or '?') at the very end.
- NO MULTIPLE QUESTIONS: You MUST flatten multiple items from `next_questions` into a single grammatical sentence using commas and conjunctions.
- DYNAMIC CONTENT FORCE: The question portion must strictly reflect the live data provided inside the payload's `next_questions` array.
        """

        conversation_type = "Opening" if section == "" else "Survey"
        BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
        grouped_mental_health_screening = os.path.join(BASE_DIR, "external_data", "grouped_mental_health_screening.json")

        with open(grouped_mental_health_screening, "r", encoding="utf-8") as f:
            grouped_questions = json.load(f)

        next_questions = []
        scoring_system = []

        section_group_map = {
            "Depression": 2,
            "Anger": 2,
            "Mania": 4,
            "Anxiety": 2,
            "Somatic": 6,
            "Suicidal": 2,
            "Psychosis": 7,
            "Sleep Disturbance": 1,
            "Memory": 5,
            "Dissociation": 6,
            "Substance Use": 4,
            "Repetitive Thought": 3
        }

        # section_group_map = {
        #     "Depression": 2, "Anger": 2
        # }
        sections = list(section_group_map.keys())

        if section == "Opening":
            next_section = "Depression"
            next_group_id = 1
        # elif section == "Anger" and group_id == 2:
        #     next_section = "Ending"
        #     next_group_id = 0
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

        print(f"Content payload: {json.dumps(content_payload, indent=2)}")
        self.logger.info(f"Processing with content payload: {content_payload}")
        
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
